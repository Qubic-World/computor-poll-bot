from ast import Delete
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
        if message.author == client.user:
            return

        print("Message from " + str(message.author) + " contains " + str(message.content))

        if(message.content == "$help"):
            await message.channel.send("$transferTo ID = transfer to ID\n...")

        if message.content.startswith("$transferTo"):
            id = message.content.split(' ')[1]
            await message.channel.send("transfer success to " + id)       

        if message.content.startswith("$hello bot"):
            await message.channel.send('hello boss') 
            #private message
            await message.author.send("hello boss!")    # Delete after=120 file send 

   
# Read from .env
load_dotenv()
token = os.environ.get("BOT_ACCESS_TOKEN")

client = MyClient()
client.run(str(token))
