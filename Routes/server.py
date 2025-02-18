import webbrowser
import threading
from http.server import SimpleHTTPRequestHandler
import http.server
import json
import requests

PORT = 8000
FLASK_PORT = 5000
map_file_path = "templates/map.html"
location_file_path = "templates/location.json"
url = f"http://127.0.0.1:{PORT}/templates/map.html"

def starting_coordinates(lat, lon):
    location_data = {"lat": lat, "lon": lon}
    with open(location_file_path, "w") as file:
        json.dump(location_data, file)

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/update_location":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data)
                with open(location_file_path, "w") as file:
                    json.dump(data, file)

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Location updated"}).encode())

            except json.JSONDecodeError:
                self.send_response(400)
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
                self.wfile.write(b'{"error": "Location file not found"}')
        else:
            return http.server.SimpleHTTPRequestHandler.do_GET(self)

def run_http_server():
    with http.server.HTTPServer(("127.0.0.1", PORT), CustomHandler) as httpd:
        print(f"Plavelin käynnissä osoitteessa http.//127.0.0.1:{PORT}")
        webbrowser.open(url)
        httpd.serve_forever()

def start_server():
    server_thread = threading.Thread(target=run_http_server, daemon=True)
    server_thread.start()

def update_server(latitude, longitude, zoom):
    new_data = {"lat": latitude, "lon": longitude}
    try:
        with open(location_file_path, "w") as file:
            json.dump(new_data, file)
        print(f"Päivitetty sijainti: {latitude}, {longitude}")
        # Lähetetään pyyntö päivittämään kartta JavaScriptin kautta
        requests.post(f"http://127.0.0.1:{PORT}/update_location", json=new_data)
    except Exception as e:
        print(f"Virhe sijainnin tallentamisessa: {e}")