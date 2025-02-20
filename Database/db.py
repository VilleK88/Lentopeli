import mysql.connector
from Routes.config import db_config

def connect_db():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"Virhe yrittäessä yhdistää tietokantaan: {err}")
        return None

def get_airport_coords(icao):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        sql = "select name, ident, latitude_deg, longitude_deg from airport where ident = %s"
        cursor.execute(sql, (icao,))
        result = cursor.fetchone()
        conn.close()
        return (result[0], result[1], result[2], result[3]) if result else None
    return False

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