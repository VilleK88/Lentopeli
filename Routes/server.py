import webbrowser
import threading
import http.server
import json
import requests
import os

# Määritetään palvelimen portti ja muut asetukset
PORT = 8000
MAX_CONTENT_LENGTH = 1024
ALLOWED_FILES = {"/templates/map.html", "/templates/location.json", "/templates/airplane.svg"}
MAP_FILE_PATH = "templates/map.html"
LOCATION_FILE_PATH = "templates/location.json"
URL = f"http://127.0.0.1:{PORT}/templates/map.html"

# Alustaa pelaajan aloituskoordinaatit ja tallentaa ne JSON-tiedostoon
def starting_coordinates(lat, lon):
    location_data = {"lat": lat, "lon": lon}
    with open(LOCATION_FILE_PATH, "w") as file:
        json.dump(location_data, file)

# HTTP-palvelimen käsittelijäluokka, joka hallitsee GET- ja POST-pyynnöt
class CustomHandler(http.server.SimpleHTTPRequestHandler):

    # Käsittelee POST-pyynnöt, joita käytetään sijainnin päivittämiseen
    def do_post(self):
        # Tarkistetaan, että pyyntö on /update_location, muuten palautetaan 404
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
            self.wfile.write(b'{"error": "Invalid JSON"}')

    # Käsittelee GET-pyynnöt, kuten sijaintitiedon hakemisen
    def do_GET(self):
        if self.path == "/location":
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
            self.wfile.write(b'{"error": "Forbidden"}')

# Käynnistää HTTP-palvelimen, joka toimii paikallisella koneella
def run_http_server():
    with http.server.HTTPServer(("127.0.0.1", PORT), CustomHandler) as httpd:
        print(f"Palvelin käynnissä osoitteessa http://127.0.0.1:{PORT}")
        webbrowser.open(URL) # Avaa selaimen karttasivulle
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