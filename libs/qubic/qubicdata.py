import ctypes
import os
import sys
from enum import Enum

from algorithms.verify import get_public_key_from_id

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))


NUMBER_OF_EXCHANGED_PEERS = 4
NUMBER_OF_COMPUTORS = 676
NUMBER_OF_SOLUTION_NONCES = 1000
QUORUM = int((NUMBER_OF_COMPUTORS * 2 / 3) + 1)
SIGNATURE_SIZE = 64
KEY_SIZE = 32


c_ip_type = (ctypes.c_uint8 * 4)
c_nonce_type = (ctypes.c_uint8 * 32)
c_nonce_type_array = c_nonce_type * NUMBER_OF_SOLUTION_NONCES
c_signature_type = (ctypes.c_uint8 * SIGNATURE_SIZE)
c_public_key_type = (ctypes.c_uint8 * KEY_SIZE)
c_public_keys_type = c_public_key_type * NUMBER_OF_COMPUTORS
c_revenues_type = ctypes.c_uint32 * NUMBER_OF_COMPUTORS

ADMIN_ID = "EEDMBLDKFLBNKDPFHDHOOOFLHBDCHNCJMODFMLCLGAPMLDCOAMDDCEKMBBBKHEGGLIAFFK"
ADMIN_PUBLIC_KEY = get_public_key_from_id(ADMIN_ID)
EMPTY_PUBLIC_KEY = bytes(KEY_SIZE)
ISSUANCE_RATE = 1000000000000

MAX_REVENUE_VALUE = int(ISSUANCE_RATE / NUMBER_OF_COMPUTORS)


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
    BROADCAST_REVENUES = 'qubic.data.broadcast_revenues'


class DataSubjects:
    TICKS = 'qubic.data.ticks'
    SCORES = 'qubic.data.scores'
    REVENUES = 'qubic.data.revenues'


"""Network packages
"""
EXCHANGE_PUBLIC_PEERS = 0
BROADCAST_RESOURCE_TESTING_SOLUTION = 1
BROADCAST_COMPUTORS = 2
BROADCAST_TICK = 3
BROADCAST_REVENUES = 4
REQUEST_COMPUTORS = 11


class RequestResponseHeader(ctypes.Structure):
    _fields_ = [("size", ctypes.c_uint32),
                ("protocol", ctypes.c_ushort),
                ("type", ctypes.c_ushort)]

    def __repr__(self) -> str:
        return str(f"Size: {self.size}\nProtocol: {self.protocol}\nType: {self.type}")


class ExchangePublicPeers(ctypes.Structure):
    _fields_ = [("peers", c_ip_type * NUMBER_OF_EXCHANGED_PEERS)]


class ResourceTestingSolution(ctypes.Structure):
    _fields_ = [('computorPublicKey', c_public_key_type),
                ('nonces', c_nonce_type_array)]


class BroadcastResourceTestingSolution(ctypes.Structure):
    _fields_ = [('resourceTestingSolution', ResourceTestingSolution)]


class Computors(ctypes.Structure):
    _fields_ = [("epoch", ctypes.c_ushort),
                ("public_keys", c_public_keys_type),
                ("signature", c_signature_type)]


class BroadcastComputors(ctypes.Structure):
    _fields_ = [('computors', Computors)]


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

                ('initSpectrumDigest', ctypes.c_uint8 * 32),
                ('initComputerDigest', ctypes.c_uint8 * 32),
                ('initUniverseDigest', ctypes.c_uint8 * 32),
                ('prevSpectrumDigest', ctypes.c_uint8 * 32),
                ('prevComputerDigest', ctypes.c_uint8 * 32),
                ('prevUniverseDigest', ctypes.c_uint8 * 32),
                ('saltedSpectrumDigest', ctypes.c_uint8 * 32),
                ('saltedComputerDigest', ctypes.c_uint8 * 32),
                ('saltedUniverseDigest', ctypes.c_uint8 * 32),

                ('nextTickChosenTransfersEffectsAndQuestionsDigest', ctypes.c_uint8 * 32),

                ('signature', c_signature_type)]


class Revenues(ctypes.Structure):
    _fields_ = [('computorIndex', ctypes.c_ushort),
                ('epoch', ctypes.c_ushort),
                ('revenues', c_revenues_type),
                ('signature', c_signature_type)]


class BroadcastRevenues(ctypes.Structure):
    _fields_ = [('revenues', Revenues)]


class System(ctypes.Structure):
    _fields_ = [('version', ctypes.c_short),
                ('epoch', ctypes.c_ushort),
                ('tick', ctypes.c_uint32),
                ('tickCounters', ctypes.c_uint32 * NUMBER_OF_COMPUTORS)]


class BroadcastedComputors(ctypes.Structure):
    _pack_: int = 1
    _fields_ = [('header', RequestResponseHeader),
                ('broadcastComputors', BroadcastComputors)]

    @property
    def epoch(self):
        return self.broadcastComputors.computors.epoch


__protocol_version = int(os.getenv('QUBIC_NETWORK_PROTOCOL_VERSION', 0))
computors_system_data = Computors()
REQUEST_COMPUTORS_HEADER = RequestResponseHeader(size=ctypes.sizeof(
    RequestResponseHeader), protocol=__protocol_version, type=REQUEST_COMPUTORS)


def __get_random_public_keys() -> bytes:
    import secrets
    return secrets.token_bytes(ctypes.sizeof(c_public_keys_type))


broadcasted_computors = BroadcastedComputors(header=RequestResponseHeader(size=ctypes.sizeof(
    RequestResponseHeader) + ctypes.sizeof(BroadcastComputors), protocol=__protocol_version, type=BROADCAST_COMPUTORS),
    broadcastComputors=BroadcastComputors(computors=Computors(epoch=0,
                                                              public_keys=c_public_keys_type.from_buffer_copy(
                                                                  __get_random_public_keys()),
                                                              signature=c_signature_type.from_buffer_copy(bytes(ctypes.sizeof(c_signature_type))))))
