import logging
import os
import re
import sys
from ctypes import sizeof
from os import getenv

import aiofiles
from algorithms.verify import get_identity, kangaroo_twelve, verify

from qubic.qubicdata import (ADMIN_PUBLIC_KEY, EMPTY_PUBLIC_KEY,
                             SIGNATURE_SIZE, Computors, ExchangePublicPeers,
                             RequestResponseHeader, System, c_ip_type,
                             computors_system_data)

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
    return header.protocol == get_protocol_version() and header.size > 0


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


def is_valid_broadcast_computors(payload: Computors) -> bool:
    if payload.protocol != get_protocol_version():
        return False

    # Checking signature
    print(f"Sizeof Computors: {sizeof(payload)}")
    data_withou_signature = bytes(payload)[:sizeof(Computors) - SIGNATURE_SIZE]
    print(f"Len butes: {len(data_withou_signature)}")
    digest = kangaroo_twelve(data_withou_signature)
    return verify(ADMIN_PUBLIC_KEY, digest, bytes(payload.signature))


def can_apply_computors_data(computors: Computors):
    return computors.epoch > computors_system_data.epoch or (computors.epoch == computors_system_data.epoch and computors.index > computors_system_data.index)


async def cache_computors(computors: Computors):
    async with aiofiles.open(COMPUTORS_CACHE_PATH, "wb") as f:
        await f.write(bytes(computors))

    global computors_system_data
    computors_system_data = computors


def get_comutors_system_data():
    global computors_system_data
    return computors_system_data


async def load_cache_computors():
    if not os.path.isfile(COMPUTORS_CACHE_PATH):
        return

    async with aiofiles.open(COMPUTORS_CACHE_PATH, "rb") as f:
        global computors_system_data
        b = await f.read()
        len_b = len(b)
        logging.info(
            f'Len bytes: {len_b}, sizeof System: {sizeof(System)}, sizeof Computors: {sizeof(Computors)}')
        if len_b == sizeof(System):
            logging.info('Loading computors from System')
            system = System.from_buffer_copy(b)
            computors_system_data = system.computors
            return

        if len_b != sizeof(Computors):
            return

        logging.info('Loading computors from Computors')
        computors_system_data = Computors.from_buffer_copy(b)


def get_identities_from_computors(computors: Computors):
    identities = []
    raw_public_key_list = list(bytes(computors.public_keys))
    for idx in range(0, len(raw_public_key_list), 32):
        public_key = bytes(computors.public_keys[idx: idx + 32])
        if public_key != EMPTY_PUBLIC_KEY:
            identities.append(get_identity(public_key))

    return identities


async def apply_computors_data(computors: Computors):
    if can_apply_computors_data(computors):
        await cache_computors(computors)
        # identity = []
        # raw_public_key_list = list(bytes(computors.public_keys))
        # for idx in range(0, len(raw_public_key_list), 32):
        #     public_key = bytes(computors.public_keys[idx: idx + 32])
        #     if public_key != EMPTY_PUBLIC_KEY:
        #         identity.append(get_identity(public_key))

        # identity_manager.apply_identity(identity)

        # # TODO: The identity save to file can be removed, as the public keys are stored in COMPUTORS_CACHE_PATH
        # # await cache_computors(computors)
        # # await identity_manager.save_to_file()
        # await asyncio.gather(cache_computors(computors), identity_manager.save_to_file())
