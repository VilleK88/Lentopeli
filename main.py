from loops import flight, user
from routes import server
from datetime import datetime
from database.db import get_columns_and_tables, get_airport_coords

# Pelin nopeuden määritys (mitä suurempi arvo, sitä nopeammin aika kuluu)
time_multiplier = 100

# Pelin muuttujat
remaining_distance = None # Jäljellä oleva etäisyys määränpäähän
current_time = None # Nykyinen peliaika
current_location = 60.3172, 24.9633 # Nykyinen sijainti (latitude, longitude)
icao = None # lentokenttä jolle lennetään
#menu_on = True

# Pygame-ikkunan asetukset
screen = None # Pygame-ikkunaobjekti
font = None # Pygame-kirjasinobjekti

# Käynnistää pelin ja alustaa tarvittavat asetukset
def start():
    global remaining_distance, current_time, current_location, screen, font

    # Tarkistetaan ja luodaan tarvittavat tietokantataulukot ja sarakkeet
    get_columns_and_tables()

    # Käynnistetään päävalikko, jossa käyttäjä voi valita pelaajan tai luoda uuden
    server.start_server()
    user.main_menu()

    # Alustetaan peliaika
    current_time = datetime.now()

    # Haetaan kirjautuneen käyttäjän lähtölentoasema
    starting_airport = user.initialize_starting_airport()

    # Haetaan lähtölentoaseman koordinaatit tietokannasta
    airport = get_airport_coords(starting_airport)

    return airport

# Pääohjelman silmukka, joka pyörittää pelin kulkua
def main_program():
    global remaining_distance, current_location, current_time, time_multiplier, screen, font, icao#, menu_on

    # Käynnistetään peli ja saadaan lähtölentoaseman tiedot sekä Pygame-ikkuna
    current_icao = start()
    current_location = current_icao[2], current_icao[3]

    # Käynnistetään palvelin ja asetetaan sen aloituskoordinaatit
    server.starting_coordinates(current_icao[2], current_icao[3])

    menu_on = True # Määrittää, onko valikko aktiivinen

    # Pääpelisilmukka
    while True:

        # Päivitetään palvelimelle pelaajan sijainti
        server.update_server(flight.new_lat, flight.new_lon, False)

        # Tarkistetaan, onko pelaaja saapunut määränpäähän
        if remaining_distance != None:
            if remaining_distance <= 0:
                print(f"Saavuit {current_icao[0]}, ICAO: {current_icao[1]}.")
        else:
            remaining_distance = 0 # Alustetaan etäisyys nollaksi, jos ei ole määritetty

        # Käynnistetään pelin sisäinen valikko, jos se on aktiivinen
        while menu_on:
            menu_on, icao = user.ingame_menu(current_icao[1], remaining_distance)
        print(f"menu_on: ", menu_on)

        print(f"🔍 Debug: ennen asetusta, main.icao = {icao}")

        # Pyydetään käyttäjää syöttämään seuraavan lentoaseman ICAO-koodi
        #icao = get_valid_icao(screen, font, "ICAO-koodi: ")

        # Tarkistetaan, keskeytyikö lento ennen määränpäätä
        remaining_distance = flight.was_flight_interrupted(remaining_distance, current_icao, icao, current_location)

        # Käynnistetään lentosilmukka ja päivitetään tiedot
        flight.stop_flight = False
        print(f"remaining distance main: {remaining_distance}")
        remaining_distance, current_time, current_location = flight.flight_loop(current_location, icao, remaining_distance, current_time, time_multiplier)

        # Päivitetään nykyinen lentoasema ja asetetaan valikko takaisin aktiiviseksi
        current_icao = icao
        user.current_icao = current_icao[1]
        user.ingame_menu_active = True
        menu_on = True

def update_target_icao(target_icao):
    global icao
    icao = target_icao


if __name__ == '__main__':
    main_program()