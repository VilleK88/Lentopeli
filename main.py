from Loops import flight, user
from Routes import server
from datetime import datetime
from Utils.utils import get_valid_icao, initialize_pygame_screen
from Database.db import get_columns_and_tables, get_airport_coords

# Pelin nopeuden määritys (mitä suurempi arvo, sitä nopeammin aika kuluu)
time_multiplier = 100

# Pelin muuttujat
remaining_distance = None # Jäljellä oleva etäisyys määränpäähän
current_time = None # Nykyinen peliaika
current_location = 60.3172, 24.9633 # Nykyinen sijainti (latitude, longitude)

# Pygame-ikkunan asetukset
screen = None # Pygame-ikkunaobjekti
font = None # Pygame-kirjasinobjekti

# Käynnistää pelin ja alustaa tarvittavat asetukset
def start():
    global remaining_distance, current_time, current_location, screen, font

    # Alustetaan pygame-ikkuna ja kirjasin
    screen, font = initialize_pygame_screen()

    # Tarkistetaan ja luodaan tarvittavat tietokantataulukot ja sarakkeet
    get_columns_and_tables()

    # Käynnistetään päävalikko, jossa käyttäjä voi valita pelaajan tai luoda uuden
    user.main_menu(screen, font)

    # Alustetaan peliaika
    current_time = datetime.now()

    # Haetaan kirjautuneen käyttäjän lähtölentoasema
    starting_airport = user.initialize_starting_airport()

    # Haetaan lähtölentoaseman koordinaatit tietokannasta
    airport = get_airport_coords(starting_airport)

    return airport, screen

# Pääohjelman silmukka, joka pyörittää pelin kulkua
def main_program():
    global remaining_distance, current_location, current_time, time_multiplier, screen, font

    # Käynnistetään peli ja saadaan lähtölentoaseman tiedot sekä Pygame-ikkuna
    current_icao, screen = start()
    current_location = current_icao[2], current_icao[3]

    # Käynnistetään palvelin ja asetetaan sen aloituskoordinaatit
    server.starting_coordinates(current_icao[2], current_icao[3])
    server.start_server()

    menu_on = True # Määrittää, onko valikko aktiivinen

    # Pääpelisilmukka
    while True:

        # Päivitetään palvelimelle pelaajan sijainti
        server.update_server(flight.new_lat, flight.new_lon, False)

        # Tarkistetaan, onko pelaaja saapunut määränpäähän
        if remaining_distance != None:
            if remaining_distance <= 0:
                flight.process_arrived_at_airport(current_icao[0], current_icao[1], screen, font)
        else:
            remaining_distance = 0 # Alustetaan etäisyys nollaksi, jos ei ole määritetty

        # Käynnistetään pelin sisäinen valikko, jos se on aktiivinen
        while menu_on:
            menu_on = user.ingame_menu(screen, font, current_icao[1], remaining_distance)

        # Pyydetään käyttäjää syöttämään seuraavan lentoaseman ICAO-koodi
        icao = get_valid_icao(screen, font, "ICAO-koodi: ")

        # Tarkistetaan, keskeytyikö lento ennen määränpäätä
        remaining_distance = flight.was_flight_interrupted(remaining_distance, current_icao, icao, current_location)

        # Käynnistetään lentosilmukka ja päivitetään tiedot
        flight.stop_flight = False
        remaining_distance, current_time, current_location = flight.flight_loop(screen, font, current_location, (icao[2], icao[3]), remaining_distance, current_time, time_multiplier, current_location)

        # Päivitetään nykyinen lentoasema ja asetetaan valikko takaisin aktiiviseksi
        current_icao = icao
        user.current_icao = current_icao[1]
        menu_on = True

if __name__ == '__main__':
    main_program()