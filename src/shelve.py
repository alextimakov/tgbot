import shelve
from enum import Enum

shelve_name = 'shelve.db'


class States(Enum):
    START = "0"
    MENU = "1"
    SET_STATE = "2"
    LOGIN = "3"
    CHECK = "4"
    NEWS = "5"
    ATTACH = "6"
    NO_ATTACH = "7"
    SENT = "8"
    ANSWER = "9"
    RESULT = "10"
    WHERE = "11"
    ANSWER_MOD = "12"
    ANSWER_USER = "13"


def get_current_state(user_id):
    with shelve.open(shelve_name, writeback=True) as storage:
        try:
            return storage[user_id]
        except KeyError:
            return States.START.value


# Сохраняем текущее «состояние» пользователя в нашу базу
def set_state(user_id, value):
    with shelve.open(shelve_name, writeback=True) as storage:
        try:
            storage[user_id] = value
            return True
        except KeyError:
            return False
