import ctypes
from ctypes import CDLL, create_string_buffer
from sys import platform


def get_qubic_verify_dll():
    import os
    if platform == "linux" or platform == "linux2":
        from qubic_verify import linux

        return CDLL(os.path.join(os.path.dirname(linux.__file__), "libqubic_verify.so"))
    elif platform == "win32":
        from qubic_verify import win64

        return CDLL(os.path.join(os.path.dirname(win64.__file__), "qubic_verify.dll"))

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

def verify_message(public_key: bytes, message: bytes, signature: bytes) -> bool:
    verify_message_C = qubic_verify_dll.verify_message
    verify_message_C.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint64, ctypes.c_char_p]
    verify_message_C.restype = ctypes.c_bool

    return verify_message_C(ctypes.c_char_p(public_key), ctypes.c_char_p(message), ctypes.c_uint64(len(message)), ctypes.c_char_p(signature))

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
    # length must be a multiple of 2
    if len(signature) % 2 != 0:
        signature = 'a' + signature

    signature_bytes_list = []
    for idx in range(0, len(signature), 2):
        high = (ord(signature[idx]) - ord('a')) << 4
        low = (ord(signature[idx + 1]) - ord('a'))
        signature_bytes_list.append(high | low)

    return bytes(signature_bytes_list)


def get_subseed(seed: str):
    get_subseed_C = qubic_verify_dll.get_subseed
    get_subseed_C.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    get_subseed_C.restype = ctypes.c_bool

    subseed_buffer = create_string_buffer(32)
    result = get_subseed_C(ctypes.c_char_p(
        seed.encode('ascii')), subseed_buffer)
    return (result, bytes(subseed_buffer))


def get_private_key(subseed: bytes) -> bytes:
    get_private_key_C = qubic_verify_dll.get_private_key
    get_private_key_C.argtypes = [ctypes.c_char_p, ctypes.c_char_p]

    private_key_buffer = create_string_buffer(32)
    get_private_key_C(ctypes.c_char_p(subseed), private_key_buffer)
    return bytes(private_key_buffer)


def get_public_key(private_key: bytes) -> bytes:
    get_public_key_C = qubic_verify_dll.get_public_key
    get_public_key_C.argtypes = [ctypes.c_char_p, ctypes.c_char_p]

    public_key_buffer = create_string_buffer(32)
    get_public_key_C(ctypes.c_char_p(private_key), public_key_buffer)
    return bytes(public_key_buffer)


def get_identity(public_key: bytes):
    get_identity_C = qubic_verify_dll.get_identity
    get_identity_C.argtypes = [ctypes.c_char_p]

    identity_buffer = (ctypes.c_uint16 * (70))()
    get_identity_C(ctypes.c_char_p(public_key), identity_buffer)

    return ''.join([chr(s) for s in identity_buffer])


def sign(subseed: bytes, public_key: bytes, digest: bytes) -> bytes:
    sign_C = qubic_verify_dll.sign_signature
    sign_C.argtypes = [ctypes.c_char_p, ctypes.c_char_p,
                       ctypes.c_char_p, ctypes.c_char_p]

    signature_buffer = create_string_buffer(64)
    sign_C(ctypes.c_char_p(subseed), ctypes.c_char_p(
        public_key), ctypes.c_char_p(digest), signature_buffer)
    return bytes(signature_buffer)

def sign_message(subseed: bytes, public_key: bytes, message: bytes) -> bytes:
    sign_message_C = qubic_verify_dll.sign_message
    sign_message_C.argtypes = [ctypes.c_char_p, ctypes.c_char_p,
                       ctypes.c_char_p, ctypes.c_uint64, ctypes.c_char_p]

    signature_buffer = create_string_buffer(64)
    sign_message_C(ctypes.c_char_p(subseed), ctypes.c_char_p(
        public_key), ctypes.c_char_p(message), ctypes.c_uint64(len(message)), signature_buffer)
    return bytes(signature_buffer)


def pretty_signatyre(signature: bytes) -> str:
    signature_str: str = ""
    for s in signature:
        signature_str += chr(ord('a') + (s >> 4))
        signature_str += chr(ord('a') + (s & 0x0F))

    return signature_str

def get_score(nonces:bytes, number_of_solution_nonces: int = 1000)->int:
    get_score_C = qubic_verify_dll.get_score
    get_score_C.argtypes = [ctypes.c_char_p, ctypes.c_uint16]
    get_score_C.restype = ctypes.c_uint32

    return get_score_C(ctypes.c_char_p(nonces), number_of_solution_nonces)
