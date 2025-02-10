import msvcrt
import sys
import threading
import time
import keyboard
from datetime import datetime, timedelta
from utils import calculate_distance_between_airports, get_valid_icao
from weather import generate_random_weather
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
def start():
    global remaining_distance, current_fuel, current_time, current_speed_kmh
    current_time = datetime.now()
    current_fuel = fuel_capacity
    current_speed_kmh = max_speed_kmh
    icao1 = get_valid_icao("1. ICAO-koodi: ")
    icao2 = get_valid_icao("2. ICAO-koodi: ")
    remaining_distance = calculate_distance_between_airports(icao1, icao2)
    print(f"Lentoaseman {icao1[0]} {icao1[1]} etäisyys {icao2[0]} {icao2[1]} on {remaining_distance:.2f} kilometriä")
    t1 = threading.Thread(target=flight_loop, daemon=True)
    t1.start()
    t1.join()
    print(f"Saavuit {icao2[0]} {icao2[1]}")
    return icao2
def flight_loop():
    global remaining_distance, current_fuel, current_time, current_speed_kmh, current_location
    keyboard_thread = threading.Thread(target=keyboard_listener, daemon=True)
    keyboard_thread.start()
    print("\n📍 Paina '1' muuttaakseksi kurssia tai odota...\n")
    while remaining_distance > 0:
        time.sleep(1) # loopin nopeus
        if stop_flight:
            # Tallennetaan nykyinen sijainti ja keskeytetään lento
            current_location = (current_time, remaining_distance)
            print("\n🔄 Kurssin muutos käynnistetty! Uusi määränpää valittava.")
            break
        # Päivitetään matka, polttoaine ja aika
        remaining_distance -= (current_speed_kmh * time_multiplier / 3600)
        if remaining_distance < 0:
            remaining_distance = 0
        current_fuel -= (fuel_per_km * (current_speed_kmh * time_multiplier / 3600))
        current_time += timedelta(seconds=time_multiplier)
        # Päivitetään sää ja muutetaan lentonopeutta tarvittaessa
        weather = generate_random_weather()
        turbulence_warning = "" # alustetaan tyhjäksi
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
        #sys.stdout.write("\n Paina '1' Muuttaaksesi kurssia")
        sys.stdout.flush() # varmistetaan, että rivi päivittyy heti
        if current_fuel <= 0:
            print("\n⛽ Polttoaine loppui! Kone ei voi jatkaa matkaa.")
            remaining_distance = 0
            break
def keyboard_listener():
    # Kuuntelee näppäimistön syötettä taustalla
    global stop_flight
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch().decode("utf-8")
            if key == "1":
                stop_flight = True
                break
def main_program():
    global remaining_distance, stop_flight, current_location
    current_icao = start()
    while True:
        icao = get_valid_icao("ICAO-koodi: ")
        remaining_distance = calculate_distance_between_airports(current_icao, icao)
        print(f"Lentoaseman {current_icao[0]} {current_icao[1]} etäisyys {icao[0]} {icao[1]} on {remaining_distance:.2f} kilometriä")
        stop_flight = False
        t1 = threading.Thread(target=flight_loop, daemon=True)
        t1.start() # update_loop käynnistyy tässä
        t1.join() # join -metodi varmistaa, että pääohjelma ei siirry seuraavaan osaan, ennen kuin update_loop on suorittanut loppuun
        print(f"Saavuit {icao[0]} {icao[1]}")
        current_icao = icao
if __name__ == '__main__':
    main_program()