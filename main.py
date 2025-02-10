import sys
import threading
import time
import keyboard
from datetime import datetime, timedelta
from geopy.distance import geodesic
from utils import calculate_distance_between_airports, calculate_distance ,get_valid_icao
from weather import generate_random_weather
# Lentokoneen tiedot
remaining_distance = 0
max_speed_kmh = 780
current_speed_kmh = 0
fuel_capacity = 25941
current_fuel = 0
fuel_per_km = 2.6
time_multiplier = 250 # tämä muuttuja määrittää pelin nopeuden
current_time = None
current_location = None # Latitude & Longitude tallennetaan tähän
stop_flight = False
on_flight = False
def keyboard_listener(): # Kuuntelee näppäimistön syötettä taustalla
    global stop_flight, on_flight
    while True:
        if keyboard.is_pressed("1") and on_flight:
            stop_flight = True
            print("\n🔄 Kurssin muutos käynnistetty! Uusi määränpää valittava.")
            break
def start():
    global remaining_distance, current_fuel, current_time, current_speed_kmh,current_location, on_flight
    current_time = datetime.now()
    current_fuel = fuel_capacity
    current_speed_kmh = max_speed_kmh
    icao1 = get_valid_icao("1. ICAO-koodi: ")
    icao2 = get_valid_icao("2. ICAO-koodi: ")
    remaining_distance = calculate_distance_between_airports(icao1, icao2)
    print(f"\n✈️ Lähtö: {icao1[0]} {icao1[1]} ({icao1[2]:.5f}, {icao1[3]:.5f} |"
          f"\nMääränpää: {icao2[0]} {icao2[1]} ({icao2[2]:.5f}, {icao2[3]} |"
          f"\nEtäisyys: {remaining_distance:.2f} km")
    keyboard_thread = threading.Thread(target=keyboard_listener, daemon=True)
    keyboard_thread.start()
    t1 = threading.Thread(target=flight_loop, daemon=True, args=((icao1[2], icao1[3]), (icao2[2], icao2[3])))
    on_flight = True
    t1.start() # flight_loop käynnistyy tässä
    t1.join() # join -metodi varmistaa, että pääohjelma ei siirry seuraavaan osaan, ennen kuin update_loop on suorittanut loppuun
    if remaining_distance <= 0:
        print(f"\nSaavuit {icao2[0]} {icao2[1]}")
    else:
        print("\nMatka jäi kesken.")
    return icao2
def flight_loop(start_coords, end_coords):
    global remaining_distance, current_fuel, current_time, current_speed_kmh, current_location, stop_flight
    print("\n📍 Paina '1' muuttaakseksi kurssia tai odota...\n")
    lat1, lon1 = start_coords
    lat2, lon2 = end_coords
    new_lat = lat1
    new_lon = lon1
    total_distance = geodesic(start_coords, end_coords).kilometers
    if total_distance == 0:
        total_distance = 1
    while remaining_distance > 0:
        time.sleep(1) # loopin nopeus
        if stop_flight: # Tallennetaan nykyinen sijainti ja keskeytetään lento
            current_location = (new_lat, new_lon)
            print(f"Current location: {current_location}")
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
        # Päivitetään sää ja muutetaan lentonopeutta tarvittaessa
        weather = generate_random_weather()
        turbulence_warning = ""
        if weather["wind"] > 15:
            current_speed_kmh = max_speed_kmh * 0.8
            turbulence_warning = "⚠️ Kova tuuli!"
        else:
            current_speed_kmh = max_speed_kmh
        # Päivitetään sama riivi terminaalissa, eikä lisätä uutta riviä
        sys.stdout.write(f"\r🌤️ {weather['weather']} | 💨 {weather['wind']:.2f} m/s | "
                         f"⏳ {current_time.strftime('%H:%M')} | "
                         f"✈️ {remaining_distance:.2f} km |"
                         f"⚡ {current_speed_kmh:.2f} km/h | "
                         f"⛽ {current_fuel:.2f} L {turbulence_warning } |")
        sys.stdout.flush() # varmistetaan, että rivi päivittyy heti
        if current_fuel <= 0: # Polttoaineen loppumisen tarkistus
            print("\n⛽ Polttoaine loppui! Kone ei voi jatkaa matkaa.")
            remaining_distance = 0
            break
def main_program():
    global remaining_distance, stop_flight, current_location, on_flight
    current_icao = start()
    while True:
        keyboard.clear_all_hotkeys()
        on_flight = False
        icao = get_valid_icao("ICAO-koodi: ")
        if remaining_distance <= 0:
            remaining_distance = calculate_distance_between_airports(current_icao, icao)
            print(f"Lentoaseman {current_icao[0]} {current_icao[1]} etäisyys {icao[0]} {icao[1]} on {remaining_distance:.2f} kilometriä")
        else:
            remaining_distance = calculate_distance(current_location, icao)
            print(f"Nykyisen sijaintisi {current_location[0]} {current_location[1]} etäisyys {icao[0]} {icao[1]} on {remaining_distance:.2f} kilometriä")
        keyboard_thread = threading.Thread(target=keyboard_listener, daemon=True)
        keyboard_thread.start()
        t1 = threading.Thread(target=flight_loop, daemon=True, args=(current_location, (icao[2], icao[3])))
        on_flight = True
        t1.start() # flight_loop käynnistyy tässä
        t1.join() # join -metodi varmistaa, että pääohjelma ei siirry seuraavaan osaan, ennen kuin update_loop on suorittanut loppuun
        if remaining_distance <= 0:
            print(f"\nSaavuit {icao[0]} {icao[1]}")
        current_icao = icao
if __name__ == '__main__':
    main_program()