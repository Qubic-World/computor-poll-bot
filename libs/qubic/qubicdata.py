import ctypes
import os
import sys
from enum import Enum

from algorithms.verify import get_public_key_from_id

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))


NUMBER_OF_EXCHANGED_PEERS = 4
NUMBER_OF_COMPUTORS = 26 * 26
QUORUM = int((NUMBER_OF_COMPUTORS * 2 / 3) + 1)
SIGNATURE_SIZE = 64
KEY_SIZE = 32


c_ip_type = (ctypes.c_uint8 * 4)
c_nonce_type = (ctypes.c_uint8 * 32)
c_signature_type = (ctypes.c_uint8 * SIGNATURE_SIZE)

ADMIN_ID = "EEDMBLDKFLBNKDPFHDHOOOFLHBDCHNCJMODFMLCLGAPMLDCOAMDDCEKMBBBKHEGGLIAFFK"
ADMIN_PUBLIC_KEY = get_public_key_from_id(ADMIN_ID)
EMPTY_PUBLIC_KEY = bytes(KEY_SIZE)
NUMBER_OF_SOLUTION_NONCES = 1000


class ConnectionState(Enum):
    NONE = 0
    CONNECTING = 1
    CONNECTED = 2
    CLOSED = 3


class Subjects:
    BROADCAST_COMPUTORS = 'qubic.data.broadcast_computors'
    EXCHANGE_PUBLIC_PEERS = 'qubic.data.exchange_public_peers'
    BROADCAST_TICK = 'qubic.data.broadcast_tick'
    BROADCAST_RESOURCE_TESTING_SOLUTION = 'qubic.data.broadcast_resource_testing_solution'


"""Network packages
"""
EXCHANGE_PUBLIC_PEERS = 0
BROADCAST_RESOURCE_TESTING_SOLUTION = 1
BROADCAST_COMPUTORS = 2
BROADCAST_TICK = 3


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
                ("signature", c_signature_type)]


class ResourceTestingSolution(ctypes.Structure):
    _fields_ = [('computorPublicKey', ctypes.c_uint8),
                ('nonces', c_nonce_type * NUMBER_OF_SOLUTION_NONCES)]


class BroadcastResourceTestingSolution(ctypes.Structure):
    _fields_ = ['resourceTestingSolution', ResourceTestingSolution]


class Tick(ctypes.Structure):
    _fields_ = [('computorIndex', ctypes.c_ushort),

                ('epoch', ctypes.c_ushort),
                ('tick', ctypes.c_uint32),

                ('millisecond', ctypes.c_ushort),
                ('second', ctypes.c_uint8),
                ('minute', ctypes.c_uint8),
                ('hour', ctypes.c_uint8),
                ('day', ctypes.c_uint8),
                ('month', ctypes.c_uint8),
                ('year', ctypes.c_uint8),

                ('saltedStateDigest', ctypes.c_uint8 * 32),
                ('prevStateDigest', ctypes.c_uint8 * 32),
                ('nextTickChosenTransfersEffectsAndQuestionsDigest', ctypes.c_uint8 * 32),

                ('signature', c_signature_type)]


computors_system_data = Computors()
