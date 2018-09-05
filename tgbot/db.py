import pandas as pd


def setup(file):
    db = pd.read_csv(file)
    return db


def check_user_uid(user, db):
    if user in db['user_uid'].values:
        return 1
    else:
        return None


def check_user(user, db):
    if user in db['user'].values:
        i = db.loc[db['user'].values == user]['boss']
        return i
    else:
        return None


def add_user(db, user, boss, user_uid, boss_uid):
    d = [[user, boss, user_uid, boss_uid]]
    labels = list(db)
    df2 = pd.DataFrame(data=d, columns=labels)
    db = db.append(df2, ignore_index=True)
    db.to_csv('db1.csv', index=False)
    print("Сотрудник добавлен!")


def add_attach(db, file_id, user_id):
    d = [[file_id, user_id]]
    labels = list(db)
    df2 = pd.DataFrame(data=d, columns=labels)
    db = db.append(df2, ignore_index=True)
    db.to_csv('db3.csv', index=False)
    print("Приложение добавлено!")


def add_news(db, text, time, status, user_id, boss_id):
    d = [[text, time, status, user_id, boss_id]]
    labels = list(db)
    df2 = pd.DataFrame(data=d, columns=labels)
    db = db.append(df2, ignore_index=True)
    db.to_csv('db2.csv', index=False)
    print("Новость добавлена!")


def get_boss_id(user, db):
    return int(db.loc[db['user_uid'] == user]['boss_uid'])
