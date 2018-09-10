import src.dbhelper as db

sqlite_file = 'db.sqlite'
table_name_1 = 'user_boss'
new_column = 'user'
column_type = 'TEXT'

user_db = db.SQLighter(sqlite_file)
user_db.cursor.execute('CREATE TABLE {tn} ({nf} {ft})'.format(tn=table_name_1, nf=new_column, ft=column_type))

user_db.commit()
user_db.close()
