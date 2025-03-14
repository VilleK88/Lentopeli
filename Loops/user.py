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

# Käyttäjän tiedot (globaalit muuttujat)
user_name = ""
user_id = ""
logged_in = ""
current_icao = ""
co2_consumed = ""
co2_budget = ""
cash = 0
reputation = 0

# Päävalikko, jossa käyttäjä voi luoda uuden pelaajan, valita pelaajan tai aloittaa pelin
def main_menu(screen, font):
    global user_id, user_name

    key_list = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6] # Käytettävissä olevat painikkeet
    active = True # Loopin tila

    get_user_data() # Haetaan kirjautuneen käyttäjän tiedot
    starting_airport = initialize_starting_airport() # Haetaan aloituslentokenttä

    # Haetaan lentoaseman koordinaatit, jos aloitusasema on määritetty
    if starting_airport:
        airport = get_airport_coords(starting_airport)
        main.current_location = airport[2], airport[3]

    # Haetaan ja päivitetään säätila
    weather = get_weather(main.current_location[0], main.current_location[1])
    weather, turbulence_warning = update_weather_on_ground(weather)
    last_weather_update = time.time()

    while active:
        wipe_pygame_screen(screen) # Pyyhitään ruutu
        user_info_on_screen(screen, font) # Näytetään käyttäjän tiedot

        # Päivitetään sää
        weather, last_weather_update = weather_timer_ground(weather, last_weather_update)
        weather, turbulence_warning = update_weather_on_ground(weather)
        weather_info_on_screen(weather, last_weather_update, screen, font)

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
            data_list = show_current_users()
            draw_user_list(screen, font, data_list)
        elif char == pygame.K_5:
            pygame.quit()
            sys.exit()
        elif char == pygame.K_6:
            if user_name != "":
                log_out()
            pygame.quit()
            sys.exit()

# Funktio käyttäjän valintaan tietokannasta
def select_user(screen, font):
    global user_id, user_name, weather, current_icao
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
        get_user_data()
        airport = get_airport_coords(current_icao)
        main.current_location = airport[2], airport[3]
        wipe_pygame_screen(screen)
        draw_text_to_center_x(screen, f"Käyttäjä {user_name} kirjautunut sisään", 165, font)
        update_pygame_screen()
        time.sleep(2)

# Funktio uuden käyttäjän lisäämiseksi tietokantaan
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

# Hakee sisäänkirjautuneen käyttäjän tiedot tietokannasta
def get_user_data():
    global user_id, user_name, current_icao, cash, reputation

    result_game = get_logged_in_user_data()

    if result_game:
        user_id = result_game[0]
        user_name = result_game[1]
        current_icao = result_game[2]
        reputation = result_game[3]

    result_inventory = get_inventory(user_id)

    if result_inventory:
        cash = result_inventory[1]
        flight.current_fuel = result_inventory[0]

# Näyttää käyttäjän tiedot ruudulla
def user_info_on_screen(screen, font):
    global user_id, user_name, current_icao, cash#, current_fuel

    if user_id != "" and user_name != "":
        draw_text(screen, f"{user_name}", 10, 10, font)
        draw_text(screen, f"{current_icao}", 10, 40, font)
        draw_text(screen, f"{flight.current_fuel:.0f}", 10, 70, font)

""" Huolto/kauppa koodi kutsutaan ingame_menusta user.py """
# ingame menu
def ingame_menu(screen, font, current_icao, remaining_distance):
    global user_id

    # Lista käytössä olevista näppäimistä
    key_list = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5] # Käytettävissä olevat painikkeet
    if remaining_distance <= 0:
        flight_menu = ["1 - Syötä ICAO-koodi", "2 - Kauppa", "3 - Matkustajat",
            "4 - Tallenna ja lopeta", "5 - Tallenna, lopeta ja kirjaudu ulos"]
    else:
        flight_menu = ["1 - Syötä ICAO-koodi"]
    active = True # Loopin tila

    # Haetaan säätila
    weather = get_weather(main.current_location[0], main.current_location[1])
    weather, turbulence_warning = update_weather_on_ground(weather)
    last_weather_update = time.time()

    while active:
        wipe_pygame_screen(screen)
        draw_centered_list(screen, font, 100, flight_menu)
        user_info_on_screen(screen, font)

        # Päivitetään sää
        weather, last_weather_update = weather_timer_ground(weather, last_weather_update)
        weather, turbulence_warning = update_weather_on_ground(weather)
        weather_info_on_screen(weather, last_weather_update, screen, font)
        update_pygame_screen()

        char = press_button_list(key_list)
        if char == pygame.K_1:
            active = False
        elif char == pygame.K_4 and remaining_distance <= 0:
            save_game_progress(user_id, flight.current_fuel, current_icao, False)
            pygame.quit()
            sys.exit()
        elif char == pygame.K_5 and remaining_distance <= 0:
            save_game_progress(user_id, flight.current_fuel, current_icao, True)
            pygame.quit()
            sys.exit()
        elif char == pygame.K_2 and remaining_distance <= 0:
            shop.shop(user_id, cash, screen, font) # Avaa kauppa
        elif char == pygame.K_3 and remaining_distance <= 0:
            customers.load_and_select_customer(current_icao, screen, font) # Avaa matkustajavalinnan

    return active

# Alustaa aloituslentokentän ja palauttaa sen ICAO-koodin
def initialize_starting_airport():
    global current_icao
    starting_airport = current_icao
    return starting_airport

# Päivittää säätilan ja määrittää turbulenssivaroituksen
def update_weather_on_ground(weather):
    if weather is None:
        weather = {"weather": "Tuntematon", "temp": 0, "wind": 0}
        turbulence_warning = ""

    if weather["wind"] > 15:
        turbulence_warning = ", Kova tuuli!"
    else:
        turbulence_warning = ""

    return weather, turbulence_warning

# Tarkistaa, onko sää päivitettävä ja päivittää sen 5 sekunnin välein
def weather_timer_ground(weather, last_weather_update):
    if time.time() - last_weather_update >= 5:
        new_weather = get_weather(main.current_location[0], main.current_location[1])
        if new_weather:
            weather = new_weather
            last_weather_update = time.time()
    return weather, last_weather_update

# Näyttää säätilan pygame-ikkunassa
def weather_info_on_screen(weather, last_weather_update, screen, font):
    if user_name != "":
        weather, last_weather_update = weather_timer_ground(weather, last_weather_update)
        weather, turbulence_warning = update_weather_on_ground(weather)
        draw_text(screen, f"Sää: {weather['weather']}, Tuuli: {weather['wind']:.2f} m/s {turbulence_warning}", 10, 365,
                  font)