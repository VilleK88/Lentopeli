import time
import pygame
from Routes import server
from datetime import datetime, timedelta
from geopy.distance import geodesic
from Utils.utils import calculate_distance_between_airports, calculate_distance, get_valid_icao
from Utils.weather import generate_random_weather

# Lentokoneen tiedot
remaining_distance = 0
max_speed_kmh = 780
current_speed_kmh = 0
fuel_capacity = 25941
current_fuel = 0
fuel_per_km = 2.6
time_multiplier = 200 # tämä muuttuja määrittää pelin nopeuden
current_time = None
current_location = None # Latitude & Longitude tallennetaan tähän
stop_flight = False
on_flight = False
keyboard_hook = None
zoom = 12

def start(screen, font):
    global remaining_distance, current_fuel, current_time, current_speed_kmh,current_location, on_flight, zoom

    current_time = datetime.now()
    current_fuel = fuel_capacity
    current_speed_kmh = max_speed_kmh

    # tänne huolto koodi

    icao1 = get_valid_icao(screen, font, "1. ICAO-koodi: ")
    icao2 = get_valid_icao(screen, font, "2. ICAO-koodi: ")
    ##icao1 = get_valid_icao("1. ICAO-koodi: ")
    ##icao2 = get_valid_icao("2. ICAO-koodi: ")

    remaining_distance = calculate_distance_between_airports(icao1, icao2)

    print(f"\n✈️ Lähtö: {icao1[0]} {icao1[1]} ({icao1[2]:.5f}, {icao1[3]:.5f} |"
          f"\nMääränpää: {icao2[0]} {icao2[1]} ({icao2[2]:.5f}, {icao2[3]} |"
          f"\nEtäisyys: {remaining_distance:.2f} km")

    server.start_server(icao1[2], icao1[3], zoom)

    on_flight = True
    flight_loop(screen, font,(icao1[2], icao1[3]), (icao2[2], icao2[3]))

    if remaining_distance <= 0:
        print(f"\nSaavuit {icao2[0]} {icao2[1]}")
    else:
        print("\nMatka jäi kesken.")

    return icao2, screen

def flight_loop(screen, font, start_coords, end_coords):
    """ Lentopelin pääsilmukka 'curses' -kirjastolla """
    global remaining_distance, current_fuel, current_time, current_speed_kmh, current_location, stop_flight, zoom

    print("\n📍 Paina '1' muuttaakseksi kurssia tai odota...\n")

    lat1, lon1 = start_coords
    lat2, lon2 = end_coords

    new_lat, new_lon = lat1, lon1
    total_distance = geodesic(start_coords, end_coords).kilometers
    if total_distance == 0:
        total_distance = 1

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
            print("\n🔄 Kurssin muutos käynnistetty! Uusi määränpää valittava.")
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
        server.update_server(new_lat, new_lon, zoom)


        # Päivitetään sää ja muutetaan lentonopeutta tarvittaessa
        weather = generate_random_weather()
        turbulence_warning = ""
        if weather["wind"] > 15:
            current_speed_kmh = max_speed_kmh * 0.8
            turbulence_warning = ", Kova tuuli!"
        else:
            current_speed_kmh = max_speed_kmh

        screen.fill((0, 0, 0))
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

        pygame.display.flip()

        if current_fuel <= 0: # Polttoaineen loppumisen tarkistus
            print("\n⛽ Polttoaine loppui! Kone ei voi jatkaa matkaa.")
            remaining_distance = 0
            break

def main_program():
    global remaining_distance, stop_flight, current_location, on_flight

    pygame.init()
    screen = pygame.display.set_mode((600, 400))
    pygame.display.set_caption("Lentopeli")
    font = pygame.font.Font(None, 30)

    current_icao, screen = start(screen, font)

    # tänne huolto koodi

    while True:
        on_flight = False

        icao = get_valid_icao(screen, font, "ICAO-koodi: ")
        #icao = get_valid_icao("ICAO-koodi: ")

        if remaining_distance <= 0:
            remaining_distance = calculate_distance_between_airports(current_icao, icao)
            print(f"Lentoaseman {current_icao[0]} {current_icao[1]} etäisyys {icao[0]} {icao[1]} on {remaining_distance:.2f} kilometriä")
        else:
            remaining_distance = calculate_distance(current_location, icao)
            print(f"Nykyisen sijaintisi {current_location[0]} {current_location[1]} etäisyys {icao[0]} {icao[1]} on {remaining_distance:.2f} kilometriä")

        on_flight = True
        stop_flight = False
        flight_loop(screen, font, current_location, (icao[2], icao[3]))

        if remaining_distance <= 0:
            print(f"\nSaavuit {icao[0]} {icao[1]}")
        current_icao = icao

if __name__ == '__main__':
    main_program()