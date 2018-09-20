from vedis import Vedis
from enum import Enum

db_name = 'db.vdb'
lost_name = 'lost.vdb'


def get_current_state(db, user_id):
    with Vedis(db) as d:
        try:
            return d[user_id]
        except KeyError:
            return States.START.value


def set_state(db, user_id, value):
    with Vedis(db) as d:
        try:
            d[user_id] = value
            return True
        except KeyError:
            return False


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
