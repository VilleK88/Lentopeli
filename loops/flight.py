import pygame
import time
from datetime import timedelta
from geopy.distance import geodesic
from routes import server
from utils.utils import calculate_distance, calculate_distance_between_airports

# Lentokoneen tiedot
max_speed_kmh = 780
current_speed_kmh = 0
fuel_capacity = 25941
current_fuel = 0
fuel_per_km = 2.6
stop_flight = False
zoom = 10
new_lat = 0
new_lon = 0
turbulence_warning = ""

def flight_loop(current_location, icao, remaining_distance, current_time, time_multiplier):

    global stop_flight, zoom, new_lat, new_lon, turbulence_warning, current_speed_kmh, current_fuel

    print("\n📍 Paina '1' muuttaakseksi kurssia tai odota...\n")

    # Alustetaan lähtö ja meno koordinaatit
    start_coords = current_location
    lat1, lon1 = start_coords
    end_coords = icao[2], icao[3]
    lat2, lon2 = end_coords
    new_lat, new_lon = lat1, lon1

    # Lasketaan kokonaismatka
    total_distance = geodesic(start_coords, end_coords).kilometers
    if total_distance == 0:
        total_distance = 1

    # Alustetaan sää
    #weather = get_weather(lat1, lon1)
    #weather, turbulence_warning = update_weather_on_flight(weather)
    #last_weather_update = time.time()

    # Alustetaan nopeus
    current_speed_kmh = max_speed_kmh

    while remaining_distance > 0:
        time.sleep(1) # Loopin nopeus
        print(f"Remaining distance: {remaining_distance}")

        # Keskeytä lento painamalla '1'
        #interrupt_flight()

        if stop_flight:
            # Tallennetaan nykyinen sijainti ja keskeytetään lento
            current_location = (new_lat, new_lon)
            stop_flight = False
            break

        # Päivitetään matka, polttoaine ja aika
        remaining_distance -= (current_speed_kmh * time_multiplier / 3600)
        if remaining_distance < 0:
            remaining_distance = 0
        current_fuel -= (fuel_per_km * (current_speed_kmh * time_multiplier / 3600))
        current_time += timedelta(seconds=time_multiplier)

        # Lasketaan uusi sijainti koordinaateissa
        progress = 1 - (remaining_distance / total_distance)
        new_lat = lat1 + (lat2 - lat1) * progress
        new_lon = lon1 + (lon2 -lon1) * progress
        current_location = (new_lat, new_lon)

        # Päivitä karttakuva
        server.update_server(new_lat, new_lon, True)

        """Tähän lisätään process_customers-funktio"""

        # Polttoaineen loppumisen tarkistus
        if current_fuel <= 0:
            remaining_distance = 0
            break

    return remaining_distance, current_time, current_location

# Pysäyttää lennon painamalla '1'
def interrupt_flight():
    global stop_flight
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                stop_flight = True

def was_flight_interrupted(remaining_distance, current_icao, icao, current_location):
    if remaining_distance <= 0:
        remaining_distance = calculate_distance_between_airports(current_icao, icao)
    else:
        remaining_distance = calculate_distance(current_location, icao)
    return remaining_distance

def process_arrived_at_airport(current_icao):
    # Tarkistetaan mm. onko asiakas oikealla lentoasemalle. Ottaa tästä parametrin vastaan.
    # Kutsutaan tässä customers.py lennonloppumis-funktiota.
    return