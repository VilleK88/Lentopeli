import os
import json
import random
import mysql.connector
from Routes.config import db_config
from Database.db import connect_db
import pygame

# Globaalit muuttujat
current_customer = None
customer_mood = 5
cash = 500
reputation = 50

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

# 🔹 Käsittelee lentomatkan lopun ja päivittää pelaajan rahat, maineen ja asiakkaan mielialan
def process_flight(customer, wind_speed, inventory, icao):
    global customer_mood, cash, reputation, current_customer

    if customer is None:
        print("Virhe: Ei valittua asiakasta!")
        return

    # Debug-tulosteita asiakkaan mieltymyksistä ja varastosta
    likes = customer.get("likes", [])
    dislikes = customer.get("dislikes", [])
    print(f"Asiakkaan mieltymykset: {likes}")
    print(f"Asiakkaan inhokit: {dislikes}")
    print(f"Pelaajan varasto: {inventory}")

    # Mielialan muutos tuulen nopeuden (turbulenssin) perusteella
    if wind_speed >= 16:
        customer_mood -= 2

    # Päivitetään mielialaa asiakkaan mieltymysten perusteella
    for item in ["water", "alcohol", "meals", "snacks", "soda", "fruits"]:
        if item in likes and inventory.get(item, 0) > 0:
            customer_mood += 1
        if item in dislikes and inventory.get(item, 0) > 0:
            customer_mood -= 1

    # Varmistetaan, että mieliala pysyy välillä 1-10
    customer_mood = max(1, min(customer_mood, 10))

    # Tulostetaan asiakkaan mieliala laskun jälkeen
    print(f"Matka päättyi. Asiakkaan mieliala: {customer_mood}/10")

    # Debug-tuloste määränpäästä
    print(f"Asiakkaan määränpää JSON: {customer.get('destination', 'Ei määritelty')}")
    print(f"Saavutettu kenttä: {icao}")

    # Jos asiakas pääsee haluamaansa määränpään
    if icao == customer.get("destination", ""):
        cash += 100 * customer_mood  # Rahamäärä perustuu asiakkaan mielialaan
        reputation += 5 if customer_mood >= 7 else -5  # Mainetta lisätään tai vähennetään
        print(f"Asiakas saapui perille! {100 * customer_mood} rahaa ja {'lisäsit' if customer_mood >= 7 else 'vähensit'} maineesi.")
    else:
        print("Asiakas ei päässyt perille.")

    # Poistetaan nykyinen asiakas käytöstä
    current_customer = None
