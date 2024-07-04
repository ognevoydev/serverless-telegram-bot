from enum import Enum


class Stage(Enum):
    """
    Stage of request processing enum.
    """
    PROCESS = 'P'
    SUCCESS = 'S'
    FAILED = 'F'


class State(Enum):
    """
    State of conversation handler enum.
    """
    PHONE = 'phone'
    SIGN_UP = 'signup'
    UPLOAD = 'upload'
    ANALYSIS = 'analysis'
    RECOMMENDATION = 'recommendation'
    TRANSCRIPTION = 'transcription'
    BACK_TO_LIST = 'back_to_list'


class Emoji(Enum):
    """
    Emoji enum.
    """
    CHECK = '\U00002705'
    WAIT = '\U0001F551'
