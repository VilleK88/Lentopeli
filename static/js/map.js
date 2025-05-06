let map; // Karttaobjekti
let marker; // Lentokoneen merkki kartalla
let lastLat = null; // Viimeisin latitude (leveysaste)
let lastLon = null; // Viimeisin longitude (pituusaste)
let in_flight = false;
let remaining_distance = 0;
const weatherEffectContainer = document.getElementById("weather-effect-container");

function getAirports() {
    fetch("/get_airports")
        .then(response => {
            if(!response.ok) {
                throw new Error("Verkkopyyntö epäonnistui");
            }
            return response.json();
        })
        .then(data => {
            console.log("Läheiset lentokentät:", data);
            data.forEach(airport => {
                const lat = airport.latitude_deg;
                const lon = airport.longitude_deg;
                const a_distance = airport.distance / 1000
                const airportMarker = L.marker([lat, lon])
                    .addTo(map)
                    .bindPopup(
                        `<strong>${airport.ident}</strong><br>${airport.name}<br>${a_distance.toFixed(0)} km<br><button onclick="selectAirportFromMarker('${airport.ident}')">Valitse tämä lentokenttä</button>`
                    );
            });
        })
        .catch(error => {
            console.error("Virhe haettaessa lentokenttiä:", error);
        });
}

document.addEventListener("DOMContentLoaded", getAirports);

function selectAirportFromMarker(icao) {
    document.getElementById("icao-input").value = icao;
    selectIcao();
}

function quitGame() {
    fetch("/exit_game", {method: "POST"})
        .then(response => {
            if(!response.ok) {
                throw new Error("Palvelin ei hyväksynyt pyyntöä");
            }
            return response.text();
        })
        .then(data => {
            console.log("Palvelimen vastaus:", data);
            alert("Palvelin on suljettu. Voit nyt sulkea tämän välilehden.");
        })
        .catch(error => {
            console.error("Virhe pelin lopetuksessa:", error);
        });
}

function quitGameAndLogOut() {
    fetch("/exit_game_and_logout", {method: "POST"})
        .then(response => {
            if(!response.ok) {
                throw new Error("Palvelin ei hyväksynyt pyyntöä");
            }
            return response.text();
        })
        .then(data => {
            console.log("Palvelimen vastaus:", data);
            alert("Palvelin on suljettu. Voit nyt sulkea tämän välilehden.");
        })
        .catch(error => {
            console.error("Virhe pelin lopetuksessa:", error);
        });
}

// Funktio, joka alustaa kartan ja sijoittaa lentokoneen siihen
function initializeMap(lat, lon) {
    if (!map) {
        // Jos karttaa ei ole vielä luotu, luodaan se
        map = L.map('map').setView([lat, lon], 12);

        // Lisätään karttalaatta OpenStreetMapista
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19
        }).addTo(map)

        // Lisätään lentokoneen merkki kartalle
        marker = L.marker([lat, lon], {
            icon: getRotatedAirplaneIcon(0)
        }).addTo(map);
        lastLat = lat;
        lastLon = lon;

    } else {
        // Jos kartta on jo olemassa, päivitetään sijainti vain tarvittaessa
        if (lastLat !== lat || lastLon !== lon) {
            marker.setLatLng([lat, lon]); // Päivitetään merkin sijainti
            map.setView([lat, lon], map.getZoom(), {animate: true}); // Liikutetaan näkymää

            // Päivitetään viimeisimmät koordinaatit
            lastLat = lat;
            lastLon = lon;
        }
    }
}

// Funktio hakee sijaintitiedon palvelimelta ja päivittää kartan
async function fetchLocation() {
    try {
        let response = await fetch('/location');
        let data = await response.json(); // Muuntaa vastauksen JSON-muotoon

        if (data.lat && data.lon) {
            if (lastLat !== null && lastLon !== null) {
                // Lasketaan kulma ja päivitetään kuvake
                if (lastLat !== data.lat || lastLon !== data.lon) {
                    let angle = calculateIconAngle(lastLat, lastLon, data.lat, data.lon);
                    marker.setLatLng([data.lat, data.lon]);
                    marker.setIcon(getRotatedAirplaneIcon(angle));
                    map.setView([data.lat, data.lon], map.getZoom(), {animate: true});
                }
            } else {
                // Jos ensimmäinen kerta: pelkkä setLatLng + ikoni
                marker.setLatLng([data.lat, data.lon]);
            }

            // Päivitetään viimeisin sijainti joka tapauksessa
            lastLat = data.lat;
            lastLon = data.lon;
        }
        setTimeout(fetchLocation, 1000); // Uudelleenhaku 1 sekunnin välein
    } catch (error) {
        console.error("Virhe haettaessa sijaintia:", error);
    }
}

// Funktio hakee alkuperäisen sijainnin ja aloittaa sijaintipäivityksen, jos lentokone on ilmassa
async function fetchInitialLocation() {
    try {
        let response = await fetch('/location'); // Hakee sijaintitiedoston
        let data = await response.json(); // Muuntaa vastauksen JSON-muotoon

        if (data.lat && data.lon) {
            initializeMap(data.lat, data.lon); // Asettaa aloitussijainnin

            if (data.on_flight) {
                fetchLocation(); // Aloittaa jatkuvan sijaintipäivityksen, jos lentokone on ilmassa
            }
        }
        setTimeout(fetchLocation, 1000); // Uudelleenhaku 1 sekunnin välein
    } catch (error) {
        console.error("Virhe haettaessa sijaintia:", error);
    }
}

// Käynnistää alkuperäisen sijainninhaun, kun sivu latautuu
window.onload = fetchInitialLocation;

async function fetchUserInfo() {
    try {
        let response = await fetch("/get_user");
        let data = await response.json();
        if(data) {
            in_flight = data.in_flight;
            remaining_distance = data.remaining_distance;
            updateLighting(data.current_time);

            let infoText = `Klo: ${data.current_time}
            Käyttäjä: ${data.user_name}
                Lentoasema ${data.airport_name}
                ICAO: ${data.current_icao}
                Käteinen: ${data.cash.toFixed(2)} €
                Polttoaine: ${data.fuel.toFixed(2)} L`;

            if(in_flight) {
                infoText += `\nMatka: ${remaining_distance.toFixed(0)} km`;
                showContainer("stop-flight-container");
            } else {
                hideContainer("stop-flight-container");
            }

            document.getElementById("user-info").innerText = infoText;
        }
    } catch(error) {
        console.error("Virhe haettaessa sijaintia: ", error);
    }
}

// Päivitetään käyttäjätiedot 1 sekunnin välein
setInterval(fetchUserInfo, 1000);

function updateLighting(current_time) {
    const mapElement = document.getElementById("map");
    let hours = parseInt(current_time.split(":")[0]);
    mapElement.classList.remove("daylight", "dusk", "night");

    if (hours >= 6 && hours < 18) {
        mapElement.classList.add("daylight");
    } else if ((hours >= 18 && hours < 21) || (hours >= 3 && hours < 6)) {
        mapElement.classList.add("dusk");
    } else {
        mapElement.classList.add("night");
    }
}

function toggleFogEffect(enable) {
    const fogContainer = document.getElementById("fog-container");
    fogContainer.style.display = enable ? "block" : "none";
}

function toggleSnowEffect(enable) {
    if (enable) {
        // Jos ei ole jo lunta, lisätään
        if (weatherEffectContainer.childElementCount === 0) {
            for (let i = 0; i < 50; i++) {
                const flake = document.createElement("div");
                flake.className = "snowflake";
                flake.innerText = "❄";
                flake.style.left = Math.random() * 100 + "vw";
                flake.style.animationDuration = (Math.random() * 3 + 2) + "s";
                flake.style.fontSize = (Math.random() * 10 + 10) + "px";
                weatherEffectContainer.appendChild(flake);
            }
        }
    } else {
        weatherEffectContainer.innerHTML = ""; // Poistaa kaikki hiutaleet
    }
}

function toggleRainEffect(enable) {
    if (enable) {
        if (weatherEffectContainer.childElementCount === 0) {
            for (let i = 0; i < 100; i++) {
                const drop = document.createElement("div");
                drop.className = "raindrop";
                drop.style.left = Math.random() * 100 + "vw";
                drop.style.animationDuration = (Math.random() * 1 + 0.5) + "s";
                drop.style.animationDelay = Math.random() * 5 + "s";
                weatherEffectContainer.appendChild(drop);
            }
        }
    } else {
        weatherEffectContainer.innerHTML = "";
    }
}

function triggerLightningFlash() {
    const lightningContainer = document.getElementById("lightning-container");
    const flash = document.createElement("div");
    flash.className = "flash";
    lightningContainer.appendChild(flash);
    setTimeout(() => lightningContainer.removeChild(flash), 300);
}

function startLightningEffect(enable) {
    if (!enable) return;

    setInterval(() => {
        if (Math.random() < 0.3) { // satunnainen välähdys
            triggerLightningFlash();
        }
    }, 4000); // joka 4s mahdollisuus salamaan
}


// Haetaan reaaliaikainen sää
async function fetchWeather() {
    try {
        let response = await fetch("/get_weather");
        let data = await response.json();
        console.log("Hae sää");
        if(data.error) {
            document.getElementById("weather-info").innerText = "Säätietoja ei saatavilla.";
            console.error("Säätietojen virhe:", data.error);
            return;
        }

        document.getElementById("weather-info").innerHTML = `Sää: ${data.weather} <br>
            Lämpötila: ${data.temperature}°C <br>         
            Tuuli: ${data.wind_speed} m/s <br>
            Suunta: ${data.wind_direction}° <br>
            ${data.turbulence_warning ? "<span style='color:red;'>Varoitus: Turbulenssia!</span>" : ""}
        `;

        const conditionText = data.weather ? data.weather.toLowerCase() : "";
        toggleSnowEffect(conditionText.includes("snow") || conditionText.includes("lumi"));
        toggleRainEffect(conditionText.includes("rain") || conditionText.includes("sade"));
        toggleFogEffect(conditionText.includes("fog") || conditionText.includes("sumu"));
        startLightningEffect(conditionText.includes("thunder") || conditionText.includes("ukkonen"));

    } catch (error) {
        console.error("Virhe säätietojen haussa:", error);
        document.getElementById("weather-info").innerText = "Säätietoja ei saatavilla.";
    }
}

// Päivitetään sää automaattisesti 5 sekunnin välein
setInterval(fetchWeather, 5000);

// Haetaan sää heti sivun latautuessa
document.addEventListener("DOMContentLoaded", fetchWeather);

function selectIcao() {
    let targetIcao = document.getElementById("icao-input").value;
    let command = "select_icao";

    fetch("/select_icao", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({icao: targetIcao, command: command})
    })
        .then(response => response.json())
        .then(data => {
            if(data.success) {
                hideContainer("icao-container");
                //showContainer("stop-flight-container");
                getCoordsForIcon(targetIcao);
            }
        })
        .catch(error => {
            console.error("Virhe:", error);
        });
}

function stopFlight() {
    let command = "stop_flight";

    fetch("/stop_flight", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({command: command})
    })
        .then(response => response.json())
        .then(data => {
            if(data.success) {
                console.log("Lento pysäytetty");
            }
        })
        .catch(error => {
            console.error("Virhe:", error);
        });
}

function getCoordsForIcon(destination_icao) {
    fetch(`/get_coords_for_icon?dest_icao=${destination_icao}`)
        .then(response => response.json())
        .then(data => {
            if(data.success) {
                let angle = calculateIconAngle(data.lat1, data.lon1, data.lat2, data.lon2);
                marker.setIcon(getRotatedAirplaneIcon(angle));
            }
        })
        .catch(error => console.error("Virhe koordinaattien haussa:", error));
}

function getRotatedAirplaneIcon(angleDegrees) {
    return L.divIcon({
        className: 'rotated-airplane-icon',
        html: `
            <div class="plane-icon-wrapper" style="transform: rotate(${angleDegrees}deg);">
                ${in_flight ? `
                    <div class="trail trail-left"></div>
                    <div class="trail trail-right"></div>
                ` : ''}
                <div class="rotating-image">
                    <img src="/static/images/airplane_icon.png" class="airplane-img">
                    <div class="nav-light red"></div>
                    <div class="nav-light green"></div>
                    <div class="nav-light white"></div>
                </div>
            </div>
        `,
        iconSize: [50, 70],
        iconAnchor: [25, 25]
    });
}

function calculateIconAngle(lat1, lon1, lat2, lon2) {
    const toRadians = deg => deg * Math.PI / 180;
    const toDegrees = rad => rad * 180 / Math.PI;

    const lat1_rad = toRadians(lat1);
    const lat2_rad = toRadians(lat2);
    const delta_lambda = toRadians(lon2 - lon1);

    const y = Math.sin(delta_lambda) * Math.cos(lat2_rad);
    const x = Math.cos(lat1_rad) * Math.sin(lat2_rad) -
              Math.sin(lat1_rad) * Math.cos(lat2_rad) * Math.cos(delta_lambda);

    let angle = Math.atan2(y, x);
    let bearing = (toDegrees(angle) + 360) % 360;
    return bearing;
}

function showInputIcao() {
    showInputContainer("icao-container", "icao-input", handleSelectIcaoEnter)
}

function showInputContainer(container, input_field, handleEnterFunction) {
    showContainer(container);
    let icaoInput = document.getElementById(input_field);
    icaoInput.value = "";
    icaoInput.focus();
    icaoInput.removeEventListener("keydown", handleEnterFunction);
    icaoInput.addEventListener("keydown", handleEnterFunction);

}

function handleEnter(event, actionFunction) {
    if(event.key === "Enter") {
        actionFunction();
    }
}

function handleSelectIcaoEnter(event) {
    handleEnter(event, selectIcao);
}

function hideContainer(container) {
    document.getElementById(container).style.display = "none";
}

function showContainer(container) {
    document.getElementById(container).style.display = "block";
}