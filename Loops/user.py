import main
from Utils.utils import draw_text
from Database.db import get_users_and_set_as_logged_in, check_if_name_in_db, add_user_to_db, get_logged_in_user_data, \
    get_inventory, get_airport_coords
import time
from Loops import flight

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

# Näyttää käyttäjän tiedot ruudulla
def user_info_on_screen(screen, font):
    global user_id, user_name, current_icao, cash#, current_fuel

    if user_id != "" and user_name != "":
        draw_text(screen, f"{user_name}", 10, 10, font)
        draw_text(screen, f"{current_icao}", 10, 40, font)
        draw_text(screen, f"{flight.current_fuel:.0f}", 10, 70, font)

""" Huolto/kauppa koodi kutsutaan ingame_menusta user.py """
# ingame menu
def ingame_menu(current_icao, remaining_distance):
    global user_id, ingame_menu_active, target_airport

    # Lista käytössä olevista näppäimistä
    """key_list = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5] # Käytettävissä olevat painikkeet
    if remaining_distance <= 0:
        flight_menu = ["1 - Syötä ICAO-koodi", "2 - Kauppa", "3 - Matkustajat",
            "4 - Tallenna ja lopeta", "5 - Tallenna, lopeta ja kirjaudu ulos"]
    else:
        flight_menu = ["1 - Syötä ICAO-koodi"]"""
    #ingame_menu_active = True # Loopin tila

    # Haetaan säätila
    #weather = get_weather(main.current_location[0], main.current_location[1])
    #weather, turbulence_warning = update_weather_on_ground(weather)
    #last_weather_update = time.time()

    while ingame_menu_active:
        time.sleep(1)

    print(f"User Target airport: {target_airport}")

    return ingame_menu_active, target_airport

# Alustaa aloituslentokentän ja palauttaa sen ICAO-koodin
def initialize_starting_airport():
    global current_icao
    starting_airport = current_icao
    return starting_airport

# Päivittää säätilan ja määrittää turbulenssivaroituksen
"""def update_weather_on_ground(weather):
    if weather is None:
        weather = {"weather": "Tuntematon", "temp": 0, "wind": 0}
        turbulence_warning = ""

    if weather["wind"] > 15:
        turbulence_warning = ", Kova tuuli!"
    else:
        turbulence_warning = ""

    return weather, turbulence_warning"""

# Tarkistaa, onko sää päivitettävä ja päivittää sen 5 sekunnin välein
"""def weather_timer_ground(weather, last_weather_update):
    if time.time() - last_weather_update >= 5:
        new_weather = get_weather(main.current_location[0], main.current_location[1])
        if new_weather:
            weather = new_weather
            last_weather_update = time.time()
    return weather, last_weather_update"""

# Näyttää säätilan pygame-ikkunassa
"""def weather_info_on_screen(weather, last_weather_update, screen, font):
    if user_name != "":
        weather, last_weather_update = weather_timer_ground(weather, last_weather_update)
        weather, turbulence_warning = update_weather_on_ground(weather)
        draw_text(screen, f"Sää: {weather['weather']}, Tuuli: {weather['wind']:.2f} m/s {turbulence_warning}", 10, 365,
                  font)"""