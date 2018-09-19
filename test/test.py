import src.dbhelper as db_hp
import src.shelve as shelve


def main():
    user = 125500294
    auth = db_hp.SQLighter('db.sqlite')
    shelve.set_state(str(user), shelve.States.MENU.value)
    print()


if __name__ == '__main__':
    main()

