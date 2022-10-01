import os
import sys
from ctypes import sizeof
from os import getenv

import aiofiles
from algorithms.verify import get_identity, kangaroo_twelve, verify

from qubic.qubicdata import (ADMIN_PUBLIC_KEY, EMPTY_PUBLIC_KEY,
                             SIGNATURE_SIZE, Computors, ExchangePublicPeers,
                             RequestResponseHeader, c_ip_type,
                             computors_system_data, broadcasted_computors)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))


COMPUTORS_CACHE_PATH = os.path.join(
    os.getenv('DATA_FILES_PATH', './'), 'system.data')

""" IP
"""


def is_valid_ip(ip: str):
    octets = ip.split(".")
    if len(octets) != 4:
        return False

    for octet in octets:
        if not octet.isdigit() or len(octet) > 3:
            return False

        int_octet = int(octet)
        if int_octet > 255:
            return False

    return True


def ip_to_ctypes(ip: str) -> c_ip_type:
    ctypes_ip = c_ip_type()

    if is_valid_ip(ip):
        octets = ip.split(".")
        idx = 0
        for octet in octets:
            ctypes_ip[idx] = int(octet)
            idx = idx + 1

        return ctypes_ip

    return None


def exchange_public_peers_to_list(exchange_public_peers: ExchangePublicPeers) -> list:
    raw_list = list(bytes(exchange_public_peers.peers))
    ip_list = []
    for idx in range(0, len(raw_list), 4):
        ip_str = ""
        ip_str = ip_str + str(raw_list[idx]) + '.'
        ip_str = ip_str + str(raw_list[idx + 1]) + '.'
        ip_str = ip_str + str(raw_list[idx + 2]) + '.'
        ip_str = ip_str + str(raw_list[idx + 3])

        ip_list.append(ip_str)

    return ip_list


def get_protocol_version() -> int:
    try:
        value = getenv("QUBIC_NETWORK_PROTOCOL_VERSION")
    finally:
        if value == None:
            value = -1

    return int(value)


"""Headers
"""


def is_valid_header(header: RequestResponseHeader) -> bool:
    protocol = get_protocol_version()
    min_protocol = protocol - 1
    max_protocol = protocol + 1
    return header.size > 0 and min_protocol <= header.protocol <= max_protocol


def get_header_from_bytes(raw_data: bytes) -> RequestResponseHeader:
    if len(raw_data) < sizeof(RequestResponseHeader):
        raise ValueError("The data cannot be smaller than the header size")

    return RequestResponseHeader.from_buffer_copy(raw_data)


def get_raw_payload(raw_data: bytes):
    try:
        header = get_header_from_bytes(raw_data)
    except Exception as e:
        raise e

    if len(raw_data) < header.size:
        raise ValueError("The data cannot be smaller than header.size")

    return raw_data[sizeof(header):]


def is_valid_computors_data(payload: Computors) -> bool:
    # Checking signature
    data_withou_signature = bytes(payload)[:sizeof(Computors) - SIGNATURE_SIZE]
    digest = kangaroo_twelve(data_withou_signature)
    return verify(ADMIN_PUBLIC_KEY, digest, bytes(payload.signature))


def can_apply_computors_data(computors: Computors):
    return computors.epoch > broadcasted_computors.epoch


async def cache_computors(computors: Computors):
    async with aiofiles.open(COMPUTORS_CACHE_PATH, "wb") as f:
        await f.write(bytes(computors))

    global computors_system_data
    computors_system_data = computors


def get_comutors_system_data():
    global computors_system_data
    return computors_system_data


def get_identities_from_computors(computors: Computors):
    identities = []
    raw_public_key_list = list(bytes(computors.public_keys))
    for idx in range(0, len(raw_public_key_list), 32):
        public_key = bytes(computors.public_keys[idx: idx + 32])
        if public_key != EMPTY_PUBLIC_KEY:
            identities.append(get_identity(public_key))

    return identities


def apply_computors(computors: Computors):
    global broadcasted_computors

    broadcasted_computors.broadcastComputors.computors = computors
