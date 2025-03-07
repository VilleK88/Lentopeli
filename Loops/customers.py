import mysql.connector
import json
import random
from Routes.config import db_config
from Database.db import connect_db

current_customer = None
customer_mood = 5
cash = 0
reputation = 50


def get_airport_info(icao):
    #Hakee lentokentän tiedot ICAO-koodin perusteella.
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        sql = "SELECT name, ident, type FROM airport WHERE type = 'large_airport' AND ident = %s"
        cursor.execute(sql, (icao,))
        result = cursor.fetchall()
        conn.close()
        return result if result else None
    return None

def load_and_select_customer(current_icao):
    #lataa asiakastiedot, valitsee satunnaisen asiakkaan ja asettaa määränpään.
    global current_customer

    # Lataa asiakkaat ja lentokenttien ICAO-koodit
    with open("customersdb.json", "r", encoding="utf-8") as file:
        customers = json.load(file)

    icao_list = load_airports()  # Haetaan ICAO-koodit

    current_customer = random.choice(customers)

    # Valitsee satunnaisen määränpään nykyisen ICAO-koodin ulkopuolelta
    destination_icao = random.choice([icao for icao in icao_list if icao != current_icao])

    return current_customer, destination_icao


def process_flight(customer, wind_speed, water, alcohol, snacks, soda, meals, fruits, icao):
    #Käsittelee asiakkaan mielialan, rahojen ja maineen lentomatkan lopussa.
    global customer_mood, cash, reputation

    if customer is None:
        return

    # Käsittelee mielialan tuulen nopeuden mukaan (esim. turbulenssi)
    if wind_speed >= 16:
        customer_mood -= 2

    likes = customer.get("likes", [])
    dislikes = customer.get("dislikes", [])

    # Päivittää mielialaa asiakkaan mieltymyksien mukaan
    for item in ["water", "alcohol", "meals", "snacks", "soda", "fruits"]:
        if item in likes and locals()[item] > 0:
            customer_mood += 1
        if item in dislikes and locals()[item] > 0:
            customer_mood -= 1

    # Varmistaa, että mieliala pysyy alueella 1-10
    customer_mood = max(1, min(customer_mood, 10))

    # Lentomatkan loppuprosessi
    if icao == customer.get("destination", ""):
        cash += 100 * customer_mood  # Lisää rahaa asiakkaan mielialan mukaan
        reputation += 5 if customer_mood >= 7 else -5  # Lisää mainetta mielialan mukaan

    current_customer = None  # Asiakas , ei ole enää valittavana
