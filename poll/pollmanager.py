import asyncio
from typing import Optional
from uuid import UUID, uuid4

from checkers import has_role_on_member
from commands.pool import pool_commands
from data.identity import identity_manager
from data.users import user_data
from discord import Client, Embed, Message
from discord.ext import commands
from discord.ext.commands import Context
from discord_components import Button, ButtonStyle
from utils.botutils import get_channel_id, get_role_name

DESCRIPTION_FIELD = "description"
VARIANTS_FIELD = "variants"

FIELDS = [DESCRIPTION_FIELD, VARIANTS_FIELD]

VARIANT_NUMBERS = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣', '🔟']

MINIMUM_NUMBER_OF_VARIANTS = 1
MAXIMUM_NUMBER_OF_VARIANTS = 5
BUTTON_CLICK_EVENT_NAME = "button_click"


class Poll():
    """Responsible for counting votes, serialization, deserialization of the poll
    """

    def __init__(self, bot: Client, ctx: Context, description: str, variants: list) -> None:
        self.__bot = bot
        self.__ctx = ctx
        self.__description = description
        self.__variants = variants
        """Poll ID
        """
        self.__id: UUID = uuid4()
        self.__poll_message_id: Optional[int] = None
        self.__poll_message: Optional[Message] = None
        self.__done_callback = set()
        self.__components = []
        self.__background_tasks = []
        """Number of votes for a specific vote
        """
        self.__vote_counter = dict()
        """Users who took part in the poll and their numbers of votes
        """
        self.__voted_users = dict()

    async def __listen_buttons(self):
        custom_id_list = [
            component.custom_id for component in self.__components]

        def check_role(member):
            """Only people with a role can click the buttons
            """
            return get_role_name() in [role.name for role in member.roles]

        def check_button(custom_id: str):
            """Process only those buttons that relate to this poll
            """
            return custom_id in custom_id_list

        def has_unused_votes(user_id: int):
            """Each user can vote as many times as their ID is in 676
            """
            identity_set = user_data.user_identity(user_id)
            if len(identity_set) <= 0:
                return

            total_user_number_of_votes = len(
                [id for id in identity_set if id in identity_manager.identity])
            if total_user_number_of_votes <= 0:
                return False

            number_of_votes = self.__voted_users.setdefault(user_id, 0)
            return total_user_number_of_votes > number_of_votes

        def check(interaction):
            user = interaction.user
            return check_role(user) and check_button(interaction.custom_id) and has_unused_votes(user.id)

        def get_variant_index(interaction):
            """Get the variant number from the button pressed
            """
            return custom_id_list.index(interaction.custom_id)

        def get_variant(interaction):
            """Get variant on the button pressed
            """
            return self.__variants[get_variant_index(interaction)]

        def add_vote(interaction):
            """Increasing the number of votes
            """

            """Increase the number of votes of a particular user
            """
            user_id = interaction.user.id
            value = self.__voted_users.setdefault(user_id, 0)
            self.__voted_users[user_id] = value + 1

            dict_key = get_variant_index(interaction)
            value = self.__vote_counter.setdefault(dict_key, 0)
            self.__vote_counter[dict_key] = value + 1

        def pretty_vote_count():
            list_vote = []
            for key, value in self.__vote_counter.items():
                list_vote.append(f"{key + 1}: {value}")

            return ", ".join(list_vote)

        while True:
            try:
                """Waiting for the button to be clicked
                """
                interaction = await self.__bot.wait_for(BUTTON_CLICK_EVENT_NAME, check=check)

                await interaction.send(content=f"You voted for the option: {get_variant(interaction)}")
                """Increasing the number of votes
                """
                add_vote(interaction)

                # if self.__poll_message == None:
                #     self.__poll_message =self.__get_message_by_id()
                #     if self.__poll_message == None:
                #         raise ValueError("Failed to retrieve ID message")

                """Outputting the number of votes
                """
                embed: Embed = self.__poll_message.embeds[0]
                embed.set_footer(text=f'Vote count:\n {pretty_vote_count()}')
                await self.__poll_message.edit(embed=embed)

            except asyncio.CancelledError:
                pass

    async def __get_message_by_id(self) -> Message:
        channel = self.__bot.get_channel(get_channel_id())
        return await channel.fetch_message(self.__poll_message_id)

    async def create(self):
        embed = Embed(title="Poll", description=self.__description)

        variant_len = len(self.__variants)
        value = "\n".join(
            [f"{VARIANT_NUMBERS[idx]} {self.__variants[idx]}" for idx in range(0, variant_len)])
        embed.add_field(name="Variants:", value=value, inline=False)
        self.__components = [Button(style=ButtonStyle.grey, label=str(idx + 1), custom_id=f"button{idx}_{self.__id}")
                             for idx in range(0, variant_len)]

        message = await self.__ctx.reply(embed=embed, components=[self.__components])
        self.__poll_message_id = message.id
        self.__poll_message = message

        task = asyncio.create_task(self.__listen_buttons())
        self.__background_tasks.append(task)
        task.add_done_callback(self.__background_tasks.remove)

    async def done(self):
        """Completing the poll
        """

        """Removing the voting buttons
        """
        await self.__poll_message.edit(components=[])

        """Notify listeners that the poll has been completed
        """
        if len(self.__done_callback) > 0:
            coroutine_list = []
            for callback in self.__done_callback:
                if asyncio.iscoroutinefunction(callback):
                    coroutine_list.append(asyncio.create_task(callable(self)))
                else:
                    callable(self)

            if len(coroutine_list) > 0:
                await asyncio.wait(coroutine_list)

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


class PollManager():
    def __init__(self) -> None:
        pass


poll_manager = PollManager()
