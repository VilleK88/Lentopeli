import pygame
import time
from datetime import timedelta
from geopy.distance import geodesic
from routes import server
from utils.utils import calculate_distance, calculate_distance_between_airports
from loops.customers import CustomerManager

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
    # weather = get_weather(lat1, lon1)
    # weather, turbulence_warning = update_weather_on_flight(weather)
    # last_weather_update = time.time()

    # Alustetaan nopeus
    current_speed_kmh = max_speed_kmh

    # Alustetaan CustomerManager
    customer_manager = CustomerManager()

    while remaining_distance > 0:
        time.sleep(1)  # Loopin nopeus
        print(f"Remaining distance: {remaining_distance}")

        # Keskeytä lento painamalla '1'
        # interrupt_flight()

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
        new_lon = lon1 + (lon2 - lon1) * progress
        current_location = (new_lat, new_lon)

        # Päivitä karttakuva
        server.update_server(new_lat, new_lon, True)

        # Kutsutaan process_customers-funktiota
        if customer_manager.current_customer:
            customer_manager.adjust_mood_based_on_product("example_product_name")  # Esimerkki, voit korvata tuotteen nimellä
            print(f"[DEBUG] Asiakkaan mieliala: {customer_manager.get_customer_mood()}")

        # Polttoaineen loppumisen tarkistus
        if current_fuel <= 0:
            remaining_distance = 0
            break

    return remaining_distance, current_time, current_location


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


def process_arrived_at_airport(arrived_icao, customer_manager, economy_manager):
    """
    Käsittelee asiakkaan saapumisen lentokentälle

    Args:
        arrived_icao (str): Saapumiskentän ICAO-koodi
        customer_manager (CustomerManager): Asiakkaiden hallintainstanssi
        economy_manager (EconomyManager): Talouden hallintainstanssi

    Returns:
        bool: True jos asiakas saapui onnistuneesti määränpäähänsä, muuten False
    """
    # Varmistetaan että ICAO on oikeassa muodossa
    arrived_icao = arrived_icao.strip().upper()

    # Haetaan nykyinen asiakas
    current_customer = customer_manager.current_customer

    if not current_customer:
        print("[DEBUG] Ei asiakasta valittuna!")
        return False

    customer_destination = current_customer.get("destination", "").strip().upper()
    print(f"[DEBUG] Asiakas {current_customer.get('name')} -> määränpää: {customer_destination}")
    print(f"[DEBUG] Saavuttu kentälle: {arrived_icao}")

    # Tarkistetaan, onko asiakas saapunut oikealle lentokentälle
    if customer_destination == arrived_icao:
        print(f"[DEBUG] Asiakas {current_customer.get('name')} saapui määränpäähän {arrived_icao}.")

        # Haetaan asiakkaan mieliala
        mood = customer_manager.get_customer_mood()

        # Kutsutaan talousmanageria maksun käsittelemiseksi ja mainetta säädetään
        payment = economy_manager.process_customer_arrival(current_customer, mood)

        # Nollataan asiakas, jotta hän poistuu koneesta
        customer_manager.reset_customer()

        print(f"[DEBUG] Maksu suoritettu, asiakas maksoi {payment}€.")
        return True
    else:
        print(f"[DEBUG] Asiakas {current_customer.get('name')} ei saapunut määränpäähän.")
        print(f"[DEBUG] Odottaa kenttää: {customer_destination}, saapui kentälle: {arrived_icao}")
        return False