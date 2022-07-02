from discord import Client, User


def is_valid_user(username_id: str):
    if username_id.isdigit() == False:
        return (False, "Username ID should only consist of numbers")
        
    return (True,"")

async def is_existing_user(client:Client, user_id:str):
    try:
        user:User = await client.fetch_user(user_id)
    except:
        return (False, "")

    return (True, user.display_name)
