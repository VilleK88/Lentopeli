import webbrowser
import threading
import http.server
import json
import requests
import os

PORT = 8000
MAX_CONTENT_LENGTH = 1024
ALLOWED_FILES = {"/templates/map.html", "/templates/location.json"}
map_file_path = "templates/map.html"
location_file_path = "templates/location.json"
url = f"http://127.0.0.1:{PORT}/templates/map.html"

def starting_coordinates(lat, lon):
    location_data = {"lat": lat, "lon": lon}
    with open(location_file_path, "w") as file:
        json.dump(location_data, file)

class CustomHandler(http.server.SimpleHTTPRequestHandler):

    def do_POST(self):

        if self.path != "/update_location":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error": "Not found"}')
            return

        # Tarkistetaan, että pyyntö tulee oikeasta lähteestä
        origin = self.headers.get('Origin')
        if origin and "127.0.0.1" not in origin:
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b'{"error": "Forbidden"}')
            return

        # Rajoitetaan datan koko
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
            temp_path = location_file_path + ".tmp"

            with open(temp_path, "w") as temp_file:
                json.dump(data, temp_file)
            os.replace(temp_path, location_file_path)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"message": "Location updated"}).encode())

        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error": "Invalid JSON"}')

    def do_GET(self):
        if self.path == "/location":
            try:
                with open(location_file_path, "r") as file:
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

def run_http_server():
    with http.server.HTTPServer(("127.0.0.1", PORT), CustomHandler) as httpd:
        print(f"Palvelin käynnissä osoitteessa http://127.0.0.1:{PORT}")
        webbrowser.open(url)
        httpd.serve_forever()

def start_server():
    server_thread = threading.Thread(target=run_http_server, daemon=True)
    server_thread.start()

def update_server(latitude, longitude, on_flight):
    if not on_flight:
        print("Lentokone ei liiku. Ei päivitetä sijaintia.")
        return

    new_data = {"lat": latitude, "lon": longitude, "on_flight": on_flight}
    temp_path = location_file_path + ".tmp"

    try:
        with open(temp_path, "w") as temp_file:
            json.dump(new_data, temp_file)
        os.replace(temp_path, location_file_path)

        # Lähetetään pyyntö päivittämään kartta JavaScriptin kautta
        requests.post(f"http://127.0.0.1:{PORT}/update_location", json=new_data)

    except Exception as e:
        print(f"Virhe sijainnin tallentamisessa: {e}")