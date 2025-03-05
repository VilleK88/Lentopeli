import mysql.connector
from Routes.config import db_config


def shop(player_id, cash):
    #Pelaaja voi ostaa tuotteita kaupasta, ja inventory päivitetään tietokantaan.
    products = {
        "fruits": 10,
        "alcohol ": 15,
        "snacks": 8,
        "soda": 5,
        "meals": 12,
        "water": 3,
        "fuel": 100
    }

    print("\nKauppa - Valitse ostettava tuote:")
    for item, price in products.items():
        print(f"{item}: {price}€")

    selection = input("Mitä haluat ostaa? (kirjoita tuotteen nimi tai 'poistu' lopettaaksesi): ").strip().lower()

    if selection == "poistu":
        return cash

    if selection not in products:
        print("Tuotetta ei löydy kaupasta.")
        return cash

    price = products[selection]
    if cash >= price:
        cash -= price
        update_inventory(player_id, selection)
        print(f"Ostit {selection}. Käteistä jäljellä: {cash}€")
    else:
        print("Ei tarpeeksi rahaa!")

    return cash


def update_inventory(player_id, item):
    #Päivittää pelaajan inventory-tietokantaa.
    if item not in ["fruits", "alcohol", "snacks", "soda", "meals", "water", "fuel"]:
        print("Virheellinen tuotteen nimi!")
        return

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    sql = f"UPDATE inventory SET {item} = {item} + 1 WHERE inventory_id = %s"
    cursor.execute(sql, (player_id,))

    conn.commit()
    cursor.close()
    conn.close()
