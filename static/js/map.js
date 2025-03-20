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
    if(!map) {
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
        if(lastLat !== lat || lastLon !== lon) {
            marker.setLatLng([lat, lon]) // Päivitetään merkin sijainti
            map.setView([lat, lon], map.getZoom(), {animate: true }); // Liikutetaan näkymää

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

        if(data.lat && data.lon) {
            initializeMap(data.lat, data.lon) // Päivittää kartan
        }
        setTimeout(fetchLocation, 3000); // Uudelleenhaku 1 sekunnin välein
    } catch(error) {
        console.error("Virhe haettaessa sijaintia:", error);
    }
}

// Funktio hakee alkuperäisen sijainnin ja aloittaa sijaintipäivityksen, jos lentokone on ilmassa
async function fetchInitialLocation() {
    try {
        let response = await fetch('location.json'); // Hakee sijaintitiedoston
        let data = await response.json(); // Muuntaa vastauksen JSON-muotoon

        if(data.lat && data.lon) {
            initializeMap(data.lat, data.lon); // Asettaa aloitussijainnin

            if(data.on_flight) {
                fetchLocation(); // Aloittaa jatkuvan sijaintipäivityksen, jos lentokone on ilmassa
            }
        }
        setTimeout(fetchLocation, 1000); // Uudelleenhaku 1 sekunnin välein
    } catch(error) {
        console.error("Virhe haettaessa sijaintia:", error);
    }
}

// Käynnistää alkuperäisen sijainninhaun, kun sivu latautuu
window.onload = fetchInitialLocation;