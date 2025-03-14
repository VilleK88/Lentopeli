from dotenv import load_dotenv # Ladataan ympäristömuuttujat .env-tiedostosta
import os # Käyttöjärjestelmän kanssa työskentelyyn
import requests # HTTP-pyyntöjen tekemiseen
import time # Aikaleiman käsittelyyn
import threading # Monisäikeisyyteen liittyvät toiminno

# Alustetaan muuttujat
API_KEY = None # API-avaimen tallennus
CITY = "Helsinki" # Oletuskaupunki, jota voidaan käyttää, jos koordinaatit puuttuvat
BASE_URL = "https://api.openweathermap.org/data/2.5/weather" # OpenWeatherMapin perus-URL
url = None # URL-rakenne, määritetään haettaessa säätä
current_weather = None # Viimeisimmän säädatan tallennus
last_weather_update = 0 # Aikaleima viimeisimmälle sääpäivitykselle

# Funktio sään hakemiseen annetuille koordinaateille
# force_update=True ohittaa välimuistin ja hakee uuden datan
def get_weather(lat, lon, force_update=False):
    global current_weather, last_weather_update

    # Ladataan ympäristömuuttujat, kuten API-avain
    load_dotenv()
    API_KEY = os.getenv("OPENWEATHER_API_KEY")

    # Tarkistetaan, että API-avain on olemassa
    if not API_KEY:
        return None # Palautetaan None, jos API-avainta ei löydy

    # Tarkistetaan, että annetut koordinaatit eivät ole tyhjiä
    if lat is None or lon is None:
        return None

    # Tarkistetaan, onko viimeisimmästä päivityksestä kulunut alle 3 sekuntia
    if not force_update and time.time() - last_weather_update < 3:
        return current_weather

    # Sisäfunktio sään hakemiseen API:sta
    def fetch_weather():
        global current_weather, last_weather_update

        url = f"{BASE_URL}?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=fi"

        # Suoritetaan HTTP GET -pyyntö säädatan hakemiseksi
        response = requests.get(url, timeout=2)

        # Tarkistetaan, onnistuiko pyyntö
        if response.status_code == 200:
            data = response.json() # Muutetaan vastaus JSON-muotoon

            # Haetaan tarvittavat sääparametrit vastauksesta
            weather_condition = data["weather"][0]["description"].capitalize()
            temp = data["main"]["temp"]
            wind_speed = data["wind"]["speed"]

            # Tallennetaan nykyinen sää
            current_weather = {
                "weather": weather_condition,
                "temp": temp,
                "wind": wind_speed
            }
            # Päivitetään aika, jolloin viimeksi haettiin säätä
            last_weather_update = time.time()
        else:
            print(f"Virhe API-kutsussa! Statuskoodi: {response.status_code}, Viesti: {response.text}")
            return None

    # Käynnistetään fetch_weather säikeessä, jotta pyyntö ei estä pääohjelman suoritusta
    threading.Thread(target=fetch_weather, daemon=True).start()

    return current_weather # Palautetaan viimeisin saatavilla oleva sää