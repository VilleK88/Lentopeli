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
        conn.close()
        return result if result else None