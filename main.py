import mysql.connector
import threading
import time
from geopy.distance import geodesic
from datetime import datetime, timedelta
done = False
update_distance = 0
speed_kmh = 780
time_multiplier = 70
db_config = {
    "host": "localhost",
    "user": "VK88",
    "password": "helppo",
    "database": "flight_game",
    "charset": "utf8mb4",
    "collation": "utf8mb4_unicode_ci"
}
def connect_db():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"Virhe yrittäessä yhdistää tietokantaan: {err}")
        return False
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
    global update_distance, done
    current_time = datetime.now()
    while update_distance > 0 and not done:
        time.sleep(1.2)
        update_distance -= (speed_kmh * time_multiplier / 3600)
        current_time += timedelta(seconds=time_multiplier)
        print(f"{update_distance:.2f} km, {current_time.strftime("%H:%M")}")
def main_program():
    global update_distance
    icao1 = input("1. ICAO-koodi: ").strip().upper()
    icao2 = input("2. ICAO-koodi: ").strip().upper()
    koord1 = get_airport(icao1)
    koord2 = get_airport(icao2)
    update_distance = calculate_distance(koord1, koord2)
    if not koord1 or not koord2:
        return
    print(f"Lentoaseman {koord1[0]} {icao1} etäisyys {koord2[0]} {icao2} on {update_distance:.2f} kilometriä")
    t1 = threading.Thread(target=update_loop, daemon=True)
    t1.start()
    t1.join()
if __name__ == '__main__':
    main_program()