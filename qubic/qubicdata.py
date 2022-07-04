import ctypes
from enum import Enum

NUMBER_OF_EXCHANGED_PEERS = 4


class RequestResponseHeader(ctypes.Structure):
    _fields_ = [("size", ctypes.c_uint32),
                ("protocol", ctypes.c_ushort),
                ("type", ctypes.c_ushort)]

    def __repr__(self) -> str:
        return str(f"Size: {self.size}\nProtocol: {self.protocol}\nType: {self.type}")


EXCHANGE_PUBLIC_PEERS = 0
c_ip_type = (ctypes.c_uint8 * 4)


class ExchangePublicPeers(ctypes.Structure):
    _fields_ = [("peers", c_ip_type * NUMBER_OF_EXCHANGED_PEERS)]


class PeerState(Enum):
    NONE = 0
    CONNECTING = 1
    CONNECTED = 2
    CLOSED = 3
