import os
import json
import random
import mysql.connector
from routes.config import db_config
from database.db import connect_db

# 🔹 Asiakashallinta
class CustomerManager:
    def __init__(self):
        self.current_customer = None
        self.customer_mood = 5

    def load_customers(self):
        file_path = os.path.join(os.path.dirname(__file__), "../database/customersdb.json")
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                customers = json.load(file)
                print(f"Ladattu {len(customers)} asiakasta.")
                return customers
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Virhe asiakkaiden latauksessa: {e}")
            return []

    def select_customer(self, current_icao, icao_list, customers):
        self.current_customer = random.choice(customers)
        destination = random.choice([icao for icao in icao_list if icao != current_icao])
        self.current_customer["destination"] = destination
        print(f"Valittu asiakas: {self.current_customer['name']} -> {destination}")
        return self.current_customer, destination

    def get_customer_mood(self):
        return self.customer_mood

    def reset_customer(self):
        self.current_customer = None
        self.customer_mood = 5

    def adjust_mood(self, value):
        self.customer_mood = max(1, min(10, self.customer_mood + value))


# 🔹 Varaston hallinta
class InventoryManager:
    def __init__(self):
        self.inventory = {}

    def set_inventory(self, inventory_data):
        self.inventory = inventory_data

    def get_inventory(self):
        return self.inventory

    def use_item(self, player_id, item):
        if item == "fuel":
            item = "current_fuel"

        valid_items = ["fruits", "alcohol", "snacks", "soda", "meals", "water", "current_fuel"]
        if item not in valid_items:
            print("Virheellinen tuotteen nimi!")
            return False

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(f"SELECT {item} FROM inventory WHERE inventory_id = %s", (player_id,))
        current_quantity = cursor.fetchone()

        if current_quantity and current_quantity[0] > 0:
            cursor.execute(f"UPDATE inventory SET {item} = {item} - 1 WHERE inventory_id = %s", (player_id,))
            conn.commit()
            print(f"Käytettiin tuotetta: {item}")
            success = True
        else:
            print(f"Ei tarpeeksi varastossa: {item}")
            success = False

        cursor.close()
        conn.close()
        return success


# 🔹 Lentokenttien hallinta
class AirportManager:
    def load_airports(self):
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT ident FROM airport WHERE type = 'large_airport'")
            icao_list = [row[0] for row in cursor.fetchall()]
            return icao_list
        except mysql.connector.Error as e:
            print(f"Virhe lentokenttien haussa: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_airport_info(self, icao):
        conn = connect_db()
        if not conn:
            return None
        cursor = conn.cursor()
        cursor.execute("SELECT name, ident FROM airport WHERE type = 'large_airport' AND ident = %s", (icao,))
        result = cursor.fetchone()
        conn.close()
        return result if result else None


# 🔹 Talouden hallinta
class EconomyManager:
    def __init__(self):
        self.cash = 500
        self.reputation = 50

    def add_cash(self, amount):
        self.cash += amount
        print(f"+{amount}€ → Käteinen: {self.cash}")

    def adjust_reputation(self, mood):
        if mood >= 7:
            self.reputation += 5
            print("Maine nousi.")
        else:
            self.reputation -= 5
            print("Maine laski.")
        print(f"Maine: {self.reputation}")

    def get_cash(self):
        return self.cash

    def get_reputation(self):
        return self.reputation
