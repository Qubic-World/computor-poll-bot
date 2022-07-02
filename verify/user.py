
def is_valid_user(username_id: str):
    if username_id.isdigit() == False:
        return (False, "Username ID should only consist of numbers")
        
    return (True,"")