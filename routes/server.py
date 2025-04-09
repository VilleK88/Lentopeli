import http.server
import json, os, sys, threading, webbrowser, time, requests
from loops import user, flight
from database import db
from dotenv import load_dotenv
import main

# Määritetään palvelimen portti ja muut asetukset
PORT = 8000
MAX_CONTENT_LENGTH = 1024
ALLOWED_FILES = {"/templates/map.html", "/templates/location.json", "/templates/airplane.svg", "/templates/main_menu.html"}
MAP_FILE_PATH = "templates/map.html"
LOCATION_FILE_PATH = "templates/location.json"
PLAYER_FILE_PATH = "database/players.json"
URL = f"http://127.0.0.1:{PORT}/templates/main_menu.html"
STATIC_DIR = "static"

# Alustetaan säämuuttujat
last_weather_update = 0
cached_weather = None

# Alustaa pelaajan aloituskoordinaatit ja tallentaa ne JSON-tiedostoon
def starting_coordinates(lat, lon):
    location_data = {"lat": lat, "lon": lon}
    with open(LOCATION_FILE_PATH, "w") as file:
        json.dump(location_data, file)

# HTTP-palvelimen käsittelijäluokka, joka hallitsee GET- ja POST-pyynnöt
class CustomHandler(http.server.SimpleHTTPRequestHandler):

    # Käsittelee POST-pyynnöt, joita käytetään sijainnin päivittämiseen
    def do_POST(self):
        """Käsittelee kaikki POST-pyynnöt reititysjärjestelmän kautta."""

        # Määritetään POST-reitit ja niihin liittyvät funktiot
        routes = {
            "/select_user": self.handle_select_user,
            "/add_user": self.handle_add_user,
            "/log_out": self.handle_logout,
            "/exit_game": self.handle_exit_game,
            "/start_game": self.handle_start_game,
            "/update_location": self.handle_update_location,
            "/select_icao": self.handle_select_icao,
            "/stop_flight": self.handle_stop_flight
        }

        # Tarkistetaan, onko polku olemassa reitityksessä
        handler = routes.get(self.path)

        if handler:
            handler() # Kutsutaan vastaavaa käsittelyfunktiota
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())

    def get_post_data(self):
        """Lukee ja jäsentää JSON-datan POST-pyynnöstä."""
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            return json.loads(post_data)
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Virheellinen JSON"}).encode())
            return None

    def send_json_response(self, status, data):
        """Lähettää JSON-muotoisen vastauksen."""
        self.send_response(status)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def handle_logout(self):
        """Käsittelee käyttäjän uloskirjautumisen"""
        db.log_out()
        self.send_json_response(200, {"success": True, "message": "Käyttäjä kirjattu ulos"})

    def handle_exit_game(self):
        """Sulkee ohjelman"""
        sys.exit()

    def handle_start_game(self):
        """Käsittelee pelin käynnistyksen"""
        user.start_game()
        self.send_json_response(200, {"success": True, "message": "Peli alkaa."})

    def handle_stop_flight(self):
        data = self.get_post_data()
        if not data:
            return

        command = data.get("command")

        if command == "stop_flight":
            flight.stop_flight = True

    def handle_select_icao(self):
        data = self.get_post_data()
        if not data:
            return

        icao = data.get("icao")
        command = data.get("command")

        if command == "select_icao":
            airport = db.get_airport_coords(icao)
            if airport:
                self.send_json_response(200, {"success": True})
                user.target_airport = airport
                user.ingame_menu_active = False
        else:
            self.send_json_response(400, {"error": "Tuntematon komento"})

    def handle_select_user(self):
        """Käsittelee käyttäjän valinnan."""
        data = self.get_post_data()
        if not data:
            return

        user_name = data.get("user_name")
        command = data.get("command")

        if command == "select_user":
            result = user.select_user(user_name)
            self.send_json_response(200, {"success": True})
        else:
            self.send_json_response(400, {"error": "Tuntematon komento"})

    def handle_add_user(self):
        """Käsittelee uuden käyttäjän lisäämisen."""
        data = self.get_post_data()
        if not data:
            return

        name = data.get("name", "").strip()

        if not name:
            self.send_json_response(400, {"success": False, "message": "Nimi ei voi olla tyhjä."})
            return

        success = user.add_new_user(name)

        if success:
            self.send_json_response(200, {"success": True, "message": f"Käyttäjä '{name}' lisätty tietokantaan."})
        else:
            self.send_json_response(200, {"success": False, "message": "Käyttäjänimi on jo käytössä tai virheellinen."})

    # Käsittelee GET-pyynnöt, kuten sijaintitiedon hakemisen
    def do_GET(self):
        """Käsittelee kaikki GET-pyynnöt dynaamisen reitityksen kautta."""

        # Määritetään GET-reitit ja niihin liittyvät funktiot
        routes = {
            "/get_user": self.handle_get_user,
            "/get_users": self.handle_get_users,
            "/location": self.handle_get_location,
            "/get_weather": self.handle_get_weather,
            "/get_in_game_menu_on": self.handle_get_in_game_menu_on
        }

        # Käsitellään staattiset tiedostot
        if self.path in ALLOWED_FILES or self.path.startswith("/static/") or self.path.startswith("/templates/"):
            self.path = self.path.lstrip("/")
            super().do_GET()
            return

        # Haetaan reitti sanakirjasta ja suoritetaan funktio, jos löytyy
        handler = routes.get(self.path)
        if handler:
            handler()
        else:
            self.send_json_response(404, {"error": "Not found"})

    def handle_get_weather(self):
        """Palauttaa ajankohtaiset säätiedot JSON-muodossa."""
        if main.current_location:
            lat, lon = main.current_location
            print(f"main.current_location: ", main.current_location)
            weather_data = fetch_weather(lat, lon)

            if "error" in weather_data:
                self.send_json_response(500, weather_data)
            else:
                self.send_json_response(200, weather_data)
        else:
            self.send_json_response(400, {"error": "Sijaintia ei ole asetettu"})

    def handle_get_in_game_menu_on(self):
        data = {"in_game_menu_on": user.ingame_menu_active}
        self.send_json_response(200, data)

    def handle_get_user(self):
        """Käsittelee käyttäjän tietojen haun."""
        user_data = {
            "user_name": user.user_name,
            "airport_name": user.airport_name,
            "current_icao": user.current_icao,
            "cash": user.cash,
            "fuel": flight.current_fuel
         }
        self.send_json_response(200, user_data)

    def handle_get_users(self):
        """Käsittelee kaikkien käyttäjien haun."""
        users = db.show_current_users()
        if users:
            user_list = [{"id": player[0], "screen_name": player[1]} for player in users]
            self.send_json_response(200, user_list)
        else:
            self.send_json_response(404, {"error": "No users found"})

    def handle_get_location(self):
        """Palauttaa lentokoneen sijaintitiedot JSON-muodossa."""
        try:
            with open(LOCATION_FILE_PATH, "r") as file:
                data = json.load(file)
                self.send_json_response(200, data)
        except FileNotFoundError:
            self.send_json_response(404, {"error": "Location file not found"})

    def handle_update_location(self):
        """Päivittää lentokoneen sijainnin."""
        data = self.get_post_data()
        if not data:
            return

        try:
            with open(LOCATION_FILE_PATH, "w") as file:
                json.dump(data, file)
            self.send_json_response(200, {"message": "Location updated"})
        except Exception as e:
            self.send_json_response(500, {"error": str(e)})

# Käynnistää HTTP-palvelimen, joka toimii paikallisella koneella
def run_http_server():
    with http.server.HTTPServer(("127.0.0.1", PORT), CustomHandler) as httpd:
        print(f"Palvelin käynnissä osoitteessa http://127.0.0.1:{PORT}")
        webbrowser.open(URL) # Avaa selaimen etusivulle
        httpd.serve_forever()

# Käynnistää palvelimen erillisessä säikeessä, jotta ohjelma ei jää jumiin
def start_server():
    server_thread = threading.Thread(target=run_http_server, daemon=True)
    server_thread.start()

# Päivittää palvelimelle lentokoneen sijainnin, jos se on ilmassa
def update_server(latitude, longitude, on_flight):
    if not on_flight:
        print("Lentokone ei liiku. Ei päivitetä sijaintia.")
        return

    # Luo uuden sijaintidatan JSON-muodossa
    new_data = {"lat": latitude, "lon": longitude, "on_flight": on_flight}
    temp_path = LOCATION_FILE_PATH + ".tmp"

    try:
        # Tallennetaan uusi sijaintitieto tilapäistiedostoon ja korvataan alkuperäinen
        with open(temp_path, "w") as temp_file:
            json.dump(new_data, temp_file)
        os.replace(temp_path, LOCATION_FILE_PATH)

        # Lähetetään HTTP POST -pyyntö palvelimelle päivittämään kartta
        requests.post(f"http://127.0.0.1:{PORT}/update_location", json=new_data)

    except Exception as e:
        print(f"Virhe sijainnin tallentamisessa: {e}")

def fetch_weather(lat, lon):
    """Hakee säätiedot OpenWeatherMapista käyttäjän sijainnin perusteella."""
    global last_weather_update, cached_weather

    # Ladataan API-avain ympäristömuuttujista
    load_dotenv()
    API_KEY = os.getenv("OPENWEATHER_API_KEY")
    if not API_KEY:
        return {"error": "API-avain puuttuu"}

    # Jos viimeisimmästä päivityksestä on alle 3 minuuttia, käytetään välimuistia
    if time.time() - last_weather_update < 180 and cached_weather:
        return cached_weather

    # Määritetään OpenWeatherMap API:n URL
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
    url = f"{BASE_URL}?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=fi"

    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            data = response.json()

            # Haetaan sääparametrit
            weather_condition = data["weather"][0]["description"].capitalize()
            temp = data["main"]["temp"]
            wind_speed = data["wind"]["speed"]
            wind_direction = data["wind"].get("deg", 0)

            # Turbulenssivaroitus: jos tuuli yli 10 m/s
            turbulence_warning = wind_speed > 10

            # Tallennetaan tiedot välimuistiin
            cached_weather = {
                "temperature": temp,
                "wind_speed": wind_speed,
                "wind_direction": wind_direction,
                "weather": weather_condition,
                "turbulence_warning": turbulence_warning
            }
            last_weather_update = time.time()

            return cached_weather

        else:
            return {"error": f"Virhe API-kutsussa. Koodi: {response.status_code}"}

    except requests.RequestException as e:
        return {"error": f"Yhteysvirhe: {e}"}