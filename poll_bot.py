import logging
import os

from discord.ext import commands
from dotenv import load_dotenv

from verify.message import get_username_id_from_message, is_valid_message
from verify.user import is_existing_user

poll_bot = commands.Bot(command_prefix="/")


@poll_bot.command()
async def register(ctx, *, json):
    result = is_valid_message(json)
    if result[0] == False:
        await ctx.reply(result[1])
        return

    username_id = get_username_id_from_message(json)

    username_result = await is_existing_user(poll_bot, username_id)
    if username_result[0] == False:
        await ctx.reply("No such user could be found")
        return

    await ctx.reply(f"User {username_result[1]} added")


@poll_bot.event
async def on_ready():
    print("On ready")


def main():
    # Read from .env
    load_dotenv()

    token = os.environ.get("BOT_ACCESS_TOKEN")

    try:
        poll_bot.run(token)
    except Exception as e:
        logging.error(e)


if __name__ == "__main__":
    main()
