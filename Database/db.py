import mysql.connector
from Routes.config import db_config
import uuid

# Yhdistää tietokantaan
def connect_db():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"Virhe yrittäessä yhdistää tietokantaan: {err}")
        return None

# Palauttaa lentokenttien koordinaatit
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

# Tarkistaa onko logged_in sarake olemassa game -taulukossa ja jos ei ole niin tekee sen
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
            sql = "alter table game add column current_fuel float default 25941"
            cursor.execute(sql)
            conn.commit()
            conn.close()
        else:
            print("Sarake 'logged_in' on jo olemassa.")

# Tarkistaa onko kukaan käyttäjä kirjautuneena sisään
def check_if_logged_in():
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        sql = "select id, screen_name from game where logged_in = 1"
        cursor.execute(sql)
        result = cursor.fetchone()
        conn.close()
        return result if result else None

# Palauttaa käyttäjä listan
def show_current_users():
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        sql = "select id, screen_name from game"
        cursor.execute(sql)
        result = cursor.fetchall()
        conn.close()
        return result if result else None

def get_user_info(name):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        sql = "select id, screen_name from game where screen_name = %s"
        cursor.execute(sql, (name,))
        result = cursor.fetchone()

        if result:
            sql = "update game set logged_in = 0"
            cursor.execute(sql)
            conn.commit()
            sql = "update game set logged_in = 1 where screen_name = %s"
            cursor.execute(sql, (name,))
            conn.commit()
            conn.close()
            return result[0], result[1]
def check_if_name_in_db(name):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        sql = "select screen_name from game where screen_name = %s"
        cursor.execute(sql, (name,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return True
        else:
            return False

def add_user_to_db(name, fuel):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        sql = "insert into game (screen_name, current_fuel) values (%s, %s)"
        cursor.execute(sql, (name, fuel))
        conn.commit()
        conn.close()