import sqlite3


class SQLighter:
    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    def add_column(self, cname, dtype):
        with self.connection:
            return self.cursor.execute('ALTER TABLE user_boss ADD :column_name :datatype',
                                       {"column_name": cname, "datatype": dtype})

    def update_user(self, value, cond):
        with self.connection:
            self.cursor.execute('UPDATE user_boss SET user_id = :value WHERE user = :cond',
                                {"value": value, "cond": cond})
            self.connection.commit()

    def update_boss(self, value, cond):
        with self.connection:
            self.cursor.execute('UPDATE user_boss SET boss_id = :value WHERE boss = :cond',
                                {"value": value, "cond": cond})
            self.connection.commit()

    def update_news_start(self, values):
        with self.connection:
            self.cursor.execute('INSERT INTO news_base (id, status, user_id, boss_id) VALUES (?,?,?,?)', values)
            self.connection.commit()

    def update_news_attach(self, attach, key):
        with self.connection:
            self.cursor.execute('UPDATE news_base SET file_id  = ? WHERE id = ?', (attach, key))
            self.connection.commit()

    def update_news_text(self, time, text, key):
        with self.connection:
            self.cursor.execute('UPDATE news_base SET time = ?, news_text = ? WHERE id = ?', (time, text, key))
            self.connection.commit()

    def select_all(self):
        with self.connection:
            return self.cursor.execute('SELECT * FROM user_boss').fetchall()

    def select_user(self):
        with self.connection:
            return self.cursor.execute('SELECT user FROM user_boss').fetchall()

    def select_user_id(self, boss):
        with self.connection:
            return self.cursor.execute('SELECT user_id FROM user_boss WHERE boss_id = :boss', {"boss": boss}).fetchone()

    def select_boss(self):
        with self.connection:
            return self.cursor.execute('SELECT boss FROM user_boss').fetchall()

    def select_boss_id(self, user):
        with self.connection:
            return self.cursor.execute('SELECT boss_id FROM user_boss WHERE user_id = :user', {"user": user}).fetchone()

    def select_column(self, cname):
        with self.connection:
            return self.cursor.execute('SELECT :column_name FROM user_boss', {"column_name": cname}).fetchall()

    def select_person(self, cond):
        with self.connection:
            return self.cursor.execute('SELECT * FROM user_boss WHERE user = :condition or boss = :condition',
                                       {"condition": cond}).fetchone()

    def count_rows(self):
        with self.connection:
            result = self.cursor.execute('SELECT * FROM user_boss').fetchall()
            return len(result)

    def count_news(self, boss_id):
        with self.connection:
            result = self.cursor.execute('SELECT * FROM news_base WHERE boss_id = ? and status = 0', boss_id).fetchall()
            return len(result)

    def check_news(self, boss_id):
        with self.connection:
            return self.cursor.execute('SELECT news_text FROM news_base WHERE boss_id = ?', boss_id).fetchall()

    def close(self):
        self.connection.close()
