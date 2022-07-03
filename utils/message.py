import json
import logging

from algorithms.verify import *

from verify.user import is_valid_user

IDENTITY_FIELD = "identity"
USERID_FIELD = "username_id"
SIGNATURE_FIELD = "signature"
IVALID_IDENTITY = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACDFMDM"

def is_valid_identity(identity: str):
    return identity.isalpha() and len(identity) == 70 and identity != IVALID_IDENTITY


def is_valid_message(message):
    try:
        json_message_array = json.loads(message)
    except Exception as e:
        return (False, "Unvalid json")

    for json_message in json_message_array:
        try:
            identity: str = json_message[IDENTITY_FIELD]
            if not is_valid_identity(identity):
                return (False, "The identity length must be 70 ")
        except:
            return (False, "No `identity` field")

        try:
            username_id:str = json_message[USERID_FIELD]
            if len(username_id) <= 0:
                return (False, "The `username_id` field cannot be empty")
            
            valid_user_result = is_valid_user(username_id)
            if valid_user_result[0] == False:
                return (False, valid_user_result[1])
        except:
            return (False, "No `username_id` field")

        try:
            signature: str = json_message[SIGNATURE_FIELD]
            signature = "".join([s for s in signature if s.isalpha()])
            if len(signature) != 128:
                return (False, "The signature length must be 128")
        except:
            return (False, "No `signature` field")

        # Verify
        public_key = get_public_key_from_id(identity)
        digest = kangaroo_twelve(username_id.encode('ascii'))
        if verify(public_key,digest, str_signature_to_bytes(signature)) == False:
            return (False, "Message failed to be verified")

    return (True, "Good!")

def get_identity_list(message: str)->list:
    identity_list = []
    try:
        json_array = json.loads(message)
    except Exception as e:
        return (False, "Unvalid json")

    for json_obj in json_array:
        identity_list.append(json_obj[IDENTITY_FIELD])

    return identity_list



def get_user_id_from_message(message: str)->str:
    try:
        json_obj = json.loads(message)[0]
        return json_obj[USERID_FIELD]
    except Exception as e:
        logging.exception(e)
        return ""
