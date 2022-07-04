from ast import Delete
from unittest import result
import discord
import os
import re

from dotenv import load_dotenv
from algorithms.verify import get_public_key_from_id, verify, str_signature_to_bytes, kangaroo_twelve


voting_array = []
one_array = []
two_array = []
three_array = []
four_array = []
five_array = []
total_votes = 0

#beginn Vote settings
question = "What do we want to do?"
one_answer = "eat"
two_answer = "sleep"
three_answer = "developent"
four_answer = "mining"
five_answer = "all"
#End Vote settings

async def show_result(message):
    await message.channel.send(str(total_votes) + ''' votes to: ''' + question + '''\n
            1 = ''' + str(len(one_array)) + ''' (''' + one_answer + ''')
            2 = ''' + str(len(two_array))  + ''' (''' + two_answer + ''')
            3 = ''' + str(len(three_array))  + ''' (''' + three_answer + ''')
            4 = ''' + str(len(four_array))  + ''' (''' + four_answer + ''')
            5 = ''' + str(len(five_array))  + ''' (''' + five_answer + ''')
            ''')         

class MyClient(discord.Client):    

    #login
    async def on_ready(self):
        print("i am logged in.")

    #When the message is posted
    async def on_message(self, message):

        global voting_array 
        global one_array 
        global two_array 
        global three_array
        global four_array 
        global five_array 
        global total_votes 

        if message.author == client.user:
            return

        print("Message from " + str(message.author) + " contains " + str(message.content))       

        # $voting 1 EPJCKMDJIHGMGGPGPFPBICILHPILGBHOFIKJPBMLIJIAADLEDCKFDKODGAEMPDGIPPLOEM
        if(message.content == "/help_voting"):
             await message.channel.send('''to vote: /voting NUMBER ID (where NUMBER is the choice and ID the PublicID)\n
                Question: ''' + question + '''\n
                1 = ''' + one_answer + '''\n
                2 = ''' + two_answer + '''\n
                3 = ''' + three_answer + '''\n
                4 = ''' + four_answer + '''\n
                5 = ''' + five_answer + '''\n\n
                show result: /voting_result'''
                )
        
        if(message.content == "/voting_result"):
            await show_result(message)           

        if message.content.startswith("/voting"):
            voting_array =  message.content.split(' ')           

            if(len(voting_array) < 3):
                await message.channel.send("wrong parameters, please enter $help-voting")
                return

            choice = voting_array[1]
            id = voting_array[2].upper()

            if(choice == "" or id == ""):
                await message.channel.send("wrong parameters, please enter $help-voting")
                return

            # Voting end by 451
            if(total_votes > 2): 
                await message.channel.send("Voting ends as follows")
                await show_result(message)     
                return

            # is choice a number
            if(choice.isdigit() == False):
                await message.channel.send("Voting is not a number!") 
                return

            choice_number = int(choice)

            # check length publicId
            if(len(id) != 70):
                await message.channel.send("The length of the PublicID is incorrect!") 
                return

            # between 1 and 5
            if(choice_number < 0 or 5 < choice_number):
                await message.channel.send("Voting is out of selection!") 
                return

            # has already chosen the publicId
            if(id in one_array or id in two_array or id in three_array or id in four_array or id in five_array ):
                await message.channel.send("You have already voted with this PublicID: " + id) 
                return

            await message.channel.send("You voted for " + choice)       

            if(choice_number == 1):
                one_array.append(id)

            if(choice_number == 2):
                two_array.append(id)

            if(choice_number == 3):
                three_array.append(id)

            if(choice_number == 4):
                four_array.append(id)
            
            if(choice_number == 5):
                five_array.append(id)

            total_votes = len(one_array) + len(two_array) + len(three_array) + len(four_array) + len(five_array)
           
            await show_result(message)    

# Read from .env
load_dotenv()
token = os.environ.get("BOT_ACCESS_TOKEN")

client = MyClient()
client.run(str(token))
