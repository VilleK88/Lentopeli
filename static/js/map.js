var map; // Karttaobjekti
var marker; // Lentokoneen merkki kartalla
var lastLat = null; // Viimeisin latitude (leveysaste)
var lastLon = null; // Viimeisin longitude (pituusaste)

// Määritetään lentokoneen kuvake kartalle
/*var airplaneIcon = L.icon({
    iconUrl: '/static/images/airplane_icon.png', // Kuvake tiedostosta airplane.svg
    iconSize: [50, 50], // Kuvakkeen koko
    iconAnchor: [25, 25], // Ankkurointipiste kuvan sisällä
    popupAnchor: [0, -25] // Ponnahdusikkunan ankkuripiste
});*/

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
            //window.close();
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
            document.getElementById("user-info").innerText =
                `Käyttäjä: ${data.user_name}
                Lentoasema ${data.airport_name}
                ICAO: ${data.current_icao}
                Käteinen: ${data.cash.toFixed(2)} €
                Polttoaine: ${data.fuel.toFixed(2)} L`;
        }
    } catch(error) {
        console.error("Virhe haettaessa sijaintia: ", error);
    }
}

// Päivitetään käyttäjätiedot 1 sekunnin välein
setInterval(fetchUserInfo, 1000);

// Haetaan reaaliaikainen sää
async function fetchWeather() {
    try {
        let response = await fetch("/get_weather");
        let data = await response.json();

        if(data.error) {
            document.getElementById("weather-info").innerText = "Säätietoja ei saatavilla.";
            console.error("Säätietojen virhe:", data.error);
            return;
        }

        document.getElementById("weather-info").innerHTML = `
            Lämpötila: ${data.temperature}°C <br>
            Tuuli: ${data.wind_speed} m/s <br>
            Suunta: ${data.wind_direction}° <br>
            ${data.turbulence_warning ? "<span style='color:red;'>Varoitus: Turbulenssia!</span>" : ""}
        `;
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
                showContainer("stop-flight-container");
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
        html: `<img src="/static/images/airplane_icon.png" style="width: 50px; height: 50px; transform: rotate(${angleDegrees}deg);">`,
        iconSize: [50, 50],
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