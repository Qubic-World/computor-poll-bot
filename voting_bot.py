from ast import Delete
from asyncore import poll
from unittest import result
import discord
import os
import json

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
question = ""
one_answer = ""
two_answer = ""
three_answer = ""
four_answer = ""
five_answer = ""
#End Vote settings

async def show_result(message):
    await message.channel.send(str(total_votes) + ''' votes to: \"''' + str(question) + '''\"
            ''' + str(len(one_array)) + '''(1) = ''' + str(one_answer) + '''
            ''' + str(len(two_array))  + '''(2) = ''' + str(two_answer) + '''
            ''' + str(len(three_array))  + '''(3) = ''' + str(three_answer) + '''
            ''' + str(len(four_array))  + '''(4) = ''' + str(four_answer) + '''
            ''' + str(len(five_array))  + '''(5) = ''' + str(five_answer)
            )   


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

        global question
        global one_answer
        global two_answer
        global three_answer
        global four_answer
        global five_answer

        if message.author == client.user:
            return

        print("Message from " + str(message.author) + " contains " + str(message.content))  

        #/poll_add {"poll_text": "texttexttexttext", 
        # "buttons": [{"button1": "button 1"}, {"button2": "button 2"}, {"button3": "button 3"}, {"button4": "button 4"}, {"button5": "button 5"}]}
        if message.content.startswith("/poll_add"):
            if(question == ""):                               
                array =  message.content.split('add {')                 
                jsonString = '{'+array[1]
                pollObject = json.loads(jsonString)
                question = pollObject["poll_text"]
                
                buttonsObject = pollObject["buttons"]

                one_answer = buttonsObject[0]["button1"]
                two_answer = buttonsObject[1]["button2"]
                three_answer = buttonsObject[2]["button3"]
                four_answer = buttonsObject[3]["button4"]
                five_answer =buttonsObject[4]["button5"]
                total_votes = 0

                await show_result(message)   
            else:
                await message.channel.send("A survey is already running") 
            return
                

        if(message.content == "/poll_show"):
            if(question == ""):
                await message.channel.send("There is no poll available.") 
                return  
            
            await show_result(message)
            return

        if(message.content == "/poll_help"):
            await message.channel.send('''Functions:
                /poll_help
                /poll_add {\"poll_text\": \"question\", \"buttons\": [{\"button1\": \"buttonText\"}, {\"button2\": \"buttonText\"}, {\"button3\": \"buttonText\"}, {\"button4\": \"buttonText\"}, {\"button5\": \"buttonText\"}]}
                /poll_show
                /help_voting
                /voting_result
                /voting NUMBER PUBLIC_ID ''')
            return
        
        # /voting 1 EPJCKMDJIHGMGGPGPFPBICILHPILGBHOFIKJPBMLIJIAADLEDCKFDKODGAEMPDGIPPLOEM
        if(message.content == "/help_voting"):
            if(question == ""):
                await message.channel.send("There is no poll available.") 
                return 

            await message.channel.send('''to vote: /voting NUMBER ID (where NUMBER is the choice and ID the PublicID)\n
                Question: ''' + question + '''
                1 = ''' + one_answer + '''
                2 = ''' + two_answer + '''
                3 = ''' + three_answer + '''
                4 = ''' + four_answer + '''
                5 = ''' + five_answer )
            return
        
        if(message.content == "/voting_result"):
            if(question == ""):
                await message.channel.send("There is no poll available.") 
                return  

            await show_result(message)  
            return         

        if message.content.startswith("/voting"):
            if(question == ""):
                await message.channel.send("There is no poll available.") 
                return  

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

            await message.channel.send("You voted for " + choice + "\n")       

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
