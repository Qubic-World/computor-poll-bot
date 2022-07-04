import asyncio
import ctypes
import logging
from ctypes import sizeof
from os import getenv
from time import sleep
from typing import Optional

from dotenv import load_dotenv
from qubicdata import PeerState

from qubicdata import (EXCHANGE_PUBLIC_PEERS, NUMBER_OF_EXCHANGED_PEERS,
                       ExchangePublicPeers, RequestResponseHeader)
from qubicutils import (exchange_public_peers_to_list, get_header_from_bytes,
                        get_protocol_version, get_raw_payload, is_valid_header,
                        is_valid_ip)


class QubicNetworkManager():
    def __init__(self, public_ip_list: list) -> None:
        self._know_ip = set(public_ip_list)
        self._fogeted_ip = set()
        self._peers = set()
        self._backgound_tasks = []

    def add_ip(self, ip_set: set):
        for ip in ip_set:
            if is_valid_ip(ip):
                self._know_ip.add(ip)

    @property
    def connection_timeout(self) -> int:
        return 15

    @property
    def port(self):
        try:
            value = getenv("QUBIC_NETWORK_PORT")
        finally:
            if value == None:
                value = -1

        return int(value)

    def __connect_to_peer(self, ip: str):
        if is_valid_ip(ip):
            peer = Peer(self)
            self._peers.add(peer)
            task = asyncio.create_task(peer.connect(ip, self.port, self.connection_timeout))
            task.add_done_callback(self._backgound_tasks.remove)
            self._backgound_tasks.append(task)


    async def main_loop(self):
        while True:
            print("Main loop")
            await asyncio.sleep(1)
            pass


    async def start(self):
        tasks = []
        for peer_ip in self._know_ip:
            self.__connect_to_peer(peer_ip)

        task = asyncio.create_task(self.main_loop())
        task.add_done_callback(self._backgound_tasks.remove)
        self._backgound_tasks.append(task)
        await asyncio.gather(task)

    async def stop(self):
        tasks = []
        for peer in self._peers:
            tasks.append(peer.stop())

        await asyncio.gather(*tasks)

        for task in self._backgound_tasks:
            task: asyncio.Task = task
            task.cancel()

        try:
            await asyncio.gather(*self._backgound_tasks, return_exceptions=True)
        except asyncio.CancelledError:
            pass

    async def send_other(self, raw_data: bytes, peer_requestor):
        tasks = []
        try:
            for peer in self._peers:
                if peer != peer_requestor:
                    tasks.append(peer.send_data(raw_data))

            await asyncio.gather(*tasks)
        except Exception as e:
            logging.warning(e)
            pass

    def foget_peer(self, peer):
        self._peers.remove(peer)
        self._know_ip.remove(peer.ip)
        self._fogeted_ip(peer.ip)


class Peer():
    def __init__(self, qubic_network: QubicNetworkManager) -> None:
        self._qubic_manager = qubic_network
        self.__connect_task: Optional[asyncio.Task] = None
        self.__reader: Optional[asyncio.StreamReader] = None
        self.__writer: Optional[asyncio.StreamWriter] = None
        self.__ip = ""
        self.__state: PeerState = PeerState.NONE

    @property
    def ip(self):
        return self.__ip

    async def connect(self, ip: str, port: int, timeout: int):
        self.__ip = ip

        self.__state = PeerState.CONNECTING

        self.__connect_task = asyncio.create_task(
            asyncio.open_connection(ip, port))

        try:
            reader, writer = await asyncio.wait_for(self.__connect_task, timeout)
        except Exception as e:
            logging.warning(e)
            self.foget_peer()
            return

        self.__state = PeerState.CONNECTED
        self.__reader = reader
        self.__writer = writer

        await self.handshake()

    async def print_hello(self):
        print("Hello")

    async def handshake(self):
        """When connecting to a peer we exchange public peers. 
        """
        print("Handshake")
        if not self.__writer.is_closing():
            # TODO: add public peers
            exchange_public_peers = ExchangePublicPeers()

            header = RequestResponseHeader()
            header.size = sizeof(RequestResponseHeader) + \
                sizeof(ExchangePublicPeers)
            header.protocol = ctypes.c_ushort(
                get_protocol_version())
            header.type = EXCHANGE_PUBLIC_PEERS

            try:
                await self.send_data(bytes(header) + bytes(exchange_public_peers))
                raw_data = await self.__read_message()
                header = get_header_from_bytes(raw_data)
                header_type = header.type
                print(header)
                raw_payload = get_raw_payload(raw_data)
            except Exception as e:
                await self.__disconection(e)
                return

            if header_type == EXCHANGE_PUBLIC_PEERS:
                exchange_public_peers = ExchangePublicPeers.from_buffer_copy(
                    raw_payload)

                self._qubic_manager.add_ip(
                    set(exchange_public_peers_to_list(exchange_public_peers)))

            await self._qubic_manager.send_other(raw_data, self)

    async def __disconection(self, what):
        logging.warning(what)
        await self.stop()

    async def __read_data(self, size) -> bytes:
        raw_data = await self.__reader.read(size)
        if len(raw_data) != size:
            raise ConnectionError("Unable to read the data")

        return raw_data

    async def send_data(self, raw_data: bytes):
        if self.__state != PeerState.CONNECTED:
            return

        print("__send_data")
        if len(raw_data) <= 0:
            raise ValueError("Data cannot be empty")

        if self.__writer.is_closing():
            raise ValueError("Writer closed")

        self.__writer.write(raw_data)
        await self.__writer.drain()

    async def __read_message(self):
        if self.__state != PeerState.CONNECTED:
            return

        print("Read data")
        # Reading Header
        try:
            raw_header = await self.__read_data(sizeof(RequestResponseHeader))
        except Exception as e:
            logging.warning(e)
            await self.__disconection(e)
            return

        header = RequestResponseHeader.from_buffer_copy(raw_header)

        # Checking package validity
        if not is_valid_header(header):
            await self.__disconection("Invalid header")
            return

        # Reading payload
        try:
            raw_payload = await self.__read_data(header.size - sizeof(header))
        except Exception as e:
            await self.__disconection(e)
            return

        return raw_header + raw_payload

    def foget_peer(self):
        """We forget about this peer so we don't connect to it again.
        """
        self._qubic_manager.foget_peer(self)

    async def cancel_task(self,task: asyncio.Task):
        if not task.cancelled():
            task.cancel()
            try:
                await asyncio.gather(task, return_exceptions=True)
            except asyncio.CancelledError:
                pass

    async def stop(self):
        self.__state = PeerState.CLOSED

        if self.__connect_task != None:
            await self.cancel_task(self.__connect_task)

        if self.__writer != None and not self.__writer.is_closing():
            self.__writer.close()
            await self.__writer.wait_closed()


if __name__ == "__main__":

    load_dotenv()

    network = QubicNetworkManager(["213.127.147.70",
                                   "83.57.175.137",
                                   "178.172.194.130",
                                   "82.114.88.225",
                                   "82.223.197.126",
                                   "82.223.165.100",
                                   "85.215.98.91",
                                   "212.227.149.43"])

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(network.start())
    except KeyboardInterrupt:
        pass
    finally:
        print("Before stop")
        # loop.run_until_complete(network.stop())
        loop.run_until_complete(network.stop())
        loop.close()
        print("After stop")
