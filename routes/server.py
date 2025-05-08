from flask import Flask, request, jsonify, send_from_directory, session
import json, os, sys, threading, webbrowser, time, requests, random
from loops import user, flight, inventorymanager
from loops.customers import CustomerManager, AirportManager, EconomyManager
from loops.shop import Shop
from database import db
from dotenv import load_dotenv
import main

shop_instance = Shop()
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, "static"),
    template_folder=os.path.join(BASE_DIR, "templates")
)

app.secret_key = os.environ.get('Helpo', 'flight_game_secret_key')

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


# Lataa asiakkaat JSON-tiedostosta
def load_customers():
    try:
        with open('database/customersdb.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading customers: {e}")
        return []


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


@app.route("/exit_game", methods=["POST"])
def handle_exit_game():
    sys.exit()


@app.route("/start_game", methods=["POST"])
def handle_start_game():
    try:
        user.start_game()
        return jsonify({"success": True, "message": "Peli alkaa."})
    except Exception as e:
        print(f"Virhe start_game(): {e}")
        return jsonify({"success": False, "error": str(e)}), 500



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


@app.route("/get_user", methods=["GET"])
def handle_get_user():
    return jsonify({
        "user_name": user.user_name,
        "airport_name": user.airport_name,
        "current_icao": user.current_icao,
        "cash": user.cash,
        "fuel": flight.current_fuel
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
    if main.current_location:
        lat, lon = main.current_location
        print("main.current_location:", main.current_location)
        return jsonify(fetch_weather(lat, lon))
    return jsonify({"error": "Sijaintia ei ole asetettu"}), 400


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


# Kauppaan liittyvät reitit

@app.route("/get_shop_items", methods=["GET"])
def get_shop_items():
    """Hakee kaupan tuotteet"""
    shop = Shop()
    products = shop.get_products_list()
    return jsonify({"products": products})


@app.route("/buy_item", methods=["POST"])
def buy_item():
    """Ostaa tuotteen kaupasta"""
    data = request.get_json()
    product_name = data.get("product_name")

    if not product_name:
        return jsonify({"success": False, "message": "Virheellinen pyyntö: tuotteen nimi puuttuu"}), 400

    # Haetaan käyttäjän tiedot
    user_id = user.user_id
    cash = user.cash

    if not user_id:
        return jsonify({"success": False, "message": "Käyttäjä ei ole kirjautunut"}), 401

    # Suoritetaan osto
    shop = Shop()
    success, message, new_cash = shop.purchase_product(user_id, product_name, cash)

    if success:
        # Päivitetään käyttäjän käteinen
        user.cash = new_cash
        return jsonify({"success": True, "message": message, "new_cash": new_cash})
    else:
        return jsonify({"success": False, "message": message})


# Inventaarioon liittyvät reitit

@app.route("/get_inventory", methods=["GET"])
def get_inventory():
    """Hakee käyttäjän inventaariotiedot"""
    user_id = user.user_id

    if not user_id:
        return jsonify({"error": "Käyttäjä ei kirjautunut"}), 401

    try:
        inventory_manager = inventorymanager.InventoryManager()
        inventory = inventory_manager.get_inventory()

        if not inventory:
            return jsonify({"inventory": {
                "fruits": 0,
                "alcohol": 0,
                "snacks": 0,
                "soda": 0,
                "meals": 0,
                "water": 0,
                "fuel": flight.current_fuel
            }})

        # Varmistetaan että fuel on mukana
        if "current_fuel" in inventory and "fuel" not in inventory:
            inventory["fuel"] = inventory["current_fuel"]
        elif "fuel" not in inventory:
            inventory["fuel"] = flight.current_fuel

        # Käytetään dictionary-muotoa joka on yhteensopiva JS-koodin kanssa
        inventory_dict = {
            "fruits": inventory.get("fruits", 0),
            "alcohol": inventory.get("alcohol", 0),
            "snacks": inventory.get("snacks", 0),
            "soda": inventory.get("soda", 0),
            "meals": inventory.get("meals", 0),
            "water": inventory.get("water", 0),
            "fuel": inventory.get("fuel", flight.current_fuel)
        }

        return jsonify({"inventory": inventory_dict})

    except Exception as e:
        print(f"Virhe inventaarion haussa: {e}")
        return jsonify({"error": f"Virhe inventaarion haussa: {str(e)}"}), 500


@app.route("/use_item", methods=["POST"])
def use_item():
    """Käyttää tuotetta lennon aikana"""
    data = request.get_json()
    item_name = data.get("item_name")

    if not item_name:
        return jsonify({"success": False, "message": "Tuotteen nimi puuttuu"}), 400

    # Tarkistetaan onko käyttäjä kirjautunut sisään
    user_id = user.user_id
    if not user_id:
        return jsonify({"success": False, "message": "Käyttäjä ei kirjautunut"}), 401

    # Tarkistetaan onko asiakas
    if not hasattr(main, "customer_manager") or not main.customer_manager.current_customer:
        return jsonify({
            "success": False,
            "message": "Ei asiakasta, jolle tarjota tuotetta"
        })

    # Käytetään tuotetta InventoryManagerin kautta
    inventory_manager = inventorymanager.InventoryManager()
    success = inventory_manager.use_item(user_id, item_name, main.customer_manager)

    if success:
        # Haetaan päivitetty asiakasmieliala
        mood = main.customer_manager.get_customer_mood()
        customer_name = main.customer_manager.current_customer["name"]

        return jsonify({
            "success": True,
            "message": f"Tuote {item_name} käytetty",
            "mood": mood,
            "customer_name": customer_name
        })
    else:
        return jsonify({
            "success": False,
            "message": f"Tuotetta {item_name} ei voitu käyttää"
        })


# Asiakkaisiin liittyvät reitit
@app.route("/get_customer_info", methods=["GET"])
def get_customer_info():
    """Hakee nykyisen asiakkaan tiedot"""
    # Tarkistetaan onko customer_manager olemassa
    if not hasattr(main, "customer_manager"):
        return jsonify({"has_customer": False, "message": "No customer selected"}), 200

    # Tarkistetaan onko asiakas valittu
    if not main.customer_manager.current_customer:
        return jsonify({"has_customer": False, "message": "No customer selected"}), 200

    # Haetaan nykyisen asiakkaan tiedot
    customer = main.customer_manager.current_customer
    mood = main.customer_manager.get_customer_mood()
    mood_emoji = main.customer_manager.get_mood_emoji(mood)

    # Luodaan vastaus kaikilla tarpeellisilla asiakastiedoilla
    customer_info = {
        "has_customer": True,
        "name": customer.get("name", "Unknown"),
        "destination": customer.get("destination", "Unknown"),
        "mood": mood,
        "mood_emoji": mood_emoji,
        "likes": customer.get("likes", []),
        "dislikes": customer.get("dislikes", [])
    }

    # Jos asiakkaalla on kohde, haetaan kohdelentokentän tiedot
    if customer_info.get("destination"):
        # Käytetään olemassa olevaa airport_manager tai luodaan uusi
        if hasattr(main, "airport_manager"):
            airport_manager = main.airport_manager
        else:
            airport_manager = AirportManager()
            main.airport_manager = airport_manager

        # Haetaan lentokentän tiedot
        airport_info = airport_manager.get_airport_info(customer_info["destination"])
        if airport_info:
            customer_info["destination_name"] = airport_info[0]

        # Haetaan lentokentän koordinaatit jos saatavilla
        coords = airport_manager.get_airport_coordinates(customer_info["destination"])
        if coords:
            customer_info["destination_lat"] = coords[0]
            customer_info["destination_lon"] = coords[1]

    return jsonify(customer_info)


@app.route("/get_customer_mood", methods=["GET"])
def get_customer_mood():
    """Hakee asiakkaan mielialan"""
    if not hasattr(main, "customer_manager") or not main.customer_manager.current_customer:
        return jsonify({"has_customer": False}), 200

    mood = main.customer_manager.get_customer_mood()
    mood_emoji = main.customer_manager.get_mood_emoji(mood)

    return jsonify({
        "has_customer": True,
        "mood": mood,
        "mood_emoji": mood_emoji,
        "mood_text": f"{mood}/10"
    })


@app.route("/get_all_customers", methods=["GET"])
def get_all_customers():
    """Hakee kaikki saatavilla olevat asiakkaat"""
    customers_data = load_customers()

    # Lisätään satunnaiset kohteet asiakkaille näyttöä varten
    customers_with_destinations = []

    # Määritellään lentoasemat, jos niitä tarvitaan
    airports = [
        {"ident": "EFHK", "name": "Helsinki-Vantaa Airport", "lat": 60.3172, "lon": 24.9633},
        {"ident": "EGLL", "name": "London Heathrow Airport", "lat": 51.4775, "lon": -0.4614},
        {"ident": "KJFK", "name": "John F. Kennedy International Airport", "lat": 40.6413, "lon": -73.7781},
        {"ident": "EDDF", "name": "Frankfurt Airport", "lat": 50.0379, "lon": 8.5622},
        {"ident": "LFPG", "name": "Charles de Gaulle Airport", "lat": 49.0097, "lon": 2.5479},
        {"ident": "RJAA", "name": "Narita International Airport", "lat": 35.7647, "lon": 140.3864},
        {"ident": "YSSY", "name": "Sydney Airport", "lat": 33.9399, "lon": 151.1753}
    ]

    for customer in customers_data:
        # Kloonataan asiakas, jotta ei muuteta alkuperäistä
        customer_copy = dict(customer)

        # Lisätään satunnainen kohde, jos sitä ei ole
        if "destination" not in customer_copy:
            random_airport = random.choice(airports)
            customer_copy["destination"] = random_airport["ident"]
            customer_copy["destination_name"] = random_airport["name"]

        customers_with_destinations.append(customer_copy)

    return jsonify({
        "success": True,
        "customers": customers_with_destinations
    })


@app.route('/select_random_customer', methods=['GET'])
def select_random_customer():
    """Valitsee satunnaisen asiakkaan ja palauttaa tuloksen"""
    try:
        current_icao = user.current_icao

        if hasattr(main, "airport_manager"):
            airport_manager = main.airport_manager
        else:
            airport_manager = AirportManager()
            main.airport_manager = airport_manager

        icao_list = airport_manager.load_airports()

        if not current_icao and icao_list:
            current_icao = icao_list[0]

        if not icao_list:
            return jsonify({"success": False, "message": "No airports available"})

        if hasattr(main, "customer_manager"):
            customer_manager = main.customer_manager
        else:
            customer_manager = CustomerManager()
            main.customer_manager = customer_manager

        customers = customer_manager.load_customers()  # ✅ tämä lisäys
        customer, destination = customer_manager.select_customer(current_icao, icao_list, customers)

        if customer:
            main.customer_manager.current_customer = customer

            if not hasattr(main.customer_manager, "customer_mood"):
                main.customer_manager.customer_mood = 5

            return jsonify({"success": True, "customer": customer})
        else:
            return jsonify({"success": False, "message": "Could not select a customer"})

    except Exception as e:
        print(f"Error selecting random customer: {e}")
        return jsonify({"success": False, "message": str(e)})


@app.route('/select_customer', methods=['POST'])
def select_customer_route():
    """API-reitti tietyn asiakkaan valitsemiseen nimen perusteella"""
    data = request.get_json()
    customer_name = data.get('customer_name')

    if not customer_name:
        return jsonify({"success": False, "message": "No customer name provided"})

    try:
        # Käytetään olemassa olevaa customer_manager tai luodaan uusi
        if hasattr(main, "customer_manager"):
            customer_manager = main.customer_manager
        else:
            customer_manager = CustomerManager()
            main.customer_manager = customer_manager

        customers = customer_manager.load_customers()

        # Etsitään asiakas nimen perusteella
        customer = next((c for c in customers if c.get('name') == customer_name), None)

        if not customer:
            return jsonify({"success": False, "message": f"Customer '{customer_name}' not found"})

        # Haetaan nykyinen sijainti ja kaikki lentokentät
        current_icao = user.current_icao

        if hasattr(main, "airport_manager"):
            airport_manager = main.airport_manager
        else:
            airport_manager = AirportManager()
            main.airport_manager = airport_manager

        icao_list = airport_manager.load_airports()

        if not current_icao and icao_list:
            current_icao = icao_list[0]  # Käytä ensimmäistä lentokenttää jos mikään ei ole valittu

        if not icao_list:
            return jsonify({"success": False, "message": "No airports available"})

        # Lisätään määränpää asiakkaalle
        destination = random.choice([icao for icao in icao_list if icao != current_icao])
        customer["destination"] = destination

        # Haetaan lentokentän koko nimi määränpäälle
        airport_info = airport_manager.get_airport_info(destination)
        if airport_info:
            customer["destination_name"] = airport_info[0]
        else:
            customer["destination_name"] = "Unknown Airport"

        # Asetetaan nykyiseksi asiakkaaksi managerissa
        customer_manager.current_customer = customer
        customer_manager.customer_mood = 5  # Resetoi mieliala

        return jsonify({"success": True, "customer": customer})

    except Exception as e:
        print(f"Error selecting customer: {e}")
        return jsonify({"success": False, "message": str(e)})


@app.route("/complete_flight", methods=["POST"])
def handle_complete_flight():
    """Käsittelee lentojen päättymisen"""
    data = request.get_json()
    arrived_icao = data.get("arrived_icao")

    if not arrived_icao:
        return jsonify({"success": False, "message": "Missing ICAO code"}), 400

    print(f"Processing flight completion at {arrived_icao}")

    # Haetaan kirjautuneen käyttäjän ID
    user_data = db.get_logged_in_user_data()
    if not user_data:
        return jsonify({"success": False, "message": "No logged in user found"}), 401

    user_id = user_data[0]  # Ensimmäinen arvo on käyttäjän ID

    # Tarkistetaan ja luodaan tarvittavat managerit
    if not hasattr(main, "customer_manager") or main.customer_manager is None:
        print("Luodaan uusi CustomerManager")
        main.customer_manager = CustomerManager()

    if not hasattr(main, "economy_manager") or main.economy_manager is None:
        print("Luodaan uusi EconomyManager")
        main.economy_manager = EconomyManager(user_id=user_id)
    else:
        # Päivitetään economy manager käyttämään oikeaa käyttäjä-ID:tä
        main.economy_manager.user_id = user_id

    current_customer = main.customer_manager.current_customer

    if current_customer:
        print(f"Processing customer {current_customer.get('name')} arrival at {arrived_icao}")

        # Käsitellään saapuminen
        from loops.flight import process_arrived_at_airport

        success = process_arrived_at_airport(
            arrived_icao,
            main.customer_manager,
            main.economy_manager
        )

        if success:
            # Haetaan päivitetyt rahat ja maine
            current_cash = main.economy_manager.get_cash()
            current_reputation = main.economy_manager.get_reputation()

            # Päivitetään myös käyttäjä-objektin rahatieto
            user.cash = current_cash

            return jsonify({
                "success": True,
                "message": f"Flight completed! Customer satisfied and paid.",
                "cash": current_cash,
                "reputation": current_reputation,
                "customer_reset": True
            })
        else:
            return jsonify({
                "success": False,
                "message": "Flight completed, but customer didn't reach their destination",
                "destination": current_customer.get("destination"),
                "arrived_at": arrived_icao
            })
    else:
        print("No customer to process")
        return jsonify({
            "success": False,
            "message": "No customer to process"
        })


@app.route("/get_cash", methods=["GET"])
def handle_get_cash():
    """Hakee käyttäjän nykyisen rahamäärän"""
    user_data = db.get_logged_in_user_data()
    if not user_data:
        return jsonify({"success": False, "message": "No logged in user found"}), 401

    user_id = user_data[0]

    # Käytetään olemassa olevaa economy manageria tai luodaan uusi
    if hasattr(main, "economy_manager") and main.economy_manager.user_id == user_id:
        economy_manager = main.economy_manager
    else:
        economy_manager = EconomyManager(user_id=user_id)
        main.economy_manager = economy_manager

    current_cash = economy_manager.get_cash()

    # Päivitetään myös käyttäjä-objektin rahatieto
    user.cash = current_cash

    return jsonify({
        "success": True,
        "cash": current_cash
    })


@app.route("/get_reputation", methods=["GET"])
def handle_get_reputation():
    """Hakee käyttäjän nykyisen maineen"""
    user_data = db.get_logged_in_user_data()
    if not user_data:
        return jsonify({"success": False, "message": "No logged in user found"}), 401

    user_id = user_data[0]

    # Käytetään olemassa olevaa economy manageria tai luodaan uusi
    if hasattr(main, "economy_manager") and main.economy_manager.user_id == user_id:
        economy_manager = main.economy_manager
    else:
        economy_manager = EconomyManager(user_id=user_id)
        main.economy_manager = economy_manager

    reputation = economy_manager.get_reputation()

    return jsonify({
        "success": True,
        "reputation": reputation
    })

def run_flask_server():
    print(f"Palvelin käynnissä osoitteeessa {URL}")
    webbrowser.open(URL)
    app.run(host="127.0.0.1", port=PORT, use_reloader=False)


def start_server():
    # Create necessary directories if they don't exist
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('database', exist_ok=True)

    server_thread = threading.Thread(target=run_flask_server, daemon=True)
    server_thread.start()


def update_server(latitude, longitude, on_flight):
    if not on_flight:
        print("Lentokone ei liiku. Ei päivitetä sijaintia.")
        return

    new_data = {"lat": latitude, "lon": longitude, "on_flight": on_flight}
    temp_path = LOCATION_FILE_PATH + ".tmp"

    try:
        with open(temp_path, "w") as temp_file:
            json.dump(new_data, temp_file)
        os.replace(temp_path, LOCATION_FILE_PATH)
        requests.post(f"http://127.0.0.1:{PORT}/update_location", json=new_data)
    except Exception as e:
        print(f"Virhe sijainnin tallentamisessa: {e}")


def fetch_weather(lat, lon):
    global last_weather_update, cached_weather
    load_dotenv()
    API_KEY = os.getenv("OPENWEATHER_API_KEY")
    if not API_KEY:
        return {"error": "API-avain puuttuu"}

    if time.time() - last_weather_update < 180 and cached_weather:
        return cached_weather

    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
    url = f"{BASE_URL}?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=fi"

    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            data = response.json()
            weather_condition = data["weather"][0]["description"].capitalize()
            temp = data["main"]["temp"]
            wind_speed = data["wind"]["speed"]
            wind_direction = data["wind"].get("deg", 0)

            turbulence_warning = wind_speed > 10
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


if __name__ == "__main__":
    start_server()