import src.dbhelper as db_hp
import calendar
import time
import shelve

def main():
    auth = db_hp.SQLighter('db.sqlite')
    db = shelve.open("file2.txt")
    db['user'] = ['ru', 'rn', 'ua']


if __name__ == '__main__':
    main()

