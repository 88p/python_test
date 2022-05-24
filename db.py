import sqlite3


#https://qiita.com/saira/items/e08c8849cea6c3b5eb0c

class DataBase:
    def create_table(self, connect_obj):
        cur = connect_obj.cursor()
        cur.execute(
            'CREATE TABLE persons(id INTEGER PRIMARY KEY AUTOINCREMENT,name STRING)')
        conn.commit()
        database.close_cur(cur)
        
    def connect_database(self, dbname):
        return sqlite3.connect(dbname)
    
    def operation_database(self, connect_obj):
        cur = connect_obj.cursor()
        cur.execute('INSERT INTO persons(name) values("TARO")')
        cur.execute('INSERT INTO persons(name) values("Hanako")')
        cur.execute('INSERT INTO persons(name) values("Hiroki")')
        database.close_cur(cur)
        
    def close_cur(self, cursor):
        cursor.close()
        
    def confirmData(self, connect_obj):
        cur = connect_obj.cursor()
        cur.execute('SELECT * FROM persons')
        print(cur.fetchall())
        database.close_cur(cur)

#START
dbname = 'database.db'
database = DataBase()

conn = database.connect_database(dbname)
database.operation_database(conn)
database.confirmData(conn)


#commitすることで変更を反映する
print("end")

conn.close()


