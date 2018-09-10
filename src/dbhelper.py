import sqlite3


class SQLighter:
    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    def add_column(self):
        with self.connection:
            # ДОПИСАТЬ!
            return self.cursor.execute('ALTER ')

    def select_all(self):
        with self.connection:
            return self.cursor.execute('SELECT * FROM user_boss').fetchall()

    def select_single(self, row_num):
        with self.connection:
            return self.cursor.execute('SELECT * FROM user_boss WHERE id = ?', (row_num,)).fetchall()[0]

    def count_rows(self):
        with self.connection:
            result = self.cursor.execute('SELECT * FROM user_boss').fetchall()
            return len(result)

    def close(self):
        self.connection.close()
