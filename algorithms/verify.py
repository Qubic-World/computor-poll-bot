import ctypes
from ctypes import CDLL, create_string_buffer
from hmac import digest
import os
from sys import platform


def get_qubic_verify_dll():
    if platform == "linux" or platform == "linux2":
        return CDLL(r"libs/qubic_verify/linux/libqubic_verify.so")
    elif platform == "win32":
        return CDLL(r"libs/qubic_verify/win64/qubic_verify.dll")

    return None


qubic_verify_dll = get_qubic_verify_dll()


def get_public_key_from_id(id: str) -> bytes:
    get_public_key_from_id_C = qubic_verify_dll.get_public_key_from_id
    get_public_key_from_id_C.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    public_key_type = (ctypes.c_ubyte * 32)
    pubic_key = public_key_type()
    get_public_key_from_id_C(
        id.encode('ascii'), ctypes.cast(pubic_key, ctypes.c_char_p))
    return bytes(pubic_key)


def verify(public_key: bytes, digest: bytes, signature: bytes) -> bool:
    verify_C = qubic_verify_dll.verify_signature
    verify_C.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
    verify_C.restype = ctypes.c_bool

    return verify_C(ctypes.c_char_p(public_key), ctypes.c_char_p(digest), ctypes.c_char_p(signature))


def kangaroo_twelve(data: bytes) -> bytes:
    kangaroo_twelve_C = qubic_verify_dll.kangaroo_twelve
    kangaroo_twelve_C.argtypes = [
        ctypes.c_char_p, ctypes.c_ulonglong, ctypes.c_char_p, ctypes.c_ulonglong]

    digest_size = 32
    digest_buffer = create_string_buffer(digest_size)
    kangaroo_twelve_C(ctypes.c_char_p(data), ctypes.c_ulonglong(
        len(data)), digest_buffer, digest_size)
    return bytes(digest_buffer)


def str_signature_to_bytes(signature: str) -> bytes:
    if len(signature) != 128:
        return bytes()

    signature_bytes_list = []
    for idx in range(0, len(signature), 2):
        high = (ord(signature[idx]) - ord('a')) << 4
        low = (ord(signature[idx + 1]) - ord('a'))
        signature_bytes_list.append(high | low)

    return bytes(signature_bytes_list)
