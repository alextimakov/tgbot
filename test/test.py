# import concurrent.futures
# from multiprocessing import Pool
from src.bot import *


def enter():
    auth = db_hp.SQLighter('db.sqlite')
    print(dp.job_queue)


if __name__ == '__main__':
    bot = updater.bot
    enter()

# import sched
# import calendar
# import time
# current_time = calendar.timegm(time.gmtime())
# context = 125500294
#
# s = sched.scheduler(time.time, time.sleep)
#
#
# def run_periodically(start_time, end_time, interval, func, args=()):
#     event_time = start_time
#     while event_time < end_time:
#         s.enter(interval, 1, func, args)
#         logger.info("Новое событие создано")
#         event_time += interval
#
#     s.run()
