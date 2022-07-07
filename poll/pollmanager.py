import os
import sys

from discord import Embed
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


class Poll():
    """Responsible for counting votes, serialization, deserialization of the poll
    """
    pass


class PollCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.__bot = bot

    def _is_valid_message(self, description: str, *variants: str):
        if len(variants) <= 0 or len(variants) > 10:
            return False, "The number of variants should be from 1 to 10"

        return True, ""

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

        # TODO: Move the logic to Poll

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
