from loops import flight, user
from routes import server
from datetime import datetime
from database.db import get_columns_and_tables, get_airport_coords

# Pelin muuttujat
time_multiplier = 800 # Pelin nopeuden määritys (mitä suurempi arvo, sitä nopeammin aika kuluu)
remaining_distance = None # Jäljellä oleva etäisyys määränpäähän
current_time = None # Nykyinen peliaika
icao = None # lentokenttä jolle lennetään

# Käynnistää pelin ja alustaa tarvittavat asetukset
def start():
    global remaining_distance, current_time

    # Tarkistetaan ja luodaan tarvittavat tietokantataulukot ja sarakkeet
    get_columns_and_tables()

    # Käynnistetään päävalikko, jossa käyttäjä voi valita pelaajan tai luoda uuden
    server.start_server()
    user.main_menu()

    # Alustetaan peliaika
    current_time = datetime.now()
    print("current_time:", current_time)
    flight.pub_current_time = current_time
    print("flight current_time:", flight.pub_current_time)

    # Haetaan kirjautuneen käyttäjän lähtölentoasema
    starting_airport = user.initialize_starting_airport()

    # Haetaan lähtölentoaseman koordinaatit tietokannasta
    airport = get_airport_coords(starting_airport)

    return airport

# Pääohjelman silmukka, joka pyörittää pelin kulkua
def main_program():
    global remaining_distance, current_time, time_multiplier, icao

    # Käynnistetään peli ja saadaan lähtölentoaseman tiedot sekä Pygame-ikkuna
    current_icao = start()
    flight.current_location = current_icao[2], current_icao[3]

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
                flight.process_arrived_at_airport(current_icao)
        else:
            remaining_distance = 0 # Alustetaan etäisyys nollaksi, jos ei ole määritetty

        # Käynnistetään pelin sisäinen valikko, jos se on aktiivinen
        while menu_on:
            menu_on, icao = user.ingame_menu()

        # Tarkistetaan, keskeytyikö lento ennen määränpäätä
        remaining_distance = flight.was_flight_interrupted(remaining_distance, current_icao, icao)

        # Käynnistetään lentosilmukka ja päivitetään tiedot
        flight.stop_flight = False
        remaining_distance, current_time = flight.flight_loop(icao, remaining_distance, current_time, time_multiplier)

        # Päivitetään nykyinen lentoasema ja asetetaan valikko takaisin aktiiviseksi
        current_icao = icao
        user.current_icao = current_icao[1]
        user.airport_name = current_icao[0]
        user.ingame_menu_active = True
        menu_on = True
        flight.in_flight = False

if __name__ == '__main__':
    main_program()