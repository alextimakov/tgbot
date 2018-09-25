import src.dbhelper as db_hp
import time
import calendar
# from multiprocessing import Process
# import json
# from src.scripts import *
# from telegram.utils import request
# import src.config as config

FLAG = True


def main():
    while FLAG:
        time.sleep(10)
        auth = db_hp.SQLighter('db.sqlite')
        current_time = calendar.timegm(time.gmtime())
        user = auth.fetch_user_id_news()
        user_f = [user for user in user if len(str(user[0])) > 5]
        user_list = list(set([user[0] for user in user_f]))
        if user_list:
            print(user_list)
            rem_check = [user for user in user_list if auth.check_time(user)[-1][0] is not None
                         and (current_time - auth.check_time(user)[-1][0]) > (60*60*24*8)]
            if rem_check:
                print(rem_check)
                for i in range(len(rem_check)):
                    print(rem_check[i])
            else:
                print("Все новости написаны недавно")
                pass
        else:
            print("В базе нет пользователей!")
            pass
    pass


if __name__ == '__main__':
    # p = Process(target=main, args=())
    # p.start()
    main()
