from geopy.distance import geodesic
from db import get_airport_coords
def calculate_distance_between_airports(icao1, icao2):
    koord1 = icao1[2], icao1[3]
    koord2 = icao2[2], icao2[3]
    return geodesic(koord1, koord2).kilometers
def get_valid_icao(prompt):
    while True:
        icao = input(prompt).strip().upper()
        airport = get_airport_coords(icao)
        if airport:
            return airport
        print(f"Virhe: ICAO-koodia '{icao}' ei löytynyt. Yritä uudelleen.")