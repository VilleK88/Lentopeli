from flask import Flask, request, jsonify, send_from_directory
import json, os, threading, webbrowser, time, requests

import utils.utils
from loops import user, flight
from database import db
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, "static"),
    template_folder=os.path.join(BASE_DIR, "templates")
)
# Määritetään palvelimen portti ja muut asetukset
PORT = 8000
MAX_CONTENT_LENGTH = 1024
STATIC_DIR = "static"
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
LOCATION_FILE_PATH = os.path.join(TEMPLATES_DIR, "location.json")
MAP_FILE_PATH = os.path.join(TEMPLATES_DIR, "map.html")
PLAYER_FILE_PATH = "database/players.json"
URL = f"http://127.0.0.1:{PORT}/main_menu.html"

# Alustetaan säämuuttujat
last_weather_update = 0
cached_weather = None

# Alustaa pelaajan aloituskoordinaatit ja tallentaa ne JSON-tiedostoon
def starting_coordinates(lat, lon):
    location_data = {"lat": lat, "lon": lon}
    with open(LOCATION_FILE_PATH, "w") as file:
        json.dump(location_data, file)

@app.route("/select_user", methods=["POST"])
def handle_select_user():
    data = request.get_json()
    if data.get("command") == "select_user":
        user.select_user(data.get("user_name"))
        return jsonify({"success": True})
    return jsonify({"error": "Tuntematon komento"}), 400

@app.route("/add_user", methods=["POST"])
def handle_add_user():
    data = request.get_json()
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"success": False, "message": "Nimi ei voi olla tyhjä."}), 400

    success = user.add_new_user(name)
    msg = f"Käyttäjä '{name}' lisätty tietokantaan." if success else "Käyttäjänimi on jo käytössä tai virheellinen."
    return jsonify({"success": success, "message": msg})

@app.route("/log_out", methods=["POST"])
def handle_logout():
    db.log_out()
    return jsonify({"success": True, "message": "Käyttäjä kirjattu ulos"})

@app.route("/exit_menu", methods=["GET", "POST"])
def handle_exit_menu():
    threading.Thread(target=shutdown).start()
    return jsonify({"status": "Palvelin sammuu"}), 200

@app.route("/exit_menu_and_logout", methods=["POST"])
def handle_exit_menu_and_logout():
    db.log_out()
    threading.Thread(target=shutdown).start()
    return jsonify({"status": "Palvelin sammuu"}), 200

@app.route("/exit_game", methods=["POST"])
def handle_exit_game():
    print("Lopeta peli: exit game")
    if user.ingame_menu_active:
        user.save_game_progress(user.user_id, flight.current_fuel, user.current_icao, False)
    threading.Thread(target=shutdown).start()
    return jsonify({"status": "Palvelin sammuu"}), 200

@app.route("/exit_game_and_logout", methods=["POST"])
def handle_exit_game_and_logout():
    print("Lopeta peli: exit game and logout")
    if user.ingame_menu_active:
        user.save_game_progress(user.user_id, flight.current_fuel, user.current_icao, True)
    threading.Thread(target=shutdown).start()
    return jsonify({"status": "Palvelin sammuu"}), 200

@app.route("/start_game", methods=["POST"])
def handle_start_game():
    user.start_game()
    return jsonify({"success": True, "message": "Peli alkaa."})

@app.route("/stop_flight", methods=["POST"])
def handle_stop_flight():
    data = request.get_json()
    if data.get("command") == "stop_flight":
        flight.stop_flight = True
        return jsonify({"success": True})
    return jsonify({"error": "Tuntematon komento"}), 400

@app.route("/select_icao", methods=["POST"])
def handle_select_icao():
    data = request.get_json()
    if data.get("command") == "select_icao":
        airport = db.get_airport_coords(data.get("icao"))
        if airport:
            user.target_airport = airport
            user.ingame_menu_active = False
            return jsonify({"success": True})
    return jsonify({"error": "Tuntematon komento"}), 400

@app.route("/update_location", methods=["POST"])
def handle_update_location():
    data = request.get_json()
    try:
        with open(LOCATION_FILE_PATH, "w") as f:
            json.dump(data, f)
        return jsonify({"message": "Location updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get_coords_for_icao", methods=["GET"])
def handle_get_coords_for_icon():
    dest_icao = request.args.get("dest_icao")
    current_airport = db.get_airport_coords(user.current_icao)
    dest_airport = db.get_airport_coords(dest_icao)
    return jsonify({
        "success": True,
        "lat1": current_airport[2],
        "lon1": current_airport[3],
        "lat2": dest_airport[2],
        "lon2": dest_airport[3]
    })

@app.route("/get_user", methods=["GET"])
def handle_get_user():
    return jsonify({
        "user_name": user.user_name,
        "airport_name": user.airport_name,
        "current_icao": user.current_icao,
        "cash": user.cash,
        "fuel": flight.current_fuel,
        "in_flight": flight.in_flight,
        "remaining_distance": flight.pub_re_distance,
        "current_time": flight.pub_current_time.strftime("%H:%M:%S") if flight.pub_current_time else ""
    })

@app.route("/get_users", methods=["GET"])
def handle_get_users():
    users = db.show_current_users()
    if users:
        return jsonify([{"id": u[0], "screen_name": u[1]} for u in users])
    return jsonify({"error": "No users found"}), 404

@app.route("/location", methods=["GET"])
def handle_get_location():
    try:
        if not os.path.exists(LOCATION_FILE_PATH):
            return jsonify({"error": "Location file not found"}), 404

        with open(LOCATION_FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

            if "lat" in data and "lon" in data:
                return jsonify(data)
            else:
                return jsonify({"error": "Invalid content in the file location.json"}), 400

    except json.JSONDecodeError as e:
        return jsonify({"error": f"JSON-error: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Unknown error {str(e)}"}), 500

@app.route("/get_weather", methods=["GET"])
def handle_get_weather():
    if flight.current_location:
        lat, lon = flight.current_location
        return jsonify(fetch_weather(lat, lon))
    return jsonify({"error": "Sijaintia ei ole asetettu"}), 400

@app.route("/get_airports", methods=["GET"])
def handle_get_airports():
    lat, lon = flight.current_location
    return jsonify(utils.utils.get_airports(lat, lon))

@app.route("/get_in_game_menu_on", methods=["GET"])
def handle_get_in_game_menu_on():
    return jsonify({"in_game_menu_on": user.ingame_menu_active})

@app.route("/<filename>.html")
def serve_html(filename):
    return send_from_directory(TEMPLATES_DIR, f"{filename}.html")

@app.route("/location.json")
def serve_location_json():
    return send_from_directory(TEMPLATES_DIR, "location.json")

@app.route("/static/<path:path>")
def serve_static(path):
    return send_from_directory(STATIC_DIR, path)

# Käynnistää Flask-palvelimen, joka toimii paikallisella koneella
def run_flask_server():
    print(f"Palvelin käynnissä osoitteeessa {URL}")
    webbrowser.open(URL)
    app.run(host="127.0.0.1", port=PORT, use_reloader=False)

# Käynnistää palvelimen erillisessä säikeessä, jotta ohjelma ei jää jumiin
def start_server():
    server_thread = threading.Thread(target=run_flask_server, daemon=True)
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

def shutdown():
    time.sleep(1)
    os._exit(0)