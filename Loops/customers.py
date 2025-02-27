import mysql.connector
import json
import random
from Routes.config import db_config

# Yhdistetään MariaDB-tietokantaan
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# Haetaan vain suuret ja avoimet lentokentät
cursor.execute("select name, ident, type from airport where type = 'large_airport'")
icao_list = [row[0] for row in cursor.fetchall()]

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
