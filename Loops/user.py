import main
from Utils.utils import draw_user_list, draw_text, press_button_list, get_user_input, get_text_input, wipe_pygame_screen, \
    update_pygame_screen, draw_centered_list
import pygame
from Database.db import show_current_users, get_users_and_set_as_logged_in, check_if_name_in_db, add_user_to_db, get_logged_in_user_data, \
    save_game_progress
import time
import sys

# User info
user_name = ""
user_id = ""
logged_in = ""
current_icao = ""
co2_consumed = ""
co2_budget = ""

def main_menu(screen, font):
    global user_id, user_name

    key_list = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5]
    active = True

    while active:
        data_list = show_current_users()
        wipe_pygame_screen(screen)
        logged_in_user_text(screen, font)

        menu = ["1 - Tee uusi pelaaja", "2 - Valitse pelaaja",
                "3 - Aloita peli", "4 - Käyttäjälista" , "5 - Lopeta"]

        draw_centered_list(screen, font, menu)
        update_pygame_screen()

        char = press_button_list(key_list)
        if char == pygame.K_1:
            add_new_user(screen, font)
        elif char == pygame.K_2:
            select_user(screen, font)
        elif char == pygame.K_3:
            active = False
        elif char == pygame.K_4:
            print("4 painettu")
            draw_user_list(screen, font, data_list)
        elif char == pygame.K_5:
            pygame.quit()
            sys.exit()

# Käyttäjän valinta
def select_user(screen, font):
    global user_id, user_name
    input_text = ""
    active = True

    while active:
        wipe_pygame_screen(screen)
        draw_text(screen, "ESC", 5, 5, font)
        draw_text(screen, "Nimi: ", 80, 30, font)
        draw_text(screen, input_text, 80, 60, font)
        update_pygame_screen()

        input_text, active = get_user_input(input_text, active, False, True)

    result = get_users_and_set_as_logged_in(input_text)
    if result:
        user_id = result[0]
        user_name = result[1]
        wipe_pygame_screen(screen)
        draw_text(screen, f"Käyttäjä {user_name} kirjautunut sisään", 80, 30, font)
        update_pygame_screen()
        time.sleep(2)


def add_new_user(screen, font):
    active = True
    while active:
        wipe_pygame_screen(screen)
        draw_text(screen, "ESC", 5, 5, font)
        new_user_name, active = get_text_input(screen, font, "Nimi: ", False, True)
        update_pygame_screen()

        result = check_if_name_in_db(new_user_name)
        if result:
            wipe_pygame_screen(screen)
            draw_text(screen, f"Käyttäjä {new_user_name} löytyy jo tietokannasta", 80, 30, font)
            update_pygame_screen()
            time.sleep(2)
        else:
            if new_user_name:
                print(f"Active status: ", active)
                wipe_pygame_screen(screen)
                fuel_capacity = main.fuel_capacity
                add_user_to_db(new_user_name, fuel_capacity)
                draw_text(screen, f"Käyttäjä {new_user_name} lisätty tietokantaan", 80, 30, font)
                update_pygame_screen()
                time.sleep(2)
    wipe_pygame_screen(screen)

def logged_in_user_text(screen, font):
    global user_id, user_name
    result = get_logged_in_user_data()
    if result:
        user_id = result[0]
        user_name = result[1]
        current_fuel = result[2]
        current_icao = result[3]
    if user_id != "" and user_name != "":
        draw_text(screen, f"{user_name}", 10, 10, font)
        draw_text(screen, f"{current_fuel}", 10, 40, font)
        draw_text(screen, f"{current_icao}", 10, 70, font)

""" Huolto/kauppa koodi kutsutaan ingame_menusta user.py """
# ingame menu
def ingame_menu(screen, font, current_fuel, current_icao, remaining_distance):
    key_list = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5]
    if remaining_distance <= 0:
        flight_menu = ["1 - Syötä ICAO-koodi", "2 - Palaa kauppaan", "3 - Palaa matkustajiin",
            "4 - Tallenna ja lopeta", "5 - Tallenna, lopeta ja kirjaudu ulos"]
    else:
        flight_menu = ["1 - Syötä ICAO-koodi"]
    active = True

    while active:
        wipe_pygame_screen(screen)
        draw_centered_list(screen, font, flight_menu)
        update_pygame_screen()
        char = press_button_list(key_list)
        if char == pygame.K_1:
            active = False
        elif char == pygame.K_4 and remaining_distance <= 0:
            save_game_progress(user_id, current_fuel, current_icao)
            pygame.quit()
            sys.exit()

    return active