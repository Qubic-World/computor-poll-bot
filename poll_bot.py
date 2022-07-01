from array import ArrayType
import asyncio
import ctypes
import os

from dotenv import load_dotenv
from ctypes import CDLL


async def main():
    # Read from .env
    load_dotenv()

    token = os.environ.get("BOT_ACCESS_TOKEN")
    print(F"Token: {token}\n")

    qubic_verify_dll = CDLL(r"libs/qubic_verify/win64/qubic_verify.dll")
    get_public_key_from_id_C = qubic_verify_dll.get_public_key_from_id #getattr(qubic_verify_dll, "get_public_key_from_id")
    get_public_key_from_id_C.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    public_key_type = ctypes.c_ubyte * 32
    pubic_key = public_key_type()
    get_public_key_from_id_C(b"HPJPAFBBPMAGJBOLGDCPHKOHAPFFJMDBCNJOHCOICJIKFELILPJIJABAEMFENFCIBEPMJC", ctypes.cast(pubic_key, ctypes.c_char_p))
    print(*[s for s in pubic_key])

if __name__ == "__main__":
    asyncio.run(main())
