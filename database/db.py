import mysql.connector
from routes.config import db_config
import uuid

# Yhdistää MySQL-tietokantaan käyttäen asetustiedoston konfiguraatiota
def connect_db():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"Virhe yrittäessä yhdistää tietokantaan: {err}")
        return None

# Hakee tietokannasta lentokentän koordinaatit ICAO-koodin perusteella
def get_airport_coords(icao):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        sql = "select name, ident, latitude_deg, longitude_deg from airport where ident = %s"
        cursor.execute(sql, (icao,))
        result = cursor.fetchone()
        conn.close()
        return (result[0], result[1], result[2], result[3]) if result else None
    return None

# Tarkistaa ja luo tarvittavat tietokantataulut ja sarakkeet, jos niitä ei ole olemassa
def get_columns_and_tables():

    result = get_info_from_db("select column_name from information_schema.columns where table_name = 'game' and column_name = 'logged_in'")
    if not result:
        commit_to_db("alter table game add column logged_in boolean default false")

    result = get_info_from_db("select column_name from information_schema.columns where table_name = 'game' and column_name = 'current_fuel'")
    if not result:
        commit_to_db("alter table game add column current_fuel float default 25941")

    result = get_info_from_db("select column_name from information_schema.columns where table_name = 'game' and column_name = 'reputation'")
    if not result:
        commit_to_db("alter table game add column reputation int default 10")

    result = get_info_from_db("select column_name from information_schema.columns where table_name = 'game' and column_name = 'current_icao'")
    if not result:
        commit_to_db("alter table game add column current_icao text default 'EFHK'")

    result = get_info_from_db("select table_name from information_schema.tables where table_name = 'inventory'")
    if not result:
        commit_to_db("""create table if not exists inventory (
            inventory_id varchar(40) character set latin1 collate latin1_swedish_ci not null primary key,
            cash float default 100,
            current_fuel float default 48900,
            fruits int default 0,
            alcohol  int default 0,
            snacks int default 0,
            soda int default 0,
            meals int default 0,
            water int default 0,
            constraint fk_inventory foreign key(inventory_id) references game(id) on delete cascade
        ) ENGINE=InnoDB default charset=latin1 collate=latin1_swedish_ci""")
        commit_to_db("""CREATE TRIGGER after_game_insert AFTER INSERT ON game FOR EACH ROW
        INSERT INTO inventory (inventory_id, cash, current_fuel, fruits, alcohol , snacks, soda, meals, water)
        VALUES (NEW.id, 100, 48900, 0, 0, 0, 0, 0, 0);""")

# Suorittaa SQL-kyselyn ja palauttaa tuloksen
def get_info_from_db(sql):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchone()
        conn.close()
        return result if result else None

# Suorittaa SQL-komennon, joka muuttaa tietokantaa
def commit_to_db(sql):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        conn.close()

# Hakee kirjautuneen käyttäjän tiedot tietokannasta
def get_logged_in_user_data():
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        sql = "select id, screen_name, current_icao, reputation from game where logged_in = 1"
        cursor.execute(sql)
        result = cursor.fetchone()
        conn.close()
        return (result[0], result[1], result[2], result[3]) if result else None

# Hakee käyttäjän polttoaineen ja käteisen inventaariosta
def get_inventory(user_id):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        sql = "select current_fuel, cash from inventory where inventory_id = %s"
        cursor.execute(sql, (user_id,))
        result = cursor.fetchone()
        return (result[0],result[1]) if result else None

# Palauttaa listan kaikista käyttäjistä tietokannasta
def show_current_users():
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        sql = "select id, screen_name from game"
        cursor.execute(sql)
        result = cursor.fetchall()
        conn.close()
        return result if result else None

# Kirjaa käyttäjän sisään ja asettaa kaikki muut käyttäjät tilaan logged_in = 0
def get_users_and_set_as_logged_in(name):
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

# Lisää uuden käyttäjän tietokantaan
def add_user_to_db(name):
    conn = connect_db()
    if conn:
        random_id = str(uuid.uuid4())
        cursor = conn.cursor()
        sql = "insert into game (id, screen_name) values (%s, %s)"
        cursor.execute(sql, (random_id, name))
        conn.commit()
        conn.close()

# Tallentaa käyttäjän pelin edistymisen tietokantaan
def save_game_progress(user_id, fuel, icao, logging_out):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        sql_game = "update game set current_icao = %s where id = %s"
        cursor.execute(sql_game, (icao, user_id))
        conn.commit()
        sql_inventory= "update inventory set current_fuel = %s where inventory_id = %s"
        cursor.execute(sql_inventory, (fuel, user_id))
        conn.commit()
        if logging_out:
            log_out()
        conn.close()

# Kirjaa käyttäjän ulos ja asettaa logged_in-arvon 0:ksi kaikille käyttäjille
def log_out():
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        sql = "update game set logged_in = 0"
        cursor.execute(sql)
        conn.commit()
        conn.close()