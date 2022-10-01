import asyncio
import ctypes
import logging
from ctypes import sizeof
from os import getenv
from random import shuffle
from typing import Any, Optional

from qubic.qubicdata import (BROADCAST_COMPUTORS,
                             BROADCAST_RESOURCE_TESTING_SOLUTION,
                             BROADCAST_TICK, EXCHANGE_PUBLIC_PEERS,
                             REQUEST_COMPUTORS, BroadcastComputors,
                             BroadcastResourceTestingSolution, Computors,
                             ConnectionState, ExchangePublicPeers,
                             RequestResponseHeader, Tick,
                             broadcasted_computors)
from qubic.qubicutils import (can_apply_computors_data,
                              exchange_public_peers_to_list,
                              get_header_from_bytes, get_protocol_version,
                              get_raw_payload, is_valid_computors_data,
                              is_valid_header, is_valid_ip, apply_computors)
from utils.backgroundtasks import BackgroundTasks
from utils.callback import Callbacks


class QubicNetworkManager():
    def __init__(self, public_ip_list: list) -> None:
        self._know_ip = set(public_ip_list)
        self._fogeted_ip = set()
        self._peers = set()
        self._backgound_tasks = BackgroundTasks()
        self.__connection_state: ConnectionState = ConnectionState.NONE
        self.__callbacks = Callbacks()

    def add_ip(self, ip_set: set):
        for ip in ip_set:
            if is_valid_ip(ip):
                self._know_ip.add(ip)

    @property
    def know_ip(self):
        return self._know_ip

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

    def add_callback(self, callback):
        self.__callbacks.add_callback(callback=callback)

    def __data_from_peer(self, header_type: int, data: Any):
        """
        Send data from peers to listeners
        """
        self.__callbacks.execute(header_type=header_type, data=data)

    def __connect_to_peer(self, ip: str):
        if is_valid_ip(ip):
            peer = Peer(self)
            self._peers.add(peer)
            peer.add_callback(self.__data_from_peer)

            self._backgound_tasks.create_task(
                peer.connect, ip, self.port, self.connection_timeout)

    def is_free_ip(self, ip) -> bool:
        """Check that there are no connections to this ip
        """
        for peer in self._peers:
            if ip == peer.ip:
                return False
        return True

    async def main_loop(self):
        NUBMER_OF_CONNECTION = 10
        while self.__connection_state == ConnectionState.CONNECTED:
            number_of_available_slots = NUBMER_OF_CONNECTION - len(self._peers)
            if len(self._peers) != NUBMER_OF_CONNECTION:

                # If there are few known peers left, try reconnecting to forgotten ones
                if len(self._know_ip) <= 2 and len(self._fogeted_ip) > 0:
                    self._know_ip = self._know_ip.union(self._fogeted_ip)
                    self._fogeted_ip.clear()

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
                [peer for peer in self._peers if peer.state == ConnectionState.CONNECTED])

            print(f"Connected: {num_of_connected}")
            await asyncio.sleep(1)

    async def start(self):
        self.__connection_state = ConnectionState.CONNECTING
        for peer_ip in self._know_ip:
            self.__connect_to_peer(peer_ip)

        self.__connection_state = ConnectionState.CONNECTED
        await self._backgound_tasks.create_and_wait(self.main_loop)

    async def stop(self):
        self.__connection_state = ConnectionState.CLOSED
        tasks = []
        for peer in self._peers:
            tasks.append(peer.stop())

        await asyncio.gather(*tasks)

    async def send_other(self, raw_data: bytes, peer_requestor):
        tasks = []
        try:
            for peer in self._peers:
                if peer != peer_requestor:
                    tasks.append(peer.send_data(raw_data))

            await asyncio.gather(*tasks)
        except Exception as e:

            logging.exception(e)
            pass

    def foget_peer(self, peer):
        if peer in self._peers:
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
        self.__state: ConnectionState = ConnectionState.NONE
        self.__callbacks = Callbacks()
        self.__backgound_tasks = BackgroundTasks()

    @property
    def ip(self):
        return self.__ip

    @property
    def state(self):
        return self.__state

    @property
    def read_timeout(self):
        return 10

    async def connect(self, ip: str, port: int, timeout: int):
        self.__ip = ip

        print(f"Connect to {ip}")

        self.__state = ConnectionState.CONNECTING

        self.__connect_task = asyncio.create_task(
            asyncio.open_connection(ip, port))

        try:
            reader, writer = await asyncio.wait_for(self.__connect_task, timeout)
        except Exception as e:
            await self._disconection(e)
            return

        self.__state = ConnectionState.CONNECTED
        self.__reader = reader
        self.__writer = writer

        try:
            await self.handshake()
        except Exception as e:
            await self._disconection(e)
            return

        task = self.__backgound_tasks.create_task(self.__read_loop)
        done, pending = await asyncio.wait([task])
        result_task: asyncio.Task = None
        for result_task in done:
            try:
                e = result_task.exception()
            except asyncio.CancelledError:
                e = None
                pass

            if e is not None:
                logging.exception(e)

    def add_callback(self, callback):
        self.__callbacks.add_callback(callback=callback)

    async def handshake(self):
        """When connecting to a peer we exchange public peers. 
        """
        import random

        from qubic.qubicdata import NUMBER_OF_EXCHANGED_PEERS
        from qubic.qubicutils import ip_to_ctypes
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

            know_ip = self.__qubic_manager.know_ip
            random_ip_list = random.sample(know_ip, min(
                len(know_ip), NUMBER_OF_EXCHANGED_PEERS))
            for i in range(0, NUMBER_OF_EXCHANGED_PEERS):
                exchange_public_peers.peers[i] = ip_to_ctypes(
                    random_ip_list[i])

            try:
                await self.send_data(bytes(header) + bytes(exchange_public_peers))
            except Exception as e:
                await self._disconection(e)
                return

    async def _disconection(self, what: Optional[str] = None):
        if what is not None:
            logging.warning(what)

        self.__qubic_manager.foget_peer(self)
        await self.stop()

    async def __read_data(self, size) -> bytes:
        task = self.__backgound_tasks.create_task(
            self.__reader.readexactly, size)

        raw_data = await asyncio.wait_for(task, self.read_timeout)

        if len(raw_data) != size:
            raise ConnectionError(f"Unable to read the data ({len(raw_data)}")

        return raw_data

    async def send_data(self, raw_data: bytes):
        if self.__state != ConnectionState.CONNECTED:
            return

        if len(raw_data) <= 0:
            await self._disconection("Data cannot be empty")
            return

        if self.__writer.is_closing():
            await self._disconection("Writer closed")
            return

        try:
            self.__writer.write(raw_data)
            await self.__writer.drain()
        except Exception as e:
            await self._disconection(e)
            return
        # await self.__writer.drain()

    async def __read_loop(self):
        while self.__state == ConnectionState.CONNECTED:
            try:
                raw_data = await self.__read_message()
                header = get_header_from_bytes(raw_data)
                header_type = header.type
                raw_payload = get_raw_payload(raw_data)

            except Exception as e:
                logging.exception(e)
                await self._disconection(e)
                return

            if header_type == EXCHANGE_PUBLIC_PEERS:
                exchange_public_peers = ExchangePublicPeers.from_buffer_copy(
                    raw_payload)
                self.__qubic_manager.add_ip(
                    set(exchange_public_peers_to_list(exchange_public_peers)))
                self.__callbacks.execute(
                    header_type=EXCHANGE_PUBLIC_PEERS, data=exchange_public_peers)

            if header_type == BROADCAST_COMPUTORS:
                try:
                    broadcast_computors = BroadcastComputors.from_buffer_copy(
                        raw_payload)
                except Exception as e:
                    logging.exception(e)
                    await self._disconection()
                    return

                computors: Computors = broadcast_computors.computors
                if can_apply_computors_data(computors=computors):
                    if is_valid_computors_data(computors):
                        apply_computors(computors=computors)

                        self.__callbacks.execute(
                            header_type=BROADCAST_COMPUTORS, data=broadcast_computors)
            elif header_type == BROADCAST_RESOURCE_TESTING_SOLUTION:
                self.__callbacks.execute(
                    header_type=header_type, data=BroadcastResourceTestingSolution.from_buffer_copy(raw_payload))
            elif header_type == BROADCAST_TICK:
                tick = Tick.from_buffer_copy(raw_payload)
                if tick.hour <= 23 and tick.minute <= 59 and tick.second <= 59 and tick.millisecond <= 999:
                    # TODO: add verify check
                    self.__callbacks.execute(
                        header_type=header_type, data=tick)
            elif header_type == REQUEST_COMPUTORS:
                logging.info('REQUEST_COMPUTORS')
                if broadcasted_computors.epoch >= 0:
                    logging.info('Send broadcasted_computors')
                    self.__backgound_tasks.create_task(
                        self.send_data, bytes(broadcasted_computors))
                # Do not send this request to other piers
                continue

            self.__backgound_tasks.create_task(
                self.__qubic_manager.send_other, raw_data, self)

    async def __read_message(self):
        if self.__state != ConnectionState.CONNECTED:
            raise ConnectionRefusedError()

        # Reading Header
        try:
            task = self.__backgound_tasks.create_task(
                self.__read_data, sizeof(RequestResponseHeader))
            raw_header = await asyncio.wait_for(task, self.read_timeout)
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
            # try:
            #     await asyncio.gather(task, return_exceptions=True)
            # except asyncio.CancelledError:
            #     pass

    async def stop(self):
        logging.info("Stop Peer")
        self.__state = ConnectionState.CLOSED

        logging.info("Cancel connect")
        if self.__connect_task != None:
            await self.cancel_task(self.__connect_task)

        logging.info("Close write")
        if self.__writer != None and not self.__writer.is_closing():
            self.__writer.close()
            try:
                await self.__writer.wait_closed()
            except ConnectionResetError:
                pass

        await self.__backgound_tasks.close()
