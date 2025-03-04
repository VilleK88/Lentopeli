import mysql.connector
import json
import random
from Routes.config import db_config
from Database.db import connect_db

current_customer = ""
customer_mood = 5
cash = ""
reputation = 50

# Yhdistetään MariaDB-tietokantaan
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# Palauttaa lentokenttien koordinaatit
def get_airport_info(icao):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        sql = "SELECT name, ident, type FROM airport WHERE type = 'large_airport' AND ident = %s"
        cursor.execute(sql, (icao,))
        result = cursor.fetchall()
        conn.close()
        return result if result else None
    return None

# Suljetaan tietokantayhteys
cursor.close()
conn.close()

# Tarkistetaan, että listassa on lentoasemia
if not icao_list:
    print("Ei löydetty sopivia lentokenttiä.")
    exit()

# Ladataan asiakkaat JSON-tiedostosta
with open("customersdb.json", "r", encoding="utf-8") as file:
    customers = json.load(file)

# Valitaan satunnainen asiakas
selected_customer = random.choice(customers)
customer_name = selected_customer["name"]

# Pyydetään pelaajalta nykyinen ICAO-koodi
current_icao = input("Syötä nykyinen lentokentän ICAO-koodi: ").strip().upper()

# Poistetaan nykyinen ICAO mahdollisista kohteista
icao_list = [icao for icao in icao_list if icao != current_icao]

# Valitaan satunnainen määränpää
if icao_list:
    destination_icao = random.choice(icao_list)
    print(f"Asiakas {customer_name} nousi koneeseen ja haluaa lentää kentälle {destination_icao}.")
else:
    print("Ei saatavilla olevia lentokohteita.")

# Asiakkaat ennen lennon aloittamista
def customers_start():
    global current_customer
    # muista palauttaa myös ICAO-koodi, jotta tiedetään mille lentokentälle pitää lentää
    return current_customer # ja ICAO

# Asiakkaat lennon aikana. Ottaa vastaan tuulen nopeuden. 16 m/s ja yli tarkoittaa turbulenssia
def customers_flight(wind_speed):
    global current_customer, customer_mood

# Lennon loppu ottaa vastaan lentokentän ICAO-koodin, jolla sillä hetkellä ollaan
def customer_flight_end(icao):
    global current_customer, customer_mood, cash, reputation
    # tarkistetaan onko lennetty oikealle lentokentälle ICAO-koodin perusteella ja jos on
    # niin palauttaa rahaa ja mainetta. Tyhjennetään current_customer = "" muuttuja.
    return cash and reputation