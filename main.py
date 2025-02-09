import threading
import time
from datetime import datetime, timedelta
from utils import calculate_distance_between_airports, get_valid_icao
distance_traveled = 0
speed_kmh = 780
fuel_capacity = 25941
current_fuel = 0
fuel_per_km = 2.6
time_multiplier = 200 # tämä muuttuja määrittää lentokoneen nopeuden
current_time = 0
def start():
    global distance_traveled, current_fuel, current_time
    current_time = datetime.now()
    current_fuel = fuel_capacity
    icao1 = get_valid_icao("1. ICAO-koodi: ")
    icao2 = get_valid_icao("2. ICAO-koodi: ")
    distance_traveled = calculate_distance_between_airports(icao1, icao2)
    print(f"Lentoaseman {icao1[0]} {icao1[1]} etäisyys {icao2[0]} {icao2[1]} on {distance_traveled:.2f} kilometriä")
    t1 = threading.Thread(target=flight_loop, daemon=True)
    t1.start()
    t1.join()
    print(f"Saavuit {icao2[0]} {icao2[1]}")
    return icao2
def flight_loop():
    global distance_traveled, current_fuel, current_time
    while distance_traveled > 0:
        time.sleep(1)
        distance_traveled -= (speed_kmh * time_multiplier / 3600)
        if distance_traveled < 0:
            distance_traveled = 0
        current_fuel -= (fuel_per_km * (speed_kmh * time_multiplier / 3600))
        current_time += timedelta(seconds=time_multiplier)
        print(f"distance: {distance_traveled:.2f} km, time: {current_time.strftime("%H:%M")} fuel: {current_fuel:.2f}")
def main_program():
    global distance_traveled
    current_icao = start()
    while True:
        icao = get_valid_icao("ICAO-koodi: ")
        distance_traveled = calculate_distance_between_airports(current_icao, icao)
        print(f"Lentoaseman {current_icao[0]} {current_icao[1]} etäisyys {icao[0]} {icao[1]} on {distance_traveled:.2f} kilometriä")
        t1 = threading.Thread(target=flight_loop, daemon=True)
        t1.start() # update_loop käynnistyy tässä
        t1.join() # join -metodi varmistaa, että pääohjelma ei siirry seuraavaan osaan, ennen kuin update_loop on suorittanut loppuun
        print(f"Saavuit {icao[0]} {icao[1]}")
        current_icao = icao
if __name__ == '__main__':
    main_program()