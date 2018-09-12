# import concurrent.futures
from src.bot import *
from multiprocessing import Process, Queue
import time


def main():
    auth = db_hp.SQLighter('db.sqlite')
    for i in range(auth.count_rows()):
        user = auth.fetch_id()
        print(auth.check_time(user[0][0]))


if __name__ == "__main__":
    main()
    updater.start_polling(clean=True)

