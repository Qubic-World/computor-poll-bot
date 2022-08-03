import ctypes
import os
import sys
from enum import Enum

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from algorithms.verify import get_public_key_from_id

NUMBER_OF_EXCHANGED_PEERS = 4
NUMBER_OF_COMPUTORS = 26 * 26
QUORUM = int((NUMBER_OF_COMPUTORS * 2 / 3) + 1)
SIGNATURE_SIZE = 64
KEY_SIZE = 32


c_ip_type = (ctypes.c_uint8 * 4)

ADMIN_ID = "EEDMBLDKFLBNKDPFHDHOOOFLHBDCHNCJMODFMLCLGAPMLDCOAMDDCEKMBBBKHEGGLIAFFK"
ADMIN_PUBLIC_KEY = get_public_key_from_id(ADMIN_ID)
EMPTY_PUBLIC_KEY = bytes(KEY_SIZE)


class ConnectionState(Enum):
    NONE = 0
    CONNECTING = 1
    CONNECTED = 2
    CLOSED = 3


"""Network packages
"""
EXCHANGE_PUBLIC_PEERS = 0
BROADCAST_COMPUTORS = 2


class RequestResponseHeader(ctypes.Structure):
    _fields_ = [("size", ctypes.c_uint32),
                ("protocol", ctypes.c_ushort),
                ("type", ctypes.c_ushort)]

    def __repr__(self) -> str:
        return str(f"Size: {self.size}\nProtocol: {self.protocol}\nType: {self.type}")


class ExchangePublicPeers(ctypes.Structure):
    _fields_ = [("peers", c_ip_type * NUMBER_OF_EXCHANGED_PEERS)]


class Computors(ctypes.Structure):
    _fields_ = [("index", ctypes.c_uint32),
                ("epoch", ctypes.c_int16),
                ("protocol", ctypes.c_ushort),
                ("scores", ctypes.c_ulonglong *
                 (NUMBER_OF_COMPUTORS + (NUMBER_OF_COMPUTORS - QUORUM))),
                ("public_keys", ctypes.c_uint8 *
                 ((NUMBER_OF_COMPUTORS + (NUMBER_OF_COMPUTORS - QUORUM)) * KEY_SIZE)),
                ("signature", ctypes.c_uint8 * SIGNATURE_SIZE)]


computors_system_data = Computors()