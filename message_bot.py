import discord
import os

from dotenv import load_dotenv
from algorithms.verify import get_public_key_from_id, verify, str_signature_to_bytes, kangaroo_twelve

class MyClient(discord.Client):

    #login
    async def on_ready(self):
        print("i am logged in.")

    #When the message is posted
    async def on_message(self, message):
        print("Message from " + str(message.author) + " contains " + str(message.content))
   
# Read from .env
load_dotenv()
token = os.environ.get("BOT_ACCESS_TOKEN")

client = MyClient()
client.run(str(token))
