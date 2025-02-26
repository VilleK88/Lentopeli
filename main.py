import time
from Loops import flight, user
from Routes import server
from datetime import datetime
from Utils.utils import calculate_distance_between_airports, calculate_distance, get_valid_icao, draw_arrived_airport, \
    initialize_pygame_screen
from Database.db import check_if_logged_in_exists, get_airport_coords, check_if_logged_in

# Lentokoneen tiedot
remaining_distance = None
max_speed_kmh = 780
current_speed_kmh = 0
fuel_capacity = 25941
current_fuel = 0
fuel_per_km = 2.6
time_multiplier = 100 # tämä muuttuja määrittää pelin nopeuden
current_time = None
current_location = None # Latitude & Longitude tallennetaan tähän
on_flight = False
keyboard_hook = None
zoom = 10

# Pygame asetukset
screen = None
font = None

def start():
    global remaining_distance, current_fuel, current_time, current_speed_kmh,current_location, on_flight, zoom, screen, font

    # Alusta pygame-ikknua
    screen, font = initialize_pygame_screen()

    # tarkistaa onko logged_in sarake jo olemassa tietokannassa, ja jos ei ole niin tekee sen
    check_if_logged_in_exists()

    # menu
    user.main_menu(screen, font)
    result = check_if_logged_in()
    if result:
        current_fuel = result[2]

    # Aika, polttoaine, nopeus ja zoom muuttujien alustus
    current_time = datetime.now()
    #current_fuel = fuel_capacity
    current_speed_kmh = max_speed_kmh
    flight.zoom = zoom

    # Lento-loopin aloitus
    airport = get_airport_coords("EFHK")
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
            menu_on = user.ingame_menu(screen, font, current_fuel)

        # ICAO-koodin syöttö seuraavalle lentokentälle
        icao = get_valid_icao(screen, font, "ICAO-koodi: ")

        if remaining_distance <= 0:
            remaining_distance = calculate_distance_between_airports(current_icao, icao)
            print(f"Lentoaseman {current_icao[0]} {current_icao[1]} etäisyys {icao[0]} {icao[1]} on {remaining_distance:.2f} kilometriä")
        else:
            remaining_distance = calculate_distance(current_location, icao)
            print(f"Nykyisen sijaintisi {current_location[0]} {current_location[1]} etäisyys {icao[0]} {icao[1]} on {remaining_distance:.2f} kilometriä")

        on_flight = True
        flight.stop_flight = False
        # Lento-loopin aloitus
        remaining_distance, current_time, current_fuel, current_location = flight.flight_loop(screen, font, current_location, (icao[2], icao[3]), remaining_distance, current_time, current_fuel, current_speed_kmh, time_multiplier, current_location)

        current_icao = icao
        menu_on = True

if __name__ == '__main__':
    main_program()