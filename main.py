import time
from Loops import flight, user
from Routes import server
from datetime import datetime
from Utils.utils import get_valid_icao, draw_arrived_airport, initialize_pygame_screen
from Database.db import get_columns_and_tables, get_airport_coords, get_logged_in_user_data, get_inventory

remaining_distance = None
fuel_capacity = 48900
current_fuel = 0
fuel_per_km = 2.6
time_multiplier = 125 # tämä muuttuja määrittää pelin nopeuden
current_time = None
current_location = None # Latitude & Longitude tallennetaan tähän

# Pygame asetukset
screen = None
font = None

def start():
    global remaining_distance, current_fuel, current_time, current_speed_kmh,current_location, on_flight, zoom, screen, font

    # Alustetaan pygame-ikkuna
    screen, font = initialize_pygame_screen()

    # tarkistaa onko vaaditut taulukot/sarakkeet tietokannassa ja jos eivät ole niin tekee ne
    get_columns_and_tables()

    # main menu avautuu tässä
    user.main_menu(screen, font)
    # hakee sisään kirjautuneen käyttäjän lähtölentoaseman ja inventaarion
    result_game = get_logged_in_user_data()
    starting_airport = None
    if result_game:
        starting_airport = result_game[2]
    result_inventory = get_inventory(user.user_id)
    if result_inventory:
        current_fuel = result_inventory[0]


    # Aika, polttoaine ja nopeus muuttujien alustus
    current_time = datetime.now()
    #current_speed_kmh = max_speed_kmh

    # Lento-loopin aloitus
    airport = get_airport_coords(starting_airport)
    return airport, screen

def main_program():
    global remaining_distance, current_location, on_flight, current_time, current_fuel, current_speed_kmh, time_multiplier, screen, font

    # Palauttaa start sen hetkisen lentoaseman tiedot ja pygame ikkunan asetukset
    current_icao, screen = start()
    current_location = current_icao[2], current_icao[3]

    # Käynnistää serverin ja lähettää lentoaseman koordinaatit
    server.starting_coordinates(current_icao[2], current_icao[3])
    server.start_server()

    menu_on = True

    # main loop
    while True:
        on_flight = False
        server.update_server(flight.new_lat, flight.new_lon, False)
        if remaining_distance != None:
            if remaining_distance <= 0:
                draw_arrived_airport(current_icao[0], current_icao[1], screen, 20, 50, font)
                time.sleep(2)
        else:
            remaining_distance = 0

        """ Huolto/kauppa koodi kutsutaan ingame_menusta user.py """
        # Käynnistetään ingame menu
        while menu_on:
            menu_on = user.ingame_menu(screen, font, current_fuel, current_icao[1], remaining_distance)

        # ICAO-koodin syöttö seuraavalle lentokentälle
        icao = get_valid_icao(screen, font, "ICAO-koodi: ")

        # Tarkistaa loppuiko lento kesken
        remaining_distance = flight.was_flight_interrupted(remaining_distance, current_icao, icao, current_location)

        on_flight = True
        flight.stop_flight = False
        # Lento-loopin aloitus
        remaining_distance, current_time, current_fuel, current_location = flight.flight_loop(screen, font, current_location, (icao[2], icao[3]), remaining_distance, current_time, current_fuel, time_multiplier, current_location)

        current_icao = icao
        menu_on = True

if __name__ == '__main__':
    main_program()