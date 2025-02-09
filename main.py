import threading
import time
from geopy.distance import geodesic
from datetime import datetime, timedelta
from db import connect_db
done = False
update_distance = 0
current_distance = 0
speed_kmh = 780
fuel_capacity = 25941
current_fuel = 0
fuel_per_km = 2.6
time_multiplier = 200
def get_airport(icao):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        sql = "select name, latitude_deg, longitude_deg from airport where ident = %s"
        cursor.execute(sql, (icao,))
        result = cursor.fetchone()
        conn.close()
        return (result[0], result[1], result[2]) if result else None
    return False
def calculate_distance(icao1, icao2):
    koord1 = icao1[1], icao1[2]
    koord2 = icao2[1], icao2[2]
    return geodesic(koord1, koord2).kilometers
def update_loop():
    global update_distance, current_fuel, done
    current_time = datetime.now()
    while update_distance > 0 and not done:
        time.sleep(1)
        update_distance -= (speed_kmh * time_multiplier / 3600)
        current_fuel -= (fuel_per_km * (speed_kmh * time_multiplier / 3600))
        current_time += timedelta(seconds=time_multiplier)
        print(f"distance: {update_distance:.2f} km, time: {current_time.strftime("%H:%M")} fuel: {current_fuel:.2f}")
def start():
    global update_distance, current_fuel
    current_fuel = fuel_capacity
    icao1 = input("1. ICAO-koodi: ").strip().upper()
    icao2 = input("2. ICAO-koodi: ").strip().upper()
    koord1 = get_airport(icao1)
    koord2 = get_airport(icao2)
    if not koord1 or not koord2:
        return
    update_distance = calculate_distance(koord1, koord2)
    print(f"Lentoaseman {koord1[0]} {icao1} etäisyys {koord2[0]} {icao2} on {update_distance:.2f} kilometriä")
    t1 = threading.Thread(target=update_loop, daemon=True)
    t1.start()
    t1.join()
    print(f"Saavuit {koord2[0]} {icao2}")
    return icao2, koord2[0]
def main_program():
    current_icao, current_name = start()
    while True:
        icao = input("2. ICAO-koodi: ").strip().upper()
        koord1 = get_airport(current_icao)
        koord2 = get_airport(icao)
        if not koord1 or not koord2:
            return
        update_distance = calculate_distance(koord1, koord2)
        print(f"Update distance: {update_distance}")
        print(f"Lentoaseman {koord1[0]} {current_icao} etäisyys {koord2[0]} {icao} on {update_distance:.2f} kilometriä")
        t1 = threading.Thread(target=update_loop, daemon=True)
        t1.start()
        t1.join()
        print(f"Saavuit {koord2[0]} {icao}")
if __name__ == '__main__':
    main_program()