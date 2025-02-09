from geopy.distance import geodesic
def calculate_distance_between_airports(icao1, icao2):
    koord1 = icao1[1], icao1[2]
    koord2 = icao2[1], icao2[2]
    return geodesic(koord1, koord2).kilometers