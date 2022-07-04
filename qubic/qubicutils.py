from ctypes import sizeof
from os import getenv

from qubicdata import ExchangePublicPeers, RequestResponseHeader, c_ip_type


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

def get_protocol_version()->int:
        try:
            value = getenv("QUBIC_NETWORK_PROTOCOL_VERSION")
        finally:
            if value == None:
                value = -1

        return int(value)

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

    return raw_data[sizeof(header): ]

def exchange_public_peers_to_list(exchange_public_peers: ExchangePublicPeers)->list:
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