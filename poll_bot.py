import asyncio
import os

from dotenv import load_dotenv


async def main():
    # Read from .env
    load_dotenv()

    token = os.environ.get("BOT_ACCESS_TOKEN")
    print(F"Token: {token}")

if __name__ == "__main__":
    asyncio.run(main())
