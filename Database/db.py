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
        # result = cursor.fetchall()
        conn.close()
        return (result[0], result[1], result[2], result[3]) if result else None
        # return result if result else None
    return None

# Tarkistaa löytyykö lisättyjä sarakkeita ja taulukkoa tietokannasta ja jos ei löydy niin lisää ne
def get_columns_and_tables():

    result = get_info_from_db("select column_name from information_schema.columns where table_name = 'game' and column_name = 'logged_in'")
    if not result:
        print("Saraketta 'logged_in' ei löydy, luodaan se....")
        commit_to_db("alter table game add column logged_in boolean default false")
    else:
        print("Sarake 'logged_in' on jo olemassa.")

    result = get_info_from_db("select column_name from information_schema.columns where table_name = 'game' and column_name = 'current_fuel'")
    if not result:
        print("Saraketta 'current_fuel' ei löydy, luodaan se....")
        commit_to_db("alter table game add column current_fuel float default 25941")
    else:
        print("Sarake 'current_fuel' on jo olemassa.")

    result = get_info_from_db("select column_name from information_schema.columns where table_name = 'game' and column_name = 'current_icao'")
    if not result:
        print("Saraketta 'current_icao' ei löydy, luodaan se....")
        commit_to_db("alter table game add column current_icao text default 'EFHK'")
    else:
        print("Sarake 'current_icao' on jo olemassa.")

    result = get_info_from_db("select table_name from information_schema.tables where table_name = 'inventory'")
    if not result:
        print("Taulukkoa 'inventory' ei löydy, luodaan se....")
        commit_to_db("""create table if not exists inventory (
inventory_id varchar(40) character set latin1 collate latin1_swedish_ci not null primary key,
current_fuel float default 48900, alcohol int default 0,
constraint fk_inventory foreign key(inventory_id) references game(id) on delete cascade)
ENGINE=InnoDB default charset=latin1 collate=latin1_swedish_ci""")
        commit_to_db("""CREATE TRIGGER after_game_insert AFTER INSERT ON game FOR EACH ROW
INSERT INTO inventory (inventory_id, current_fuel, alcohol)
VALUES (NEW.id, 48900, 0);""")
    else:
        print("Taulukko 'inventory' on jo olemassa.")

# Tarkistaa onko sarake tai taulu jo olemassa
def get_info_from_db(sql):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchone()
        conn.close()
        return result if result else None

# Committaa uuden sarakkeen tai taulukon tietokantaan
def commit_to_db(sql):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        conn.close()

# Tarkistaa onko kukaan käyttäjä kirjautuneena sisään ja hakee tiedot
# tietokannasta game-taulukosta
def get_logged_in_user_data():
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        sql = "select id, screen_name, current_fuel, current_icao from game where logged_in = 1"
        cursor.execute(sql)
        result = cursor.fetchone()
        conn.close()
        return (result[0], result[1], result[2], result[3]) if result else None

def get_inventory(user_id):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        sql = "select current_fuel from inventory where inventory_id = %s"
        cursor.execute(sql, (user_id,))
        result = cursor.fetchone()
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

# Hakee käyttäjän tiedot tietokannasta ja muuttaa haetun käyttäjän
# tilan logged_in = 1 ja nollaa muut käyttäjät logged_in = 0
def get_users_and_set_as_logged_in(name):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        sql = "select id, screen_name, current_fuel from game where screen_name = %s"
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

# Tarkistaa onko nimi jo tietokannassa
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

# Lisää käyttäjän tietokantaan
def add_user_to_db(name, fuel):
    conn = connect_db()
    if conn:
        random_id = str(uuid.uuid4())
        cursor = conn.cursor()
        sql = "insert into game (id, screen_name, current_fuel) values (%s, %s, %s)"
        cursor.execute(sql, (random_id, name, fuel))
        conn.commit()
        conn.close()

# Tallentaa pelin edistymisen
def save_game_progress(user_id, fuel, icao):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        sql_game = "update game set current_fuel = %s, current_icao = %s where id = %s"
        cursor.execute(sql_game, (fuel, icao, user_id))
        conn.commit()
        sql_inventory= "update inventory set current_fuel = %s where inventory_id = %s"
        cursor.execute(sql_inventory, (fuel, user_id))
        conn.commit()
        conn.close()