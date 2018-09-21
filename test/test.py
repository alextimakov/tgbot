import src.dbhelper as db_hp
import time
import calendar
from multiprocessing import Process
# import json
# from src.scripts import *
# from telegram.utils import request
# import src.config as config

FLAG = True


def main():
    while FLAG:
        time.sleep(1)
        auth = db_hp.SQLighter('db.sqlite')
        current_time = calendar.timegm(time.gmtime())
        user = auth.fetch_user_id_news()
        user_f = [user for user in user if len(str(user[0])) > 5]
        user_list = [user[0] for user in user_f]
        if user_list:
            print(auth.check_time(user_list[0])[-1][0])
            rem_check = [user for user in user_list]
            print(rem_check)
            if rem_check:
                for i in range(len(rem_check)):
                    print(rem_check[i])
            else:
                pass
        else:
            pass
    pass


if __name__ == '__main__':
    p = Process(target=main, args=())
    p.start()
