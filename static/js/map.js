var map; // Karttaobjekti
var marker; // Lentokoneen merkki kartalla
var lastLat = null; // Viimeisin latitude (leveysaste)
var lastLon = null; // Viimeisin longitude (pituusaste)

// Määritetään lentokoneen kuvake kartalle
var airplaneIcon = L.icon({
    iconUrl: '/static/images/airplane.svg', // Kuvake tiedostosta airplane.svg
    iconSize: [50, 50], // Kuvakkeen koko
    iconAnchor: [25, 25], // Ankkurointipiste kuvan sisällä
    popupAnchor: [0, -25] // Ponnahdusikkunan ankkuripiste
});

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
        marker = L.marker([lat, lon], {icon: airplaneIcon}).addTo(map);
    } else {
        // Jos kartta on jo olemassa, päivitetään sijainti vain tarvittaessa
        if (lastLat !== lat || lastLon !== lon) {
            marker.setLatLng([lat, lon]) // Päivitetään merkin sijainti
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
        //let response = await fetch('location.json'); // Hakee sijaintitiedoston
        let response = await fetch('/location');
        let data = await response.json(); // Muuntaa vastauksen JSON-muotoon

        if (data.lat && data.lon) {
            initializeMap(data.lat, data.lon) // Päivittää kartan
        }
        setTimeout(fetchLocation, 1000); // Uudelleenhaku 1 sekunnin välein
    } catch (error) {
        console.error("Virhe haettaessa sijaintia:", error);
    }
}

// Funktio hakee alkuperäisen sijainnin ja aloittaa sijaintipäivityksen, jos lentokone on ilmassa
async function fetchInitialLocation() {
    try {
        //let response = await fetch('location.json'); // Hakee sijaintitiedoston
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

function fetchUserInfo() {
    fetch("/get_user")
        .then(response => response.json())
        .then(data => {
            document.getElementById("user-info").innerText =
                `Käyttäjä: ${data.user_name}
                Lentoasema: ${data.airport_name}
                ICAO: ${data.current_icao}
                Käteinen: ${data.cash} €
                Polttoaine: ${data.fuel} L`;
        })
        .catch(error => {
            console.error("Virhe käyttäjätietojen haussa:", error);
            document.getElementById("user-info").innerText = "Tietojen haku epäonnistui";
        });
}
document.addEventListener("DOMContentLoaded", fetchUserInfo)

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