import ctypes
from ctypes import CDLL
import os
from sys import platform

def get_qubic_verify_dll():
    if platform == "linux" or platform == "linux2":
        return CDLL(r"libs/qubic_verify/linux/qubic_verify.dll")
    elif platform == "win32":
        return CDLL(r"libs/qubic_verify/win64/qubic_verify.dll")

    return None


qubic_verify_dll = get_qubic_verify_dll() #CDLL(r"../libs/qubic_verify/win64/qubic_verify.dll")


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

    return verify_C( ctypes.c_char_p(public_key), ctypes.c_char_p(digest), ctypes.c_char_p(signature))


