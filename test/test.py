# import concurrent.futures
from src.bot import *
# from multiprocessing import Process, Queue
# import time


def main():
    auth = db_hp.SQLighter('db.sqlite')
    answer_text = auth.check_news(203411538)[-1 * 0]
    if auth.fetch_file_id(text=answer_text[0])[0] != 0:
        print(1)
    else:
        print(2)


if __name__ == "__main__":
    main()

