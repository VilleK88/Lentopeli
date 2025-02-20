import time
import pygame
import Utils.utils
from Loops import flight
from Routes import server
from datetime import datetime
from Utils.utils import calculate_distance_between_airports, calculate_distance, get_valid_icao, draw_arrived_airport, initialize_pygame_screen
from Loops.user import check_if_logged_in_exists

# Lentokoneen tiedot
remaining_distance = 0
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

# pygame asetukset
screen = None
font = None

def start():
    global remaining_distance, current_fuel, current_time, current_speed_kmh,current_location, on_flight, zoom, screen, font

    screen, font = initialize_pygame_screen()

    # tarkista onko logged_in sarake olemassa tietokanssa
    onko = check_if_logged_in_exists()
    if not onko:
        print("Ei ole")
        Utils.utils.draw_text(screen, "Ei ole", 20, 50, font)
    time.sleep(2)

    # Aika, polttoaine, nopeus ja zoom muuttujien alustus
    current_time = datetime.now()
    current_fuel = fuel_capacity
    current_speed_kmh = max_speed_kmh
    flight.zoom = zoom

    # tänne huolto koodi

    icao1 = get_valid_icao(screen, font, "1. ICAO-koodi: ")
    icao2 = get_valid_icao(screen, font, "2. ICAO-koodi: ")

    remaining_distance = calculate_distance_between_airports(icao1, icao2)

    server.starting_coordinates(icao1[2], icao1[3])
    server.start_server()

    on_flight = True
    remaining_distance, current_time, current_fuel, current_location = flight.flight_loop(screen, font,(icao1[2], icao1[3]), (icao2[2], icao2[3]), remaining_distance, current_time, current_fuel, current_speed_kmh, time_multiplier, current_location)

    return icao2, screen

def main_program():
    global remaining_distance, current_location, on_flight, current_time, current_fuel, current_speed_kmh, time_multiplier, screen, font

    current_icao, screen = start()

    # main loop
    while True:
        on_flight = False
        draw_arrived_airport(current_icao[0], current_icao[1], screen, 20, 50, font)
        time.sleep(2)

        # tänne huolto koodi

        icao = get_valid_icao(screen, font, "ICAO-koodi: ")

        if remaining_distance <= 0:
            remaining_distance = calculate_distance_between_airports(current_icao, icao)
            print(f"Lentoaseman {current_icao[0]} {current_icao[1]} etäisyys {icao[0]} {icao[1]} on {remaining_distance:.2f} kilometriä")
        else:
            remaining_distance = calculate_distance(current_location, icao)
            print(f"Nykyisen sijaintisi {current_location[0]} {current_location[1]} etäisyys {icao[0]} {icao[1]} on {remaining_distance:.2f} kilometriä")

        on_flight = True
        flight.stop_flight = False

        remaining_distance, current_time, current_fuel, current_location = flight.flight_loop(screen, font, current_location, (icao[2], icao[3]), remaining_distance, current_time, current_fuel, current_speed_kmh, time_multiplier, current_location)

        current_icao = icao

if __name__ == '__main__':
    main_program()