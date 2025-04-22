import main
from database.db import get_users_and_set_as_logged_in, check_if_name_in_db, add_user_to_db, get_logged_in_user_data, \
    get_inventory, get_airport_coords, save_game_progress
import time
from loops import flight

# Käyttäjän tiedot (globaalit muuttujat)
user_name = ""
user_id = ""
logged_in = ""
current_icao = ""
airport_name = ""
co2_consumed = ""
co2_budget = ""
cash = 0
reputation = 0

# Muut globaalit muuttujat
main_menu_active = True
ingame_menu_active = True
target_airport = None

# Päävalikko, jossa käyttäjä voi luoda uuden pelaajan, valita pelaajan tai aloittaa pelin
def main_menu():
    global user_id, user_name, main_menu_active


    get_user_data() # Haetaan kirjautuneen käyttäjän tiedot
    starting_airport = initialize_starting_airport() # Haetaan aloituslentokenttä

    # Haetaan lentoaseman koordinaatit, jos aloitusasema on määritetty
    if starting_airport:
        airport = get_airport_coords(starting_airport)
        main.current_location = airport[2], airport[3]

    # Haetaan ja päivitetään säätila
    #weather = get_weather(main.current_location[0], main.current_location[1])
    #weather, turbulence_warning = update_weather_on_ground(weather)
    #last_weather_update = time.time()

    while main_menu_active:
        time.sleep(1)

def start_game():
    global user_name, main_menu_active
    if user_name != "":
        main_menu_active = False
        print("Aloita peli")
        return True
    return False

# Funktio käyttäjän valintaan tietokannasta
def select_user(name):
    global user_id, user_name, weather, current_icao

    result = get_users_and_set_as_logged_in(name)
    if result:
        user_id = result[0]
        user_name = result[1]
        get_user_data()
        airport = get_airport_coords(current_icao)
        main.current_location = airport[2], airport[3]
        return True

# Funktio uuden käyttäjän lisäämiseksi tietokantaan
def add_new_user(name):
    if name == "" or len(name) > 15:
        return False
    result = check_if_name_in_db(name)
    if result:
        return False
    else:
        add_user_to_db(name)
        return True

# Hakee sisäänkirjautuneen käyttäjän tiedot tietokannasta
def get_user_data():
    global user_id, user_name, current_icao, cash, reputation, airport_name

    result_game = get_logged_in_user_data()

    if result_game:
        user_id = result_game[0]
        user_name = result_game[1]
        airport = get_airport_coords(result_game[2])
        airport_name = airport[0]
        current_icao = result_game[2]
        reputation = result_game[3]

    result_inventory = get_inventory(user_id)

    if result_inventory:
        cash = result_inventory[1]
        flight.current_fuel = result_inventory[0]

""" Huolto/kauppa koodi kutsutaan ingame_menusta user.py """
# ingame menu
def ingame_menu():
    global user_id, ingame_menu_active, target_airport, current_icao

    save_game_progress(user_id, flight.current_fuel, current_icao, False);

    while ingame_menu_active:
        time.sleep(1)

    return ingame_menu_active, target_airport

# Alustaa aloituslentokentän ja palauttaa sen ICAO-koodin
def initialize_starting_airport():
    global current_icao
    starting_airport = current_icao
    return starting_airport