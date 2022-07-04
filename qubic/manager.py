import asyncio
import ctypes
import logging
from ctypes import sizeof
from os import getenv
from random import shuffle
from typing import Optional

from dotenv import load_dotenv

from qubicdata import (BROADCAST_COMPUTORS, EXCHANGE_PUBLIC_PEERS, Computors,
                       ExchangePublicPeers, PeerState, RequestResponseHeader)
from qubicutils import (exchange_public_peers_to_list, get_header_from_bytes,
                        get_protocol_version, get_raw_payload,
                        is_valid_broadcast_computors, is_valid_header,
                        is_valid_ip, apply_computors_data)


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
            task = asyncio.create_task(peer.connect(
                ip, self.port, self.connection_timeout))
            task.add_done_callback(self._backgound_tasks.remove)
            self._backgound_tasks.append(task)

    def is_free_ip(self, ip) -> bool:
        """Check that there are no connections to this ip
        """
        for peer in self._peers:
            if ip == peer.ip:
                return False
        return True

    async def main_loop(self):
        NUBMER_OF_CONNECTION = 10
        while True:
            number_of_available_slots = NUBMER_OF_CONNECTION - len(self._peers)
            if len(self._peers) != NUBMER_OF_CONNECTION:

                # If there are few known peers left, try reconnecting to forgotten ones
                if len(self._know_ip) <= 1 and len(self._fogeted_ip) > 0:
                    self._know_ip.union(self._fogeted_ip)

                if len(self._know_ip) > 0:
                    list_ip = list(self._know_ip)
                    shuffle(list_ip)
                    for ip in list_ip:
                        if self.is_free_ip(ip) and is_valid_ip(ip):
                            self.__connect_to_peer(ip)
                            number_of_available_slots = number_of_available_slots - 1
                            if number_of_available_slots == 0:
                                break

            num_of_connected = len(
                [peer for peer in self._peers if peer.state == PeerState.CONNECTED])

            print(f"Connected: {num_of_connected}")
            await asyncio.sleep(1)

    async def start(self):
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
        self._fogeted_ip.add(peer.ip)


class Peer():
    def __init__(self, qubic_network: QubicNetworkManager) -> None:
        self.__qubic_manager = qubic_network
        self.__connect_task: Optional[asyncio.Task] = None
        self.__reader: Optional[asyncio.StreamReader] = None
        self.__writer: Optional[asyncio.StreamWriter] = None
        self.__ip = ""
        self.__state: PeerState = PeerState.NONE
        self.__background_tasks = []

    @property
    def ip(self):
        return self.__ip

    @property
    def state(self):
        return self.__state

    async def connect(self, ip: str, port: int, timeout: int):
        self.__ip = ip

        print(f"Connect to {ip}")

        self.__state = PeerState.CONNECTING

        self.__connect_task = asyncio.create_task(
            asyncio.open_connection(ip, port))

        try:
            reader, writer = await asyncio.wait_for(self.__connect_task, timeout)
        except Exception as e:
            await self.__disconection(e)
            return

        self.__state = PeerState.CONNECTED
        self.__reader = reader
        self.__writer = writer

        try:
            await self.handshake()
        except Exception as e:
            self.__disconection(e)
            return

        task = asyncio.create_task(self.__read_loop())
        task.add_done_callback(self.__background_tasks.remove)
        self.__background_tasks.append(task)
        await asyncio.gather(task)

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

            await self.send_data(bytes(header) + bytes(exchange_public_peers))

    async def __disconection(self, what):
        logging.warning(what)

        self.__qubic_manager.foget_peer(self)
        await self.stop()

    async def __read_data(self, size) -> bytes:
        raw_data = await self.__reader.read(size)
        if len(raw_data) != size:
            raise ConnectionError(f"Unable to read the data ({len(raw_data)}")

        return raw_data

    async def send_data(self, raw_data: bytes):
        if self.__state != PeerState.CONNECTED:
            return

        if len(raw_data) <= 0:
            raise ValueError("Data cannot be empty")

        if self.__writer.is_closing():
            raise ValueError("Writer closed")

        self.__writer.write(raw_data)
        # await self.__writer.drain()

    async def __read_loop(self):
        while True:
            try:
                raw_data = await self.__read_message()
                header = get_header_from_bytes(raw_data)
                header_type = header.type
                raw_payload = get_raw_payload(raw_data)

            except Exception as e:
                await self.__disconection(e)
                return

            if header_type == EXCHANGE_PUBLIC_PEERS:
                exchange_public_peers = ExchangePublicPeers.from_buffer_copy(
                    raw_payload)
                self.__qubic_manager.add_ip(
                    set(exchange_public_peers_to_list(exchange_public_peers)))

            if header_type == BROADCAST_COMPUTORS:
                print("BROADCAST_COMPUTORS")
                computors = Computors.from_buffer_copy(raw_payload)
                if is_valid_broadcast_computors(computors):
                    await apply_computors_data(computors)

            await self.__qubic_manager.send_other(raw_data, self)

    async def __read_message(self):
        if self.__state != PeerState.CONNECTED:
            raise ConnectionRefusedError()
            

        # Reading Header
        try:
            raw_header = await self.__read_data(sizeof(RequestResponseHeader))
        except Exception as e:
            raise e
        header = RequestResponseHeader.from_buffer_copy(raw_header)

        # Checking package validity
        if not is_valid_header(header):
            raise ValueError("Invalid header")

        # Reading payload
        try:
            raw_payload = await self.__read_data(header.size - sizeof(header))
        except Exception as e:
            raise e

        return raw_header + raw_payload

    def foget_peer(self):
        """We forget about this peer so we don't connect to it again.
        """
        self.__qubic_manager.foget_peer(self)

    async def cancel_task(self, task: asyncio.Task):
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


        for task in self.__background_tasks:
            task.cancel()

        # try:
        #     await asyncio.gather(*self.__background_tasks, return_exceptions=True)
        # except asyncio.CancelledError:
        #     pass


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
