import pygame
import mysql.connector
from Routes.config import db_config
from Utils.utils import (
    wipe_pygame_screen,
    update_pygame_screen,
    draw_centered_shop_list,
    draw_text_to_center_x,
    draw_text
)
import time


def shop(player_id, cash, screen, font):
    products = {
        "fruits": 10,
        "alcohol": 15,
        "snacks": 8,
        "soda": 5,
        "meals": 12,
        "water": 3,
        "fuel": 100
    }
    products_list = [f"{item}: {price}€" for item, price in products.items()]

    input_text = ""
    active = True

    while active:
        wipe_pygame_screen(screen)
        draw_text(screen, "ESC - Poistu", 5, 5, font)
        draw_centered_shop_list(screen, font, 50, products_list)
        draw_text_to_center_x(screen, input_text, 180, font)
        update_pygame_screen()

        # Käsitellään näppäinkomennot
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:  # ESC sulkee kaupan
                    active = False
                elif event.key == pygame.K_RETURN:  # Enter käsittelee syötteen ja tekee oston
                    selection = input_text.strip().lower()
                    if selection == "poistu":  # Poistuu kaupasta, jos syötteessä on "poistu"
                        active = False
                    elif selection in products:
                        price = products[selection]
                        if cash >= price:
                            cash -= price
                            update_inventory(player_id, selection)
                            wipe_pygame_screen(screen)
                            draw_text_to_center_x(screen, f"Ostit {selection}. Käteistä jäljellä: {cash}€", 180, font)
                            update_pygame_screen()
                            time.sleep(2)
                        else:
                            wipe_pygame_screen(screen)
                            draw_text_to_center_x(screen, "Ei tarpeeksi rahaa!", 180, font)
                            update_pygame_screen()
                            time.sleep(2)
                    else:
                        wipe_pygame_screen(screen)
                        draw_text_to_center_x(screen, "Tuotetta ei löydy kaupasta.", 180, font)
                        update_pygame_screen()
                        time.sleep(2)
                    input_text = ""  # Nollataan syöte
                elif event.key == pygame.K_BACKSPACE:  # Poistetaan merkkejä syötteestä
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode  # Lisätään syöte, jos se ei ole erikoisnäppäin

    return cash


def update_inventory(player_id, item):
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
