import pygame
import time
from datetime import timedelta
from geopy.distance import geodesic

import Utils.weather
from Routes import server
from Utils.weather import get_weather
from Utils.utils import wipe_pygame_screen, update_pygame_screen

# Lentokoneen tiedot
remaining_distance = 0
max_speed_kmh = 780
current_speed_kmh = 0
fuel_capacity = 25941
current_fuel = 0
fuel_per_km = 2.6
time_multiplier = 60 # tämä muuttuja määrittää pelin nopeuden
current_time = None
current_location = None # Latitude & Longitude tallennetaan tähän
stop_flight = False
zoom = 10
new_lat = 0
new_lon = 0

def flight_loop(screen, font, start_coords, end_coords, remaining_distance, current_time, current_fuel, current_speed_kmh, time_multiplier, current_location):
    """ Lentopelin pääsilmukka 'curses' -kirjastolla """
    global stop_flight, zoom, new_lat, new_lon

    print("\n📍 Paina '1' muuttaakseksi kurssia tai odota...\n")

    lat1, lon1 = start_coords
    lat2, lon2 = end_coords

    new_lat, new_lon = lat1, lon1
    total_distance = geodesic(start_coords, end_coords).kilometers
    if total_distance == 0:
        total_distance = 1

    weather = get_weather(lat1, lon1)
    last_weather_update = time.time()

    while remaining_distance > 0:
        time.sleep(1) # loopin nopeus

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    stop_flight = True

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

        if time.time() - last_weather_update >= 3:
            new_weather = get_weather(new_lat, new_lon)
            if new_weather:
                weather = new_weather
                last_weather_update = time.time()

        # Päivitetään sää ja muutetaan lentonopeutta tarvittaessa
        if weather is None:
            weather = {"weather": "Tuntematon", "temp": 0, "wind": 0}
        turbulence_warning = ""
        if weather["wind"] > 15:
            current_speed_kmh = max_speed_kmh * 0.8
            turbulence_warning = ", Kova tuuli!"
        else:
            current_speed_kmh = max_speed_kmh

        wipe_pygame_screen(screen)
        info_text = [
            f"Aika: {current_time.strftime('%H:%M')}",
            f"Sää: {weather['weather']}, Tuuli: {weather['wind']:.2f} m/s {turbulence_warning}",
            f"Matkaa jäljellä: {remaining_distance:.2f} km",
            f"Nopeus: {current_speed_kmh:.2f} km/h",
            f"Polttoaine: {current_fuel:.2f} L",
            f"Sijainti: ({new_lat:.5f}, {new_lon:.5f})",
            f"Paina '1' muuttaaksesi kurssia."
        ]

        y_offset = 50
        for text in info_text:
            rendered_text = font.render(text, True, (255, 255, 255))
            screen.blit(rendered_text, (20, y_offset))
            y_offset += 30

        update_pygame_screen()

        if current_fuel <= 0: # Polttoaineen loppumisen tarkistus
            remaining_distance = 0
            break

    return remaining_distance, current_time, current_fuel, current_location