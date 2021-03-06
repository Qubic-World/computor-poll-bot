import asyncio
import json
import logging
from typing import Optional
from uuid import UUID, uuid4

import aiofiles
from checkers import has_role_on_member, is_bot_channel
from commands.pool import pool_commands
from data.identity import identity_manager
from data.users import user_data
from discord import Client, Embed, Message, errors
from discord.ext import commands
from discord.ext.commands import Context
from discord_components import Button, ButtonStyle
from utils.botutils import (get_poll_channel_id, get_poll_message_by_id,
                            get_role_name)

DESCRIPTION_FIELD = "description"
VARIANTS_FIELD = "variants"
FIELDS = [DESCRIPTION_FIELD, VARIANTS_FIELD]
POLL_FIELDS = ["id", "variants", "poll_message_id",
               "vote_counter", "voted_users"]

VARIANT_NUMBERS = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣', '🔟']
MINIMUM_NUMBER_OF_VARIANTS = 1
MAXIMUM_NUMBER_OF_VARIANTS = 5
NUMBER_OF_VOTES_FOR_END = 451


BUTTON_CLICK_EVENT_NAME = "button_click"


class Poll():
    """Responsible for counting votes, serialization, deserialization of the poll
    """

    def __init__(self, bot: Client, ctx: Context, description: str, variants: list) -> None:
        self.__bot = bot
        self.__ctx = ctx
        self.__description = description
        self.__variants = variants
        self.__poll_channel = bot.get_channel(get_poll_channel_id())
        if self.__poll_channel == None:
            raise ValueError("__poll_channel is None")

        """Poll ID
        """
        self.__id: UUID = uuid4()
        self.__poll_message_id: Optional[int] = None
        self.__poll_message: Optional[Message] = None
        self.__done_callback = set()
        self.__create_callback = set()
        self.__voted_callback = set()
        self.__recount_callback = set()
        self.__components = []
        self.__components_id = []
        self.__background_tasks = []
        """Which users voted for which variant
        {user_id: variant_idx}
        """
        self.__selected_variants = dict()
        """Users and their IDs who voted
        {user_id: ["AAAAA...", "BBBBB..."]}
        """
        self.__voted_users = dict()

    @property
    def message_id(self):
        return self.__poll_message_id

    @property
    def number_of_voters(self):
        """Number of votes received
        """
        vote_counts = self.get_vote_counts()
        sum = 0
        for count in vote_counts.values():
            sum += count

        return sum

    def get_vote_counts(self):
        """
        {variant_idx: count}
        """
        vote_counts = dict()
        for user_id, variant in self.__selected_variants.items():
            # The number of IDs equals the number of votes
            count = len(self.__voted_users[user_id])
            vote_count = vote_counts.setdefault(variant, 0)
            vote_counts[variant] = vote_count + count

        return vote_counts

    def pretty_vote_count(self):
        list_vote = []
        for key, value in sorted(self.get_vote_counts().items()):
            if value > 0:
                list_vote.append(f"{key + 1}: {value}")

        return ", ".join(list_vote)

    async def resend_embed(self):
        embed: Embed = self.__poll_message.embeds[0]
        embed.set_footer(text=f'Vote count:\n {self.pretty_vote_count()}')
        await self.__poll_message.edit(embed=embed)

    def update_user_identities(self, user_id: int) -> bool:
        if user_id in self.__voted_users.keys():
            computor_identities = identity_manager.get_only_computor_identities(
                user_data.get_user_identities(user_id))
            self.__voted_users[user_id] = computor_identities
            return True
        else:
            logging.warning(
                f"Poll.update_user_identities: user_id {user_id} is not found")

        return False

    async def recount_votes_by_user_id(self, user_id: int):
        if self.update_user_identities(user_id):
            try:
                await self.resend_embed()
            except Exception as e:
                logging.warning(e)

            await self.call_callback(self.__recount_callback)

    async def recount_votes(self):
        # Overwriting the ID
        was_update = False
        for user_id in self.__voted_users.keys():
            if self.update_user_identities(user_id) and was_update == False:
                was_update = True

        if was_update:
            try:
                await self.resend_embed()
            except Exception as e:
                logging.warning(e)

            await self.call_callback(self.__recount_callback)

    def as_dict(self):
        return {POLL_FIELDS[0]: str(self.__id),
                POLL_FIELDS[1]: list(self.__variants),
                POLL_FIELDS[2]: self.__poll_message_id,
                POLL_FIELDS[3]: str(self.__selected_variants),
                POLL_FIELDS[4]: str(self.__voted_users)}

    async def __start_listen_byttons(self):
        task = asyncio.create_task(self.__listen_buttons())
        self.__background_tasks.append(task)
        task.add_done_callback(self.__background_tasks.remove)

    async def __listen_buttons(self):
        def check_role(member):
            """Only people with a role can click the buttons
            """
            return get_role_name() in [role.name for role in member.roles]

        def check_button(custom_id: str):
            """Process only those buttons that relate to this poll
            """
            return custom_id in self.__components_id

        def is_voted(user_id: int):
            """Did the user vote
            """
            return user_id in self.__voted_users.keys()

        def check(interaction):
            user = interaction.user
            return check_role(user) and check_button(interaction.custom_id) and not is_voted(user.id)

        def get_variant_index(interaction):
            """Get the variant number from the button pressed
            """
            return self.__components_id.index(interaction.custom_id)

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
            computor_identities = identity_manager.get_only_computor_identities(
                user_data.get_user_identities(user_id))
            self.__voted_users.setdefault(user_id, computor_identities)

            variant_idx = get_variant_index(interaction)
            self.__selected_variants.setdefault(user_id, variant_idx)

        while True:
            try:
                """Waiting for the button to be clicked
                """
                interaction = await self.__bot.wait_for(BUTTON_CLICK_EVENT_NAME, check=check)

                try:
                    await interaction.send(content=f"You voted for the option: {get_variant(interaction)}")
                except errors.NotFound as e:
                    logging.warning(e)
                """Increasing the number of votes
                """
                add_vote(interaction)

                """Outputting the number of votes
                """
                await self.resend_embed()

                await self.call_callback(self.__voted_callback)

                if self.number_of_voters == NUMBER_OF_VOTES_FOR_END:
                    await self.done()

            except asyncio.CancelledError:
                pass

    async def create(self):
        embed = Embed(title="Poll", description=self.__description)

        variant_len = len(self.__variants)
        value = "\n".join(
            [f"{VARIANT_NUMBERS[idx]} {self.__variants[idx]}" for idx in range(0, variant_len)])
        embed.add_field(name="Variants:", value=value, inline=False)
        self.__components = [Button(style=ButtonStyle.grey, label=str(idx + 1), custom_id=f"button{idx}_{self.__id}")
                             for idx in range(0, variant_len)]

        self.__components_id = [
            component.custom_id for component in self.__components]

        await self.__ctx.reply("Success", delete_after=10)
        message = await self.__poll_channel.send(embed=embed, components=[self.__components])
        self.__poll_message_id = message.id
        self.__poll_message = message

        await self.__start_listen_byttons()

        await self.call_callback(self.__create_callback)

    async def create_from_dict(self, data: dict):
        self.__id = UUID(data[POLL_FIELDS[0]])
        self.__variants = data[POLL_FIELDS[1]]
        self.__poll_message_id = int(data[POLL_FIELDS[2]])
        self.__selected_variants = eval(data[POLL_FIELDS[3]])
        self.__voted_users = eval(data[POLL_FIELDS[4]])

        self.__components_id = [
            f"button{idx}_{self.__id}" for idx in range(0, len(self.__variants))]

        self.__poll_message = await get_poll_message_by_id(self.__bot, self.__poll_message_id)

        await self.__start_listen_byttons()

    async def call_callback(self, functions, *args):
        if len(functions) > 0:
            coroutine_list = []
            for callback in functions:
                if asyncio.iscoroutinefunction(callback):
                    coroutine_list.append(
                        asyncio.create_task(callback(self, *args)))
                else:
                    callback(self, *args)

            if len(coroutine_list) > 0:
                await asyncio.wait(coroutine_list)

    async def done(self):
        """Completing the poll
        """

        """Removing the voting buttons
        """
        await self.__poll_message.edit(components=[])

        """Notify listeners that the poll has been completed
        """
        await self.call_callback(self.__done_callback)

    def add_done_callback(self, function):
        self.__done_callback.add(function)

    def add_crete_callback(self, function):
        self.__create_callback.add(function)

    def add_voted_callback(self, function):
        self.__voted_callback.add(function)

    def add_recount_callback(self, function):
        self.__recount_callback.add(function)


class PollCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.__bot: Client = bot
        self.__poll_list = []
        self.__cache_file = r"./data_files/poll_cache.data"

    @property
    def polls(self):
        return self.__poll_list

    def _is_valid_message(self, description: str, *variants: str):
        if len(variants) >= MINIMUM_NUMBER_OF_VARIANTS and len(variants) <= MAXIMUM_NUMBER_OF_VARIANTS:
            return True, ""

        return False, f"The number of variants should be from {MINIMUM_NUMBER_OF_VARIANTS} to {MAXIMUM_NUMBER_OF_VARIANTS}"

    def get_description(self, json_body: dict):
        return json_body[DESCRIPTION_FIELD]

    def get_variants(self, json_body: dict):
        return list(json_body[VARIANTS_FIELD])

    def init_callback(self, poll: Poll):
        poll.add_done_callback(self.__on_done)
        poll.add_crete_callback(self._save_polls_to_file)
        poll.add_voted_callback(self._save_polls_to_file)
        poll.add_recount_callback(self._save_polls_to_file)

    @commands.check(has_role_on_member)
    @commands.check(is_bot_channel)
    @commands.command(name="poll")
    async def poll_command(self, ctx: Context, description, *variants):
        """Creating a poll in which only participants with the Computor role can take part
        Example:
        /poll "poll body" "var 1" "var 2" "var 3"
        """
        await pool_commands.add_command(self._on_poll, ctx, description, *variants)

    async def recount(self, *args, **kwargs):
        """Recount of votes in all polls
        """
        try:
            user_id: int = kwargs['user_id']
        except:
            user_id = None

        poll: Poll = None
        tasks = []
        for poll in self.__poll_list:
            if user_id != None:
                task = asyncio.create_task(
                    poll.recount_votes_by_user_id(user_id))
            else:
                task = asyncio.create_task(poll.recount_votes())

            tasks.append(task)

        if len(tasks) > 0:
            await asyncio.wait(tasks)

    async def _on_poll(self, ctx: Context, description, *variants):
        success, message = self._is_valid_message(description, *variants)
        if success == False:
            await ctx.reply(message)
            return

        poll = Poll(self.__bot, ctx, description, variants)
        self.__poll_list.append(poll)

        self.init_callback(poll)
        await poll.create()

    async def __cleanup(self):
        """Deletes non-existing polls
        """
        async def is_exists_message(message_id: int) -> bool:
            try:
                message: Message = await get_poll_message_by_id(self.__bot, message_id)
            except:
                return False

            return True

        """Delete polls that don't exist or have been completed and haven't closed for some reason
        """
        tasks = []
        for item in self.__poll_list:
            tasks.append(asyncio.create_task(
                is_exists_message(item.message_id)))

        dict_list = []
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for idx in reversed(range(len(results))):
            result = results[idx]
            poll_item: Poll = self.__poll_list[idx]
            if type(result) is Exception or result == False:
                self.__poll_list.remove(poll_item)
            else:
                if poll_item.number_of_voters >= NUMBER_OF_VOTES_FOR_END:
                    await poll_item.done()

    async def _save_polls_to_file(self, poll: Poll):
        await self.__cleanup()

        dict_list = [poll_item.as_dict() for poll_item in self.__poll_list]

        async with aiofiles.open(self.__cache_file, "w") as f:
            await f.write(json.dumps(str(dict_list)))

    async def _load_polls_from_file(self):
        dict_list = []
        try:
            async with aiofiles.open(self.__cache_file, "r") as f:
                dict_list = list(eval(json.loads(await f.read())))
        except FileNotFoundError:
            return

        if len(dict_list) <= 0:
            return

        for data in dict_list:
            poll = Poll(self.__bot, None, "", "")
            try:
                await poll.create_from_dict(data)
            except:
                pass

            self.__poll_list.append(poll)
            self.init_callback(poll)

        # After loading from a file, delete invalid polls
        old_size = len(self.__poll_list)
        await self.__cleanup()
        if len(self.__poll_list) != old_size:
            await self._save_polls_to_file(None)

    async def __on_done(self, poll: Poll):
        try:
            self.__poll_list.remove(poll)
        except ValueError:
            pass

        await self.__save_polls_to_file()(None)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        removed = False
        for poll in reversed(self.__poll_list):
            if poll.message_id == message.id:
                self.__poll_list.remove(poll)
                removed = True

        if removed:
            await self.__save_polls_to_file()(None)


class PollManager():
    def __init__(self) -> None:
        pass


poll_manager = PollManager()
