import main
from Utils.utils import draw_user_list, draw_text, press_button_list, get_user_input, wipe_pygame_screen, \
    update_pygame_screen, draw_centered_list, draw_text_to_center_x
from Utils.weather import get_weather
import pygame
from Database.db import show_current_users, get_users_and_set_as_logged_in, check_if_name_in_db, add_user_to_db, get_logged_in_user_data, \
    save_game_progress, get_inventory, log_out, get_airport_coords
import time
import sys
from Loops import flight, shop, customers


# User info
user_name = ""
user_id = ""
logged_in = ""
current_icao = ""
co2_consumed = ""
co2_budget = ""
weather = None
cash = 0
reputation = 0

def main_menu(screen, font):
    global user_id, user_name, weather

    key_list = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6]
    active = True

    # Alustetaan sisäänkirjautunut käyttäjä jos sellainen on sekä haetaan sää
    starting_airport = initialize_player_data()
    if starting_airport:
        airport = get_airport_coords(starting_airport)
        weather = get_weather(airport[2], airport[3])
    else:
        weather = get_weather(main.current_location[0], main.current_location[1])

    weather, turbulence_warning = update_weather_on_ground(weather)
    last_weather_update = time.time()

    while active:
        data_list = show_current_users()
        wipe_pygame_screen(screen)
        logged_in_user_text(screen, font)

        if user_name != "":
            # Päivitetään sää
            weather, last_weather_update = weather_timer_ground(weather, last_weather_update)
            weather, turbulence_warning = update_weather_on_ground(weather)
            draw_text(screen, f"Sää: {weather['weather']}, Tuuli: {weather['wind']:.2f} m/s {turbulence_warning}", 10, 365, font)

        menu = ["1 - Tee uusi pelaaja", "2 - Valitse pelaaja",
                "3 - Aloita peli", "4 - Käyttäjälista" , "5 - Lopeta", "6 - Lopeta ja kirjaudu ulos"]

        draw_centered_list(screen, font, 70, menu)
        update_pygame_screen()

        char = press_button_list(key_list)
        if char == pygame.K_1:
            add_new_user(screen, font)
        elif char == pygame.K_2:
            select_user(screen, font)
        elif char == pygame.K_3:
            if user_name != "":
                active = False
            else:
                wipe_pygame_screen(screen)
                draw_text_to_center_x(screen, "Kirjaudu sisään ensiksi", 165, font)
                update_pygame_screen()
                time.sleep(2)
        elif char == pygame.K_4:
            print("4 painettu")
            draw_user_list(screen, font, data_list)
        elif char == pygame.K_5:
            pygame.quit()
            sys.exit()
        elif char == pygame.K_6:
            if user_name != "":
                log_out()
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
        draw_text_to_center_x(screen, "Nimi:", 150, font)
        draw_text_to_center_x(screen, input_text, 180, font)
        update_pygame_screen()

        input_text, active = get_user_input(input_text, active, False, True)

    result = get_users_and_set_as_logged_in(input_text)
    if result:
        user_id = result[0]
        user_name = result[1]
        wipe_pygame_screen(screen)
        draw_text_to_center_x(screen, f"Käyttäjä {user_name} kirjautunut sisään", 165, font)
        update_pygame_screen()
        time.sleep(2)


def add_new_user(screen, font):
    active = True
    new_user_name = ""
    while active:
        wipe_pygame_screen(screen)
        draw_text(screen, "ESC", 5, 5, font)
        draw_text_to_center_x(screen, "Nimi:", 150, font)
        draw_text_to_center_x(screen, new_user_name, 180, font)
        update_pygame_screen()

        new_user_name, active = get_user_input(new_user_name, active, False, True)

    result = check_if_name_in_db(new_user_name)
    if result:
        wipe_pygame_screen(screen)
        draw_text_to_center_x(screen, f"Käyttäjä {new_user_name} löytyy jo tietokannasta", 165, font)
        update_pygame_screen()
        time.sleep(2)
    else:
        if new_user_name:
            print(f"Active status: ", active)
            wipe_pygame_screen(screen)
            add_user_to_db(new_user_name)
            draw_text_to_center_x(screen, f"Käyttäjä {new_user_name} lisätty tietokantaan", 165, font)
            update_pygame_screen()
            time.sleep(2)
    wipe_pygame_screen(screen)

def logged_in_user_text(screen, font):
    global user_id, user_name, cash

    result_game = get_logged_in_user_data()

    if result_game:
        user_id = result_game[0]
        user_name = result_game[1]
        current_icao = result_game[2]
        reputation = result_game[3]

    result_inventory = get_inventory(user_id)

    if result_inventory:
        cash = result_inventory[0]
        current_fuel = result_inventory[1]

    if user_id != "" and user_name != "":
        draw_text(screen, f"{user_name}", 10, 10, font)
        draw_text(screen, f"{current_fuel}", 10, 40, font)
        draw_text(screen, f"{current_icao}", 10, 70, font)

""" Huolto/kauppa koodi kutsutaan ingame_menusta user.py """
# ingame menu
def ingame_menu(screen, font, current_fuel, current_icao, remaining_distance):
    global cash
    key_list = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5]
    if remaining_distance <= 0:
        flight_menu = ["1 - Syötä ICAO-koodi", "2 - Kauppa", "3 - Matkustajat",
            "4 - Tallenna ja lopeta", "5 - Tallenna, lopeta ja kirjaudu ulos"]
    else:
        flight_menu = ["1 - Syötä ICAO-koodi"]
    active = True

    while active:
        wipe_pygame_screen(screen)
        draw_centered_list(screen, font, 100, flight_menu)
        update_pygame_screen()
        char = press_button_list(key_list)
        if char == pygame.K_1:
            active = False
        elif char == pygame.K_4 and remaining_distance <= 0:
            save_game_progress(user_id, current_fuel, current_icao, False)
            pygame.quit()
            sys.exit()
        elif char == pygame.K_5 and remaining_distance <= 0:
            save_game_progress(user_id, current_fuel, current_icao, True)
            pygame.quit()
            sys.exit()
        elif char == pygame.K_2 and remaining_distance <= 0:
            # Avaa kauppa-funktio
            shop.shop(user_id, cash, screen, font)
        elif char == pygame.K_3 and remaining_distance <= 0:
            # Avaa load_and_select_customer-funktio customers.py-tiedostosta
            customers.load_and_select_customer(current_icao, screen, font)
            #active = False

    return active

# Alustetaan aloituslentokenttä ja polttoaine
def initialize_player_data():
    global cash
    result_game = get_logged_in_user_data()
    starting_airport = None
    if result_game:
        starting_airport = result_game[2]
    result_inventory = get_inventory(user_id)
    if result_inventory:
        cash = result_inventory[0]
        flight.current_fuel = result_inventory[1]
    return starting_airport

def update_weather_on_ground(weather):

    if weather is None:
        weather = {"weather": "Tuntematon", "temp": 0, "wind": 0}
        turbulence_warning = ""

    if weather["wind"] > 15:
        turbulence_warning = ", Kova tuuli!"
    else:
        turbulence_warning = ""

    return weather, turbulence_warning

def weather_timer_ground(weather, last_weather_update):
    if time.time() - last_weather_update >= 5:
        new_weather = get_weather(main.current_location[0], main.current_location[1])
        if new_weather:
            weather = new_weather
            last_weather_update = time.time()
    return weather, last_weather_update