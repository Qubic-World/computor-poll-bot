import asyncio
import os

from dotenv import load_dotenv
from algorithms.verify import get_public_key_from_id, verify, str_signature_to_bytes, kangaroo_twelve


async def main():
    # Read from .env
    load_dotenv()

    token = os.environ.get("BOT_ACCESS_TOKEN")
    print(F"Token: {token}\n")

    # print(kangaroo_twelve(b"test"))

    # print(str_signature_to_bytes("oamjjcmpbgfmjlniknkmejhacaphflcchbfiaelgbdndmigbkinngdjplcjihlacdfncbabnihanfhpjnmngkfgbedhdclfhfhckkdmdahnblmgcebcffjipdainadaa"))

    print(verify(get_public_key_from_id("BPHPEIHDBADJJPMHBEEJLIGBFFCAONGDCOEKIPHPPHCIJDAECDOIGIPFKGGDAKDMADNMKO"), kangaroo_twelve(b"test"), str_signature_to_bytes(
        "oamjjcmpbgfmjlniknkmejhacaphflcchbfiaelgbdndmigbkinngdjplcjihlacdfncbabnihanfhpjnmngkfgbedhdclfhfhckkdmdahnblmgcebcffjipdainadaa")))


if __name__ == "__main__":
    asyncio.run(main())
