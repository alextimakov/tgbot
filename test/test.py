import src.dbhelper as db_hp
from src.scripts import *


def main():
    auth = db_hp.SQLighter('db.sqlite')
    boss_uid = auth.select_boss_id(125500294)
    number_answers = auth.count_news(boss_uid)
    for i in reversed(range(number_answers)):
        while i > 0:
            print(auth.check_news(boss_uid)[-i:])
            i -= 1
    print(3)


# if auth.check_news(boss_uid)[-i:]:
#     print(answer_pos['RU'])
#     print(''.join(auth.check_news(boss_uid)[-i:]))
# else:
#     print(answer_neg['RU'])

if __name__ == '__main__':
    main()
