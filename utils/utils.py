from geopy.distance import geodesic
from database.db import connect_db
from loops import user

# Laskee kahden lentokentän välisen etäisyyden ICAO-koodien perusteella
def calculate_distance_between_airports(icao1, icao2):
    koord1 = icao1[2], icao1[3]
    koord2 = icao2[2], icao2[3]
    return geodesic(koord1, koord2).kilometers

# Laskee etäisyyden nykyisen sijainnin ja kohdelentokentän välillä
def calculate_distance(current_location, icao2):
    koord1 = current_location[0], current_location[1]
    koord2 = icao2[2], icao2[3]
    return geodesic(koord1, koord2).kilometers

def get_airports(lat, lon):
    airports_list = []
    max_distance = 2000000 # metres
    current_coords = lat, lon

    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT ident, type, name, latitude_deg, longitude_deg FROM airport WHERE type IN ('large_airport', 'medium_airport')")
        airports = cursor.fetchall()

        for ident, type, name, lat2, lon2 in airports:
            distance = geodesic(current_coords, (lat2, lon2)).meters
            if distance <= max_distance and ident != user.current_icao and (type == 'large_airport' or type == 'medium_airport'):
                airports_list.append({
                    "ident": ident,
                    "name": name,
                    "distance": distance,
                    "latitude_deg": lat2,
                    "longitude_deg": lon2
                })

        conn.close()
        return airports_list