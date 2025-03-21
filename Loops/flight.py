import pygame
import time
from datetime import timedelta
from geopy.distance import geodesic
from Routes import server
from Utils.utils import wipe_pygame_screen, update_pygame_screen, draw_centered_list, calculate_distance, calculate_distance_between_airports, draw_arrived_airport

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

        """Tähän lisätään process_fligh-funktio"""

        # Polttoaineen loppumisen tarkistus
        if current_fuel <= 0:
            remaining_distance = 0
            break

    return remaining_distance, current_time, current_location

# Päivittää sään ajastuksen
"""def weather_timer_flight(weather, last_weather_update):
    if time.time() - last_weather_update >= 2.5:
        new_weather = get_weather(new_lat, new_lon)
        if new_weather:
            weather = new_weather
            last_weather_update = time.time()
    return weather, last_weather_update"""

# Päivittää sään
"""def update_weather_on_flight(weather):
    global current_speed_kmh, turbulence_warning

    if weather is None:
        weather = {"weather": "Tuntematon", "temp": 0, "wind": 0}
        turbulence_warning = ""

    if weather["wind"] > 15:
        current_speed_kmh = max_speed_kmh * 0.8
        turbulence_warning = ", Kova tuuli!"
    else:
        current_speed_kmh = max_speed_kmh
        turbulence_warning = ""

    return weather, turbulence_warning"""

# Päivittää info tekstin
def update_info_text(current_time, weather, turbulence_warning, remaining_distance, current_speed_kmh, current_fuel, new_lat, new_lon, screen, font):
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
    draw_centered_list(screen, font, 30, info_text)
    update_pygame_screen()

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

def process_arrived_at_airport(current_icao1, current_icao2, screen, font):
    draw_arrived_airport(current_icao1, current_icao2, screen, 165, font)
    # Kutsutaan tässä customers.py lennonloppumis-funktiota.