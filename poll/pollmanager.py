import asyncio
import os
import sys
from typing import Optional
from uuid import UUID, uuid4

from discord import Embed,  Client
from discord.ext import commands
from discord.ext.commands import Context
from discord_components import Button, ButtonStyle

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from commands.pool import pool_commands
from checkers import has_role_on_member

DESCRIPTION_FIELD = "description"
VARIANTS_FIELD = "variants"

FIELDS = [DESCRIPTION_FIELD, VARIANTS_FIELD]

VARIANT_NUMBERS = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣', '🔟']

MINIMUM_NUMBER_OF_VARIANTS = 1
MAXIMUM_NUMBER_OF_VARIANTS = 5


class Poll():
    """Responsible for counting votes, serialization, deserialization of the poll
    """
    def __init__(self, bot: Client, ctx: Context, description: str, variants: list) -> None:
        self.__bot = bot
        self.__ctx = ctx
        self.__description = description
        self.__variants = variants
        self.__id:UUID = uuid4()
        self.__poll_message_id: Optional[int] = None
        self.__done_callback = set()
        self.__components = []
        self.__background_tasks = []

    async def __listen_buttons(self):
        pass

    async def create(self):
        embed = Embed(title="Poll", description=self.__description)
        embed.set_footer(text=f"ID: {str(self.__id.hex)}")

        variant_len = len(self.__variants)
        value = "\n".join(
            [f"{VARIANT_NUMBERS[idx]} {self.__variants[idx]}" for idx in range(0, variant_len)])
        embed.add_field(name="Variants:", value=value, inline=False)
        self.__components = [Button(style=ButtonStyle.grey, label=str(idx + 1), custom_id=f"button{idx}_{self.__id}")
                      for idx in range(0, variant_len)]

        message = await self.__ctx.reply(embed=embed, components=[self.__components])
        self.__poll_message_id = message.id

        task = asyncio.create_task(self.__listen_buttons())
        self.__background_tasks.append(task)
        task.add_done_callback(self.__background_tasks.remove)
        

    async def done(self):
        await asyncio.wait([asyncio.create_task(callback(self)) for callback in self.__done_callback])

    def add_done_callback(self, function):
        self.__done_callback.add(function)




class PollCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.__bot = bot
        self.__poll_list = []

    def _is_valid_message(self, description: str, *variants: str):
        if len(variants) >= MINIMUM_NUMBER_OF_VARIANTS and len(variants) <= MAXIMUM_NUMBER_OF_VARIANTS:
            return True, ""

        return False, f"The number of variants should be from {MINIMUM_NUMBER_OF_VARIANTS} to {MAXIMUM_NUMBER_OF_VARIANTS}"

    def get_description(self, json_body: dict):
        return json_body[DESCRIPTION_FIELD]

    def get_variants(self, json_body: dict):
        return list(json_body[VARIANTS_FIELD])

    @commands.check(has_role_on_member)
    @commands.command(name="poll")
    async def poll_command(self, ctx: Context, description, *variants):
        await pool_commands.add_command(self._on_poll, ctx, description, *variants)

    async def _on_poll(self, ctx: Context, description, *variants):
        success, message = self._is_valid_message(description, *variants)
        if success == False:
            await ctx.reply(message)
            return


        poll = Poll(self.__bot, ctx, description, variants)
        self.__poll_list.append(poll)
        poll.add_done_callback(self.__poll_list.remove)
        await poll.create()
        return

        embed = Embed(title="Poll", description=description)

        value = "\n".join(
            [f"{VARIANT_NUMBERS[idx]} {variants[idx]}" for idx in range(0, len(variants))])
        embed.add_field(name="Variants:", value=value, inline=False)
        components = [Button(style=ButtonStyle.grey, label=str(idx + 1))
                      for idx in range(0, len(variants))]

        message = await ctx.reply(embed=embed, components=components)


class PollManager():
    def __init__(self) -> None:
        pass


poll_manager = PollManager()
