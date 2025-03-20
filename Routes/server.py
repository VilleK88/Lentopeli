import webbrowser
import threading
import http.server
import json
import requests
import os
from Loops import user, flight
from Database import db

# Määritetään palvelimen portti ja muut asetukset
PORT = 8000
MAX_CONTENT_LENGTH = 1024
ALLOWED_FILES = {"/templates/map.html", "/templates/location.json", "/templates/airplane.svg", "/templates/main_menu.html"}
MAP_FILE_PATH = "templates/map.html"
LOCATION_FILE_PATH = "templates/location.json"
PLAYER_FILE_PATH = "database/players.json"
#URL = f"http://127.0.0.1:{PORT}/templates/map.html"
URL = f"http://127.0.0.1:{PORT}/templates/main_menu.html"
STATIC_DIR = "static"

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
            "/add_user": self.handle_add_user
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

        """if self.path == "/select_user":
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data)
                user_name = data.get("user_name")
                command = data.get("command")

                if command == "select_user":
                    result = user.select_user(user_name)
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True}).encode())
                else:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Tuntematon komento"}).encode())
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Virheellinen JSON"}).encode())
        elif self.path == "/add_user":
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data)
                name = data.get("name", "").strip()

                if not name:
                    self.send_response(400)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "message": "Nimi ei voi olla tyhjä."}).encode())
                    return

                success = user.add_new_user(name)

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                if success:
                    self.wfile.write(json.dumps({"success": True, "message": f"Käyttäjä '{name}' lisätty tietokantaan."}).encode())
                else:
                    self.wfile.write(json.dumps({"success": False, "message": "Käyttäjänimi on jo käytössä tai virheellinen."}).encode())
            except json.JSONDecodeError:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": "Virheellinen JSON-data."}).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error": "Not found"}')"""


        """"# Tarkistetaan, että pyyntö on /update_location, muuten palautetaan 404
        if self.path != "/update_location":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error": "Not found"}')
            return

        # Tarkistetaan, että pyyntö tulee oikeasta lähteestä (127.0.0.1)
        origin = self.headers.get('Origin')
        if origin and "127.0.0.1" not in origin:
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b'{"error": "Forbidden"}')
            return

        # Rajoitetaan datan koko enintään 1024 tavuun
        content_length = int(self.headers['Content-Length'])
        if content_length > MAX_CONTENT_LENGTH:
            self.send_response(413)
            self.end_headers()
            self.wfile.write(b'{"error": "Payload too large"}')
            return

        # Luetaan ja päivitetään sijaintitiedosto
        post_data = self.rfile.read(content_length)
        try:
            data = json.loads(post_data)
            temp_path = LOCATION_FILE_PATH + ".tmp"

            with open(temp_path, "w") as temp_file:
                json.dump(data, temp_file)
            os.replace(temp_path, LOCATION_FILE_PATH)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"message": "Location updated"}).encode())

        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error": "Invalid JSON"}')"""

    # Käsittelee GET-pyynnöt, kuten sijaintitiedon hakemisen
    def do_GET(self):
        if self.path in ALLOWED_FILES:
            super().do_GET()
        elif self.path.startswith("/static/"):
            self.path = self.path.lstrip("/")
            super().do_GET()
        elif self.path == "/get_user":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            user_data = {
                "user_name": user.user_name,
                "airport_name": user.airport_name,
                "current_icao": user.current_icao,
                "cash": user.cash,
                "fuel": flight.current_fuel
            }
            self.wfile.write(json.dumps(user_data).encode())
        elif self.path == "/get_users":
            users = db.show_current_users()
            if users:
                user_list = [{"id": player[0], "screen_name": player[1]} for player in users]
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(user_list).encode())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'{"error": "No users found"}')
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error": "Not found"}')

        """if self.path == "/location":
            try:
                with open(LOCATION_FILE_PATH, "r") as file:
                    data = json.load(file)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'{"error": "Location file not found"}')
        elif self.path in ALLOWED_FILES:
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        else:
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b'{"error": "Forbidden"}')"""

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