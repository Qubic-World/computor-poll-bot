import logging
import re

from algorithms.verify import *

IDENTITY_FIELD = "identity"
MESSAGE_FIELD = "message"
SIGNATURE_FIELD = "signature"
IVALID_IDENTITY = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACDFMDM"
SIGNATURE_STR_LEN = (64 * 2) + 2  # +2 - checksum
CHECKSUM_INDEX = 64
CONST_MESSAGE = r"For ComputorPollBot from "
CONST_MESSAGE_RE = re.compile(CONST_MESSAGE)
USERNAME_RE = re.compile(CONST_MESSAGE + r"(.+#\d{4})")


def is_valid_identity(identity: str):
    return identity.isalpha() and len(identity) == 70 and identity != IVALID_IDENTITY


def is_valid_json(json_message: dict):
    """Identity field
    """
    try:
        identity: str = json_message[IDENTITY_FIELD]
        if not is_valid_identity(identity):
            return (False, "The identity length must be 70 ")
    except:
        return (False, "No `identity` field")

    """Message field
    """
    try:
        message: str = json_message[MESSAGE_FIELD]
        if len(message) <= 0:
            return (False, "The `message` field cannot be empty")
    except:
        return (False, "No `message` field")

    if CONST_MESSAGE_RE.match(message) == None:
        return (False, f"The message must begin with: {CONST_MESSAGE}")

    """Signature field
    """
    try:
        signature_str: str = json_message[SIGNATURE_FIELD]
        signature_str = "".join([s for s in signature_str if s.isalpha()])
        if len(signature_str) != SIGNATURE_STR_LEN:
            return (False, f"The signature length must be {SIGNATURE_STR_LEN}")
    except:
        return (False, "No `signature` field")

    """ Verify
    """
    # Checking checksum
    signature = str_signature_to_bytes(signature_str)
    signature_without_checksum = signature[:CHECKSUM_INDEX]
    checksum = kangaroo_twelve(signature_without_checksum)[0]
    if checksum != signature[CHECKSUM_INDEX]:
        return (False, "Invalid checksum")

    public_key = get_public_key_from_id(identity)
    if verify_message(public_key, message.encode('utf-8'), signature_without_checksum) == False:
        return (False, "Message failed to be verified")

    return (True, "Good!")


def get_identity_list_from_json(json_data: dict) -> list:
    identity_list = []
    try:
        identity_list.append(json_data[IDENTITY_FIELD])
    except Exception as e:
        return (False, "Unvalid json")

    return identity_list


def get_username_from_json(json_data: dict) -> str:
    try:
        message_value = json_data[MESSAGE_FIELD]
        m = USERNAME_RE.match(message_value)
        if m != None:
            g = m.groups()
            if g != None:
                return g[0]

    except Exception as e:
        logging.exception(e)
        return ""

    return ""
