import json
from algorithms.verify import *


def is_valid_message(message):
    try:
        json_message_array = json.loads(message)
    except Exception as e:
        return (False, "Unvalid json")

    for json_message in json_message_array:
        try:
            identity: str = json_message["identity"]
            identity = "".join([i for i in identity if i.isalpha()])
            if len(identity) != 70:
                return (False, "The identity length must be 70 ")
        except:
            return (False, "No `identity` field")

        try:
            username:str = json_message["username"]
            if len(username) <= 0:
                return (False, "The `username` field cannot be empty")
        except:
            return (False, "No `username` field")

        try:
            signature: str = json_message['signature']
            signature = "".join([s for s in signature if s.isalpha()])
            if len(signature) != 128:
                return (False, "The signature length must be 128")
        except:
            return (False, "No `signature` field")

        # Verify
        public_key = get_public_key_from_id(identity)
        digest = kangaroo_twelve(username.encode('ascii'))
        if verify(public_key,digest, str_signature_to_bytes(signature)) == False:
            return (False, "Message failed to be verified")

    return (True, "Good!")
