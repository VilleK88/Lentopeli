import os
import json
import random
import mysql.connector
from routes.config import db_config
from database.db import connect_db


# 🔹 Lentokenttien hallinta
class AirportManager:
    def load_airports(self):
        try:
            with mysql.connector.connect(**db_config) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT ident FROM airport WHERE type = 'large_airport'")
                    icao_list = [row[0] for row in cursor.fetchall()]
            print(f"[DEBUG] Lentokenttien määrä: {len(icao_list)}")
            return icao_list
        except mysql.connector.Error as e:
            print(f"[DEBUG] Virhe lentokenttien haussa: {e}")
            return []

    def get_airport_info(self, icao):
        conn = connect_db()
        if not conn:
            print("[DEBUG] Ei yhteyttä tietokantaan.")
            return None
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT name, ident FROM airport WHERE type = 'large_airport' AND ident = %s", (icao,))
                result = cursor.fetchone()
        finally:
            conn.close()

        if result:
            print(f"[DEBUG] Lentokentän tiedot haettu: {result}")
        else:
            print(f"[DEBUG] Lentokenttää ei löytynyt ICAO:lla {icao}")
        return result

    def get_airport_coordinates(self, icao):
        """
        Gets the coordinates for a specific airport by ICAO code

        Args:
            icao (str): The ICAO code of the airport

        Returns:
            tuple: (latitude, longitude) or None if airport not found
        """
        conn = connect_db()
        if not conn:
            print("[DEBUG] Ei yhteyttä tietokantaan.")
            return None

        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT latitude_deg, longitude_deg FROM airport WHERE ident = %s", (icao,))
                result = cursor.fetchone()
        finally:
            conn.close()

        if result:
            print(f"[DEBUG] Lentokentän koordinaatit: {result}")
        else:
            print(f"[DEBUG] Koordinaatteja ei löytynyt ICAO:lla {icao}")

        return result if result else None


# 🔹 Talouden hallinta
class EconomyManager:
    def __init__(self, user_id):
        self.user_id = user_id

    def connect_db(self):
        try:
            return mysql.connector.connect(**db_config)
        except mysql.connector.Error as err:
            print(f"[DEBUG] Yhteysvirhe: {err}")
            return None

    def get_cash(self):
        conn = self.connect_db()
        if not conn:
            return 0
        cursor = conn.cursor()
        cursor.execute("SELECT cash FROM inventory WHERE inventory_id = %s", (self.user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0

    def get_fuel(self):
        conn = self.connect_db()
        if not conn:
            return 0
        cursor = conn.cursor()
        cursor.execute("SELECT current_fuel FROM inventory WHERE inventory_id = %s", (self.user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0

    def get_reputation(self):
        """Hakee käyttäjän maineen tietokannasta"""
        conn = self.connect_db()
        if not conn:
            return 5  # Oletus maine
        cursor = conn.cursor()
        cursor.execute("SELECT reputation FROM game WHERE id = %s", (self.user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 5

    def add_cash_to_inventory(self, amount):
        conn = self.connect_db()
        if not conn:
            return False
        cursor = conn.cursor()
        cursor.execute("UPDATE inventory SET cash = cash + %s WHERE inventory_id = %s", (amount, self.user_id))
        conn.commit()
        conn.close()
        return True

    def deduct_cash_from_inventory(self, amount):
        conn = self.connect_db()
        if not conn:
            return False
        cursor = conn.cursor()
        cursor.execute("UPDATE inventory SET cash = cash - %s WHERE inventory_id = %s AND cash >= %s",
                       (amount, self.user_id, amount))
        conn.commit()
        conn.close()
        return True

    def update_reputation(self, amount):
        """Päivittää käyttäjän maineen tietokantaan"""
        conn = self.connect_db()
        if not conn:
            return False
        cursor = conn.cursor()
        # Rajoitetaan maine välille 1-10
        cursor.execute("UPDATE game SET reputation = GREATEST(1, LEAST(10, reputation + %s)) WHERE id = %s",
                       (amount, self.user_id))
        conn.commit()
        conn.close()
        return True

    def process_customer_arrival(self, customer, mood):
        """
        Käsittelee asiakkaan saapumisen ja maksun

        Args:
            customer (dict): Asiakkaan tiedot
            mood (int): Asiakkaan mieliala asteikolla 1-10

        Returns:
            float: Asiakkaan maksama summa
        """
        # Lasketaan perushinta (voit säätää näitä arvoja)
        base_price = 500.0

        # Mieliala vaikuttaa maksun suuruuteen
        mood_multiplier = mood / 5.0  # Esim. 10/5 = 2.0, 5/5 = 1.0, 1/5 = 0.2

        # Lasketaan lopullinen maksu
        payment = base_price * mood_multiplier

        # Lisätään rahat inventoryyn
        self.add_cash_to_inventory(payment)

        # Päivitetään maine mielialan mukaan
        reputation_change = 0
        if mood >= 8:
            reputation_change = 1  # Erittäin tyytyväinen asiakas nostaa mainetta
        elif mood <= 3:
            reputation_change = -1  # Tyytymätön asiakas laskee mainetta

        if reputation_change != 0:
            self.update_reputation(reputation_change)

        print(f"[DEBUG] Asiakas maksoi {payment}€, mieliala {mood}/10, maine muuttui {reputation_change}")

        return payment


# 🔹 Asiakashallinta
class CustomerManager:
    def __init__(self):
        self.current_customer = None
        self.customer_mood = 5

    def get_customer_mood(self):
        return self.customer_mood

    def get_mood_emoji(self, mood):
        """Palauttaa asiakkaan mielialan mukaisen emojin"""
        if mood >= 8:
            return "😊"
        elif mood >= 6:
            return "🙂"
        elif mood <= 3:
            return "😠"
        elif mood <= 5:
            return "😕"
        return "😐"

    def load_customers(self):
        file_path = os.path.join(os.path.dirname(__file__), "../database/customersdb.json")
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                customers = json.load(file)
                print(f"[DEBUG] Ladattu {len(customers)} asiakasta.")
                return customers
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[DEBUG] Virhe asiakkaiden latauksessa: {e}")
            return []

    def select_customer(self, current_icao, icao_list, customers, customer_name=None):
        if not customers:
            print("[DEBUG] Asiakkaita ei löytynyt!")
            return None, None

        if customer_name:
            # Etsi asiakas nimen perusteella
            self.current_customer = next((c for c in customers if c["name"] == customer_name), None)
            if not self.current_customer:
                print(f"[DEBUG] Asiakasta {customer_name} ei löydy.")
                return None, None
            print(f"[DEBUG] Asiakas {customer_name} valittu.")
        else:
            # Valitse satunnainen asiakas
            self.current_customer = random.choice(customers)
            print(f"[DEBUG] Satunnainen asiakas valittu: {self.current_customer['name']}")

        # Tarkista onko asiakkaalla jo määränpää, jota ei tarvitse muuttaa
        if "destination" not in self.current_customer or not self.current_customer["destination"]:
            destination = random.choice([icao for icao in icao_list if icao != current_icao])
            self.current_customer["destination"] = destination
            print(f"[DEBUG] Asetettu uusi määränpää: {destination}")
        else:
            destination = self.current_customer["destination"]
            print(f"[DEBUG] Käytetään olemassa olevaa määränpää: {destination}")

        print(f"[DEBUG] Valittu asiakas: {self.current_customer['name']} -> {destination}")
        return self.current_customer, destination

    def get_customer_info(self):
        if not self.current_customer:
            print("[DEBUG] Ei asiakasta valittuna!")
            return {"has_customer": False, "message": "No customer selected"}

        customer = self.current_customer
        mood = self.get_customer_mood()
        likes = customer.get("likes", [])
        dislikes = customer.get("dislikes", [])

        return {
            "has_customer": True,
            "name": customer.get("name", "Unknown"),
            "destination": customer.get("destination", "Unknown"),
            "mood": mood,
            "likes": likes,
            "dislikes": dislikes
        }

    def reset_customer(self):
        print("[DEBUG] Asiakas nollattu.")
        self.current_customer = None
        self.customer_mood = 5

    def adjust_mood(self, value):
        self.customer_mood = max(1, min(10, self.customer_mood + value))
        print(f"[DEBUG] Asiakkaan mieliala säädetty: {self.customer_mood}")

    def adjust_mood_based_on_product(self, product_name):
        if not self.current_customer:
            print("[DEBUG] Ei asiakasta valittuna.")
            return

        product_name = product_name.strip().lower()
        likes = [item.strip().lower() for item in self.current_customer.get("likes", [])]
        dislikes = [item.strip().lower() for item in self.current_customer.get("dislikes", [])]

        if product_name in likes:
            self.adjust_mood(+2)
            print(f"[DEBUG] {self.current_customer['name']} piti tuotteesta ({product_name}) → moodi parani.")
        elif product_name in dislikes:
            self.adjust_mood(-1)
            print(f"[DEBUG] {self.current_customer['name']} inhosi tuotetta ({product_name}) → moodi huononi.")
        else:
            print(f"[DEBUG] {self.current_customer['name']} ei reagoinut tuotteeseen ({product_name}).")
