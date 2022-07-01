import asyncio
import os

from dotenv import load_dotenv
from algorithms.verify import get_public_key_from_id, verify


async def main():
    # Read from .env
    load_dotenv()

    token = os.environ.get("BOT_ACCESS_TOKEN")
    print(F"Token: {token}\n")

    print(verify(get_public_key_from_id("HPJPAFBBPMAGJBOLGDCPHKOHAPFFJMDBCNJOHCOICJIKFELILPJIJABAEMFENFCIBEPMJC"), bytes([0x3]), bytes([0x4])))


if __name__ == "__main__":
    asyncio.run(main())
