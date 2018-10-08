import sqlite3


class SQLighter:
    def __init__(self, database):
        self.con = sqlite3.connect(database)
        self.c = self.con.cursor()

    def insert_news_start(self, unique_id, status, user_id, boss_id):
        with self.con:
            self.c.execute('INSERT INTO news_base (id, status, user_id, boss_id) VALUES (?,?,?,?)',
                           (unique_id, status, user_id, boss_id))
            self.con.commit()

    def insert_lost_news(self, unique_id, time, user_id, news_text, file_id):
        with self.con:
            self.c.execute('INSERT INTO lost_news (id, time, user_id, news_text, file_id) VALUES (?,?,?,?,?)',
                           (unique_id, time, user_id, news_text, file_id, ))
            self.con.commit()

    def update_cond(self, table, col, col_val, cond, cond_val):
        with self.con:
            self.c.execute('UPDATE %s SET %s = ? WHERE %s = ?' % (table, col, cond), (col_val, cond_val, ))
            self.con.commit()

    def select_cond(self, col, table, cond, cond_val):
        with self.con:
            result = self.c.execute('SELECT %s FROM %s WHERE %s = ?' % (col, table, cond, ), (cond_val,)).fetchall()
            return result

    def select_no_cond(self, col, table):
        with self.con:
            result = self.c.execute('SELECT %s FROM %s' % (col, table, )).fetchall()
            return result

    def select_person(self, cond):
        with self.con:
            return self.c.execute('SELECT * FROM user_boss WHERE user = ? OR boss = ?', (cond, cond, )).fetchone()

    def select_answer_time(self, boss_id):
        with self.con:
            return self.c.execute('SELECT answer_time FROM news_base WHERE boss_id = ? '
                                  'AND NOT answer_time IS NULL', (boss_id, )).fetchall()

    def check_news(self, boss_id):
        with self.con:
            return self.c.execute('SELECT news_text FROM news_base WHERE boss_id = ? AND status = 0 AND answer IS NULL '
                                  'AND news_text IS NOT NULL', (boss_id, )).fetchall()

    def close(self):
        self.con.close()
