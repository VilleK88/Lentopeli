import mysql.connector
from Routes.config import db_config
from Utils.utils import wipe_pygame_screen, update_pygame_screen, draw_centered_shop_list, draw_text_to_center_x
import main



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
    input_text = ""
    active = True

    while active:
        wipe_pygame_screen(main.screen)
        draw_text(main.screen, "ESC", 5, 5, main.font)
        draw_centered_shop_list(main.screen, font, 70, products)
        draw_text_to_center_x(main.screen, input_text, 180, main.font)
        update_pygame_screen()

        input_text, active = get_user_input(input_text, active, False, True)

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
