from Database.db import connect_db

user_name = ""
user_id = ""
logged_in = ""

def check_if_logged_in_exists():
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        sql = "select column_name from information_schema.columns where table_name = 'game' and column_name = 'logged_in'"
        cursor.execute(sql)
        result = cursor.fetchone()
        if not result:
            print("Saraketta 'logged_in' ei löydy, luodaan se....")
            sql = "alter table game add column logged_in boolean default false"
            cursor.execute(sql)
            conn.commit()
            conn.close()
        else:
            print("Sarake 'logged_in' on jo olemassa.")