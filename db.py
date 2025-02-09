import mysql.connector
from config import db_config
def connect_db():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"Virhe yrittäessä yhdistää tietokantaan: {err}")
        return None