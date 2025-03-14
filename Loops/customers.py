import os
import json
import random
import mysql.connector
from Routes.config import db_config
from Database.db import connect_db

# 🔹 Globaalit muuttujat (Global variables)
current_customer = None  # Nykyinen asiakas
customer_mood = 5        # Asiakkaan mieliala (1-10)
cash = 500               # Pelaajan käteinen raha
reputation = 50          # Pelaajan maine
inventory = {}           # Pelaajan varasto (aloitustilanne)

# 🔹 Lataa asiakkaat JSON-tiedostosta
def load_customers():
    file_path = os.path.join(os.path.dirname(__file__), "../Database/customersdb.json")
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            customers = json.load(file)
            print(f"Ladattu {len(customers)} asiakasta.")  # Tarkistus
            return customers  # Palauttaa listan asiakkaista
    except FileNotFoundError:
        print(f"Virhe: Tiedostoa ei löydy: {file_path}")
        return []
    except json.JSONDecodeError:
        print("Virhe: customersdb.json ei ole validi JSON-tiedosto!")
        return []

# 🔹 Lataa ICAO-koodit tietokannasta
def load_airports():
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT ident FROM airport WHERE type = 'large_airport'")
        icao_list = [row[0] for row in cursor.fetchall()]
        return icao_list
    except mysql.connector.Error as e:
        print(f"Virhe tietokantayhteydessä: {e}")
        return []
    finally:
        if conn:
            conn.close()

# 🔹 Hakee lentokentän tiedot ICAO-koodin perusteella
def get_airport_info(icao):
    conn = connect_db()
    if not conn:
        return None
    cursor = conn.cursor()
    cursor.execute("SELECT name, ident, type FROM airport WHERE type = 'large_airport' AND ident = %s", (icao,))
    result = cursor.fetchall()
    conn.close()
    return result if result else None

# 🔹 Valitsee satunnaisen asiakkaan ja määränpään
def load_and_select_customer(current_icao, screen, font):
    global current_customer

    customers = load_customers()
    if not customers:
        return None, None

    icao_list = load_airports()
    if not icao_list:
        return None, None

    # Valitaan satunnainen asiakas
    current_customer = random.choice(customers)

    # Valitaan määränpää, joka ei ole nykyinen kenttä
    destination_icao = random.choice([icao for icao in icao_list if icao != current_icao])

    # Tallennetaan määränpää asiakkaan tietoihin, jotta sitä voidaan myöhemmin vertailla
    current_customer["destination"] = destination_icao

    # Tulostetaan asiakas ja määräpaikka
    print(f"Valittu asiakas: {current_customer['name']}")
    print(f"Määränpää ICAO-koodi: {destination_icao}")

    # Haetaan ICAO-koodin tiedot lentokentältä
    airport_info = get_airport_info(destination_icao)
    if airport_info:
        print(f"Lentokentän nimi: {airport_info[0][0]}")  # Lentokentän nimi

    return current_customer, destination_icao

# 🔹 Tarkistaa pelaajan varastosta ja käyttää tuotteen
def use_item_from_inventory(player_id, item):
    global inventory  # Käytetään globaalia inventory-muuttujaa

    if item not in ["fruits", "alcohol", "snacks", "soda", "meals", "water", "fuel"]:
        print("Virheellinen tuotteen nimi!")  # Invalid item name
        return False  # Invalid item

    if item == "fuel":
        item = "current_fuel"

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # Tarkistetaan, onko pelaajalla tuotetta ja onko varastossa enemmän kuin 0
    cursor.execute(f"SELECT {item} FROM inventory WHERE inventory_id = %s", (player_id,))
    current_quantity = cursor.fetchone()

    if current_quantity and current_quantity[0] > 0:
        # Vähennetään varastosta 1
        cursor.execute(f"UPDATE inventory SET {item} = {item} - 1 WHERE inventory_id = %s", (player_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return True  # Tuote käytettiin onnistuneesti
    else:
        cursor.close()
        conn.close()
        return False  # Tuotetta ei löytynyt tai ei tarpeeksi varastossa

# 🔹 Käsittelee asiakkaan mieltymyksiä ja varaston käyttöä
def process_customer_needs(player_id, customer, screen, font):
    global customer_mood, cash, reputation, current_customer, inventory

    if customer is None:
        print("Virhe: Ei valittua asiakasta!")
        return

    # Debugging customer preferences and inventory
    likes = customer.get("likes", [])
    dislikes = customer.get("dislikes", [])
    print(f"Asiakkaan mieltymykset: {likes}")
    print(f"Asiakkaan inhokit: {dislikes}")
    print(f"Pelaajan varasto: {inventory}")

    # Tarkistetaan ja käytetään asiakkaan mieltymyksiä varastosta
    for item in likes:
        if item in inventory and inventory.get(item, 0) > 0:
            print(f"Käytetään asiakasprofiilin tuotetta: {item}")
            if use_item_from_inventory(player_id, item):  # Käytetään tuotetta varastosta
                customer_mood += 1  # Parantaa asiakkaan mielialaa
                print(f"Tuote {item} käytettiin, mieliala parani.")
            else:
                print(f"Ei tarpeeksi {item} varastossa.")  # Ei tarpeeksi varastossa

    # Käsitellään inhokit (vähentää mielialaa)
    for item in dislikes:
        if item in inventory and inventory.get(item, 0) > 0:
            print(f"Poistetaan asiakasprofiilin tuotetta: {item}")
            if use_item_from_inventory(player_id, item):  # Käytetään tuotetta varastosta
                customer_mood -= 1  # Vähentää asiakkaan mielialaa
                print(f"Tuote {item} poistettiin, mieliala heikkeni.")
            else:
                print(f"Ei tarpeeksi {item} varastossa.")  # Ei tarpeeksi varastossa

    # Varmistetaan, että mieliala pysyy välillä 1-10
    customer_mood = max(1, min(customer_mood, 10))

    # Debug output asiakkaan mielalasta
    print(f"Asiakkaan mieliala matkan jälkeen: {customer_mood}/10")

    # Jos asiakas pääsee oikeaan määränpäähän
    if current_customer["destination"] == customer["destination"]:
        cash += 100 * customer_mood  # Pelaaja ansaitsee rahaa asiakkaan mielialan perusteella
        reputation += 5 if customer_mood >= 7 else -5  # Maine kasvaa tai laskee mielialan mukaan
        print(f"Matka onnistui! Rahaa ansaittiin: {100 * customer_mood}€ ja maine {'nousi' if customer_mood >= 7 else 'laski'}.")

    # Nollataan nykyinen asiakas matkan jälkeen
    current_customer = None
