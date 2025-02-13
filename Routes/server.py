import requests
from flask import Flask, jsonify, request
from flask_socketio import SocketIO
import webbrowser
import threading
from http.server import SimpleHTTPRequestHandler
import http.server

PORT = 8000
FLASK_PORT = 5000
file_path = "templates/map.html"
url = f"http://127.0.0.1:{PORT}/templates/map.html"
#clients = set()
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Alkukoordinaatit
latitude, longitude = None, None

def update_map_html(lat, lon):
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
        content = content.replace("var initialLat = 60.1695;", f"var initialLat = {lat};")
        content = content.replace("var initialLon = 24.9354;", f"var initialLon = {lon};")
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
@app.route("/location", methods=["GET"])
def get_location():
    global latitude, longitude
    return jsonify({"lat": latitude, "lon": longitude})

@app.route("/update_location", methods=["POST"])
def update_location():
    global latitude, longitude
    data = request.get_json()
    latitude = data["lat"]
    longitude = data["lon"]
    socketio.emit("location_update", {"lat": latitude, "lon": longitude})
    return jsonify({"message": "Location updated", "lat": latitude, "lon": longitude})

def run_flask():
    #app.run(host="127.0.0.1", port=FLASK_PORT, debug=False, use_reloader=False)
    socketio.run(app, host="127.0.0.1", port=FLASK_PORT, debug=False, use_reloader=False)

def start_server(init_latitude, init_longitude, zoom):
    #global latitude, longitude
    #latitude = init_latitude
    #longitude = init_longitude
    update_map_html(init_latitude, init_longitude)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    class CustomHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/":
                self.path = "/templates/map.html"
            return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def run_http_server():
        with http.server.HTTPServer(("127.0.0.1", PORT), CustomHandler) as httpd:
            httpd.serve_forever()

    server_thread = threading.Thread(target=run_http_server, daemon=True)
    server_thread.start()

    webbrowser.open(url)

def update_server(latitude, longitude, zoom):
    response = requests.post(f"http://127.0.0.1:5000/update_location", json={"lat": latitude, "lon": longitude})