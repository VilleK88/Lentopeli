from dotenv import load_dotenv
import os
import requests
import time
import threading
from Loops import flight

API_KEY = None
CITY = "Helsinki"
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
url = None
current_weather = None
last_weather_update = 0

# Käynnistää sään säikeen ja ottaa vastaan pelaajan sijainnin
def get_weather(lat, lon, force_update=False):
    global current_weather, last_weather_update

    load_dotenv()
    API_KEY = os.getenv("OPENWEATHER_API_KEY")

    if not API_KEY:
        return None
    if lat is None or lon is None:
        return None
    if not force_update and time.time() - last_weather_update < 3:
        return current_weather

    # Hakee sään
    def fetch_weather():
        global current_weather, last_weather_update
        url = f"{BASE_URL}?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=fi"
        if flight.on_flight:
            timer = 2
        else:
            timer = 5
        response = requests.get(url, timeout=timer)
        if response.status_code == 200:
            data = response.json()
            weather_condition = data["weather"][0]["description"].capitalize()
            temp = data["main"]["temp"]
            wind_speed = data["wind"]["speed"]
            current_weather = {
                "weather": weather_condition,
                "temp": temp,
                "wind": wind_speed
            }
            last_weather_update = time.time()
        else:
            print(f"Virhe API-kutsussa! Statuskoodi: {response.status_code}, Viesti: {response.text}")
            return None

    threading.Thread(target=fetch_weather, daemon=True).start()

    return current_weather