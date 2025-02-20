from Database.db import connect_db

user_name = ""
user_id = ""
logged_in = ""

def check_if_logged_in():
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        sql = "select id, screen_name from game where logged_in = 1"