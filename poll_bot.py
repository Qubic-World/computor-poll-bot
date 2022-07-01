import asyncio
import os

from dotenv import load_dotenv
from algorithms.verify import get_public_key_from_id, verify, str_signature_to_bytes, kangaroo_twelve


async def main():
    # Read from .env
    load_dotenv()

    token = os.environ.get("BOT_ACCESS_TOKEN")
    print(F"Token: {token}\n")


if __name__ == "__main__":
    asyncio.run(main())
