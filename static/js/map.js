// Global variables
let map; // Karttaobjekti
let marker; // Lentokoneen merkki kartalla
let destinationMarker; // Asiakkaan määränpää merkki
let destinationLine; // Linja lentokoneen ja määränpään välillä
let lastLat = null; // Viimeisin latitude (leveysaste)
let lastLon = null; // Viimeisin longitude (pituusaste)
let in_flight = false;
let destinationCheckInterval = null;

// Funktio, joka alustaa kartan ja sijoittaa lentokoneen siihen
function initializeMap(lat, lon) {
    if (!map) {
        // Jos karttaa ei ole vielä luotu, luodaan se
        map = L.map('map').setView([lat, lon], 12);

        // Lisätään karttalaatta OpenStreetMapista
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19
        }).addTo(map);

        // Lisätään lentokoneen merkki kartalle
        marker = L.marker([lat, lon], {
            icon: getRotatedAirplaneIcon(0)
        }).addTo(map);
        lastLat = lat;
        lastLon = lon;

    } else {
        // Jos kartta on jo olemassa, päivitetään sijainti vain tarvittaessa
        if (lastLat !== lat || lastLon !== lon) {
            // Lasketaan kulma ja päivitetään kuvake
            let angle = calculateIconAngle(lastLat, lastLon, lat, lon);
            marker.setLatLng([lat, lon]); // Päivitetään merkin sijainti
            marker.setIcon(getRotatedAirplaneIcon(angle));
            map.setView([lat, lon], map.getZoom(), {animate: true}); // Liikutetaan näkymää

            // Päivitetään viimeisimmät koordinaatit
            lastLat = lat;
            lastLon = lon;

            // Päivitetään myös linja määränpäähän jos se on olemassa
            updateDestinationLine(lat, lon);
        }
    }
}

// Funktio hakee ja päivittää määränpään merkin kartalle
function setupDestinationMarker(destLat, destLon, destIcao) {
    // Jos parametreja ei annettu, käytetään alkuperäistä logiikkaa
    if (arguments.length === 0) {
        // Tämä on alkuperäinen käyttötapaus, missä funktiota kutsutaan ilman parametreja
        // Haetaan asiakkaan määränpää, jos mahdollista
        if (window.CustomerManager && window.CustomerManager.currentCustomer) {
            const customerDestination = window.CustomerManager.currentCustomer.destination;
            
            // Tässä voisi hakea määränpään koordinaatit esim. erillisellä API-kutsulla
            fetch(`/get_airport_coords?icao=${customerDestination}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        setupDestinationMarker(data.lat, data.lon, customerDestination);
                    }
                })
                .catch(error => console.error("Virhe määränpään koordinaattien haussa:", error));
            
            return;
        }
    } else {
        // Jos koordinaatit annettiin, asetetaan määränpään merkki
        
        // Määritetään määränpään kuvake
        let destinationIcon = L.icon({
            iconUrl: '/static/images/destination.svg',
            iconSize: [30, 30],
            iconAnchor: [15, 15],
            popupAnchor: [0, -15]
        });

        // Jos SVG-kuvaketta ei ole, käytetään tätä varakuvaketta
        if (!destinationIcon._url) {
            destinationIcon = L.divIcon({
                className: 'destination-icon',
                html: '<div class="pin"></div>',
                iconSize: [20, 20],
                iconAnchor: [10, 20]
            });
        }

        // Asetetaan määränpään merkki kartalle
        if (map) {
            // Jos merkki on jo olemassa, poistetaan se ensin
            if (destinationMarker) {
                map.removeLayer(destinationMarker);
            }
            
            // Luodaan uusi määränpään merkki
            destinationMarker = L.marker([destLat, destLon], {
                icon: destinationIcon
            }).addTo(map);
            
            // Lisätään popup-ikkuna, joka näyttää määränpään ICAO-koodin
            destinationMarker.bindPopup(`Määränpää: ${destIcao}`);
            
            // Jos lentokoneen sijainti on tiedossa, päivitetään myös linja
            if (lastLat !== null && lastLon !== null) {
                updateDestinationLine(lastLat, lastLon);
            }
        }
    }
}

// Päivitetään linja määränpäähän
function updateDestinationLine(lat, lon) {
    if (destinationMarker && map) {
        // Jos linja on jo olemassa, poistetaan se
        if (destinationLine) {
            map.removeLayer(destinationLine);
        }

        // Luodaan uusi linja lentokoneen ja määränpään välille
        const destLatLng = destinationMarker.getLatLng();
        destinationLine = L.polyline([[lat, lon], [destLatLng.lat, destLatLng.lng]], {
            color: 'blue',
            weight: 2,
            opacity: 0.7,
            dashArray: '5, 10'
        }).addTo(map);
    }
}

// Funktio hakee sijaintitiedon palvelimelta ja päivittää kartan
async function fetchLocation() {
    try {
        let response = await fetch('/location');
        if (!response.ok) throw new Error("Virhe sijainnin haussa");
        
        let data = await response.json();

        if (data.lat && data.lon) {
            initializeMap(data.lat, data.lon); // Päivittää kartan
        }
        
        // Jatketaan sijainnin hakua riippumatta lennon tilasta,
        // alkuperäisessä koodissa sijainti päivitettiin jatkuvasti
        setTimeout(fetchLocation, 1000); // Uudelleenhaku 1 sekunnin välein
    } catch (error) {
        console.error("Virhe haettaessa sijaintia:", error);
        // Yritetään uudelleen virheen jälkeenkin
        setTimeout(fetchLocation, 1000);
    }
}

// Funktio hakee käyttäjätiedot palvelimelta
async function fetchUserInfo() {
    try {
        let response = await fetch("/get_user");
        if (!response.ok) throw new Error("Virhe käyttäjätietojen haussa");

        let data = await response.json();

        if (data) {
            // Päivitetään käyttäjätiedot näytölle selkeästi, varmistaen että ne päivittyvät
            const userInfoElement = document.getElementById("user-info");
            if (userInfoElement) {
                userInfoElement.innerHTML = `
                    Käyttäjä: ${data.user_name || 'Tuntematon'}<br>
                    Lentoasema: ${data.airport_name || 'Ei tietoa'}<br>
                    ICAO: ${data.current_icao || 'N/A'}<br>
                    Käteinen: ${data.cash ? data.cash.toFixed(2) : '0.00'} €<br>
                    Polttoaine: ${data.fuel ? data.fuel.toFixed(2) : '0.00'} L
                `;

                // Näytä päivittynyt raha konsolissa debuggausta varten
                console.log("Päivitetty raha:", data.cash ? data.cash.toFixed(2) : '0.00', "€");
            }

            // Päivitetään lennon tila
            const previousFlightState = in_flight;
            in_flight = data.in_flight || false;

            // Näytetään tai piilotetaan lennon lopetuspainike tilan mukaan
            if (in_flight) {
                showContainer("stop-flight-container");
            } else {
                hideContainer("stop-flight-container");

                // Tarkistetaan määränpään saavuttaminen vain jos olimme aiemmin lennolla
                // mutta emme ole enää (eli lento on juuri loppunut)
                if (previousFlightState && !in_flight) {
                    console.log("Lento päättyi, tarkistetaan määränpää");
                    checkDestinationArrival(data.current_icao);
                }
            }

            // Tallennetaan nykyinen ICAO-koodi session storageen
            sessionStorage.setItem('current_icao', data.current_icao || '');

            // Myös sijainnin päivitys on tärkeä
            fetchLocation();
        }
    } catch (error) {
        console.error("Virhe haettaessa käyttäjätietoja: ", error);
        document.getElementById("user-info").innerText = "Tietojen haku epäonnistui";
    }
}

// Funktio hakee inventaarion
async function fetchInventory() {
    try {
        const response = await fetch("/get_inventory");
        if (!response.ok) throw new Error("Virhe inventaarion haussa");

        const data = await response.json();

        if (data.error) {
            document.getElementById("inventory-items").innerHTML = `<p>Virhe: ${data.error}</p>`;
            return;
        }

        const inventory = data.inventory || {};
        updateInventoryDisplay(inventory);
    } catch (error) {
        console.error("Virhe inventaarion haussa:", error);
        document.getElementById("inventory-items").innerHTML = "<p>Inventaarion haku epäonnistui</p>";
    }
}

// Päivitetään inventaarion näkymä
function updateInventoryDisplay(inventory) {
    const inventoryItems = document.getElementById("inventory-items");

    if (!inventoryItems) return;

    const items = [
        { name: 'fruits', label: 'Hedelmät', emoji: '🍎' },
        { name: 'alcohol', label: 'Alkoholi', emoji: '🍷' },
        { name: 'snacks', label: 'Välipalat', emoji: '🍫' },
        { name: 'soda', label: 'Virvoitusjuomat', emoji: '🥤' },
        { name: 'meals', label: 'Ateriat', emoji: '🍲' },
        { name: 'water', label: 'Vesi', emoji: '💧' }
    ];

    let html = '';

    items.forEach(item => {
        const amount = inventory[item.name] || 0;
        if (amount > 0) {
            html += `
                <div class="inventory-item">
                    <div class="item-icon">${item.emoji}</div>
                    <div class="item-details">
                        <span class="item-name">${item.label}</span>
                        <span class="item-amount">${amount}</span>
                    </div>
                </div>
                <button class="use-item-btn" onclick="useItem('${item.name}')">Käytä</button>
            `;
        }
    });

    inventoryItems.innerHTML = html || '<p>Ei tuotteita inventaariossa</p>';
}

// Käytä inventaariosta tuotetta
function useItem(itemName) {
    fetch("/use_item", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ item_name: itemName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(`${getItemLabel(itemName)} käytetty! ${data.customer_name} on ${getMoodEmoji(data.mood)}`, "success");
            fetchInventory(); // Päivitetään inventaario käytön jälkeen
        } else {
            showNotification(data.message || "Tuotteen käyttö epäonnistui", "error");
        }
    })
    .catch(error => {
        console.error("Virhe tuotteen käytössä:", error);
        showNotification("Yhteysvirhe tuotetta käytettäessä", "error");
    });
}

// Apufunktio tuotteen nimen muuntamiseen
function getItemLabel(itemName) {
    const itemLabels = {
        'fruits': 'Hedelmät',
        'alcohol': 'Alkoholi',
        'snacks': 'Välipalat',
        'soda': 'Virvoitusjuomat',
        'meals': 'Ateriat',
        'water': 'Vesi'
    };

    return itemLabels[itemName] || itemName;
}

// Apufunktio mielentilan emojin saamiseen
function getMoodEmoji(mood) {
    if (!mood) return '';

    const moodValue = parseInt(mood);

    if (isNaN(moodValue)) {
        // Jos mood on tekstimuotoinen kuvaus
        const moodEmojis = {
            'happy': 'tyytyväinen 😊',
            'neutral': 'neutraali 😐',
            'angry': 'vihainen 😠',
            'satisfied': 'tyytyväinen 😊',
            'annoyed': 'ärtynyt 😤',
            'excited': 'innostunut 😃'
        };
        return moodEmojis[mood.toLowerCase()] || mood;
    } else {
        // Jos mood on numero
        if (moodValue >= 8) return 'tyytyväinen 😊';
        if (moodValue >= 6) return 'neutraali 🙂';
        if (moodValue <= 3) return 'vihainen 😠';
        return 'mietteliäs 😐';
    }
}

// Tarkistetaan, onko saavuttu määränpäähän
function checkDestinationArrival(currentIcao) {
    console.log("Tarkistetaan määränpäähän saapumista, nykyinen ICAO:", currentIcao);

    // Jos asiakastieto on saatavilla ja olemme saapuneet asiakkaan määränpäähän
    if (window.CustomerManager && window.CustomerManager.currentCustomer) {
        const customerDestination = window.CustomerManager.currentCustomer.destination;
        console.log("Asiakkaan määränpää:", customerDestination);

        // Tarkistetaan, onko nykyinen ICAO sama kuin asiakkaan määränpää
        if (currentIcao === customerDestination) {
            console.log("MÄÄRÄNPÄÄTÄ VASTAA! Saavuttu kohteeseen:", customerDestination);

            // Luodaan ja lähetetään tapahtuma määränpään saavuttamisesta
            const arrivalEvent = new CustomEvent('customerReachedDestination');
            document.dispatchEvent(arrivalEvent);

            // Näytetään ilmoitus saapumisesta
            showNotification(`Saavuttu määränpäähän: ${customerDestination}!`, 'success');

            // Tarkistetaan asiakkaan saapuminen ja päivitetään rahavarat
            checkCustomerPayment();

            return true;
        } else {
            console.log("Ei vielä perillä. Nykyinen:", currentIcao, "Määränpää:", customerDestination);
        }
    } else {
        console.log("CustomerManager ei saatavilla tai ei nykyistä asiakasta");
    }
    return false;
}

// Tarkistetaan asiakkaan maksutapahtuma
function checkCustomerPayment() {
    fetch("/check_customer_arrival", { method: "POST" })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(`Asiakas saapui! Rahaa saatu: ${data.payment.toFixed(2)} €`, 'success');

                // Pakota välitön tietojen päivitys
                fetchUserInfo();

                // Varmistetaan tietojen päivitys useammalla aikavälillä
                // backend-päivityksen viiveen vuoksi
                setTimeout(fetchUserInfo, 500);
                setTimeout(fetchUserInfo, 1000);
                setTimeout(fetchUserInfo, 2000);

                // Pakottava DOM-päivitys käyttäjätiedoille
                if (data.user_data) {
                    updateUserInfoDirectly(data.user_data);
                }

                // Siivoa määränpää-merkki kartalta
                if (destinationMarker) {
                    map.removeLayer(destinationMarker);
                    destinationMarker = null;
                }
                if (destinationLine) {
                    map.removeLayer(destinationLine);
                    destinationLine = null;
                }
            } else {
                console.log(data.message || "Asiakastarkistus ei tuottanut tulosta");
            }
        })
        .catch(error => {
            console.error("Virhe asiakastarkistuksessa:", error);
            showNotification("Virhe asiakastarkistuksessa", 'error');
        });
}

// Apufunktio, joka päivittää käyttäjätiedot suoraan DOM:iin
function updateUserInfoDirectly(userData) {
    const userInfoElement = document.getElementById("user-info");
    if (userInfoElement && userData) {
        userInfoElement.innerHTML = `
            Käyttäjä: ${userData.user_name || 'Tuntematon'}<br>
            Lentoasema: ${userData.airport_name || 'Ei tietoa'}<br>
            ICAO: ${userData.current_icao || 'N/A'}<br>
            Käteinen: ${userData.cash ? userData.cash.toFixed(2) : '0.00'} €<br>
            Polttoaine: ${userData.fuel ? userData.fuel.toFixed(2) : '0.00'} L
        `;
        console.log("Käyttäjätiedot päivitetty suoraan!", userData);
    }
}

// Haetaan säätiedot
async function fetchWeather() {
    try {
        let response = await fetch("/get_weather");
        if (!response.ok) throw new Error("Virhe säätietojen haussa");
        
        let data = await response.json();

        if (data.error) {
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

// Näytetään ilmoitus käyttäjälle
function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    if (!notification) {
        // Jos ilmoituselementtiä ei ole, luodaan se
        const notif = document.createElement('div');
        notif.id = 'notification';
        notif.className = 'notification ' + type;
        document.body.appendChild(notif);
    }
    
    notification.textContent = message;
    notification.className = 'notification ' + type;
    notification.style.display = 'block';

    setTimeout(() => {
        notification.style.display = 'none';
    }, 3000);
}

// Näytetään ICAO-syöttökenttä
function showInputIcao() {
    showInputContainer("icao-container", "icao-input", handleSelectIcaoEnter);
}

// Näytetään syöttökenttä
function showInputContainer(container, input_field, handleEnterFunction) {
    showContainer(container);
    let input = document.getElementById(input_field);
    input.value = "";
    input.focus();
    input.removeEventListener("keydown", handleEnterFunction);
    input.addEventListener("keydown", handleEnterFunction);
}

// Käsitellään Enter-näppäimen painallus
function handleEnter(event, actionFunction) {
    if (event.key === "Enter") {
        actionFunction();
    }
}

// ICAO-koodin valitseminen Enter-näppäimellä
function handleSelectIcaoEnter(event) {
    handleEnter(event, selectIcao);
}

// Piilotetaan säiliö
function hideContainer(container) {
    const containerElement = document.getElementById(container);
    if (containerElement) {
        containerElement.style.display = "none";
    }
}

// Näytetään säiliö
function showContainer(container) {
    const containerElement = document.getElementById(container);
    if (containerElement) {
        containerElement.style.display = "block";
    }
}

// Valitaan ICAO-koodi lentoa varten
function selectIcao() {
    let targetIcao = document.getElementById("icao-input").value;
    if (!targetIcao || targetIcao.trim() === '') {
        showNotification("Anna kelvollinen ICAO-koodi", "error");
        return;
    }
    
    fetch("/select_icao", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({icao: targetIcao, command: "select_icao"})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            hideContainer("icao-container");
            showContainer("stop-flight-container");
            in_flight = true;
            showNotification(`Lento kohteeseen ${targetIcao} aloitettu!`, "success");
            getCoordsForIcon(targetIcao);
            fetchLocation(); // Aloitetaan sijainnin päivitys
        } else {
            showNotification(data.message || "Virhe ICAO-koodin valinnassa", "error");
        }
    })
    .catch(error => {
        console.error("Virhe:", error);
        showNotification("Yhteysvirhe ICAO-koodin valinnassa", "error");
    });
}

// Pysäytetään lento
function stopFlight() {
    fetch("/stop_flight", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({command: "stop_flight"})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            in_flight = false;
            hideContainer("stop-flight-container");
            showNotification("Lento pysäytetty", "success");

            // Pakota määränpään tarkistus jos annettu data sisältää ICAO-koodin
            if (data.current_icao) {
                console.log("Tarkistetaan määränpää lennon pysähdyttyä");
                checkDestinationArrival(data.current_icao);
            }

            // Päivitä käyttäjätiedot
            fetchUserInfo();
        } else {
            showNotification(data.message || "Virhe lennon pysäytyksessä", "error");
        }
    })
    .catch(error => {
        console.error("Virhe:", error);
        showNotification("Yhteysvirhe lennon pysäytyksessä", "error");
    });
}

// Haetaan koordinaatit ikonia varten
function getCoordsForIcon(destination_icao) {
    fetch(`/get_coords_for_icon?dest_icao=${destination_icao}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                let angle = calculateIconAngle(data.lat1, data.lon1, data.lat2, data.lon2);
                if (marker) {
                    marker.setIcon(getRotatedAirplaneIcon(angle));
                }
                
                // Asetetaan myös määränpään merkki kartalle
                setupDestinationMarker(data.lat2, data.lon2, destination_icao);
            }
        })
        .catch(error => console.error("Virhe koordinaattien haussa:", error));
}

// Palautetaan käännetty lentokone-ikoni
function getRotatedAirplaneIcon(angleDegrees) {
    return L.divIcon({
        className: 'rotated-airplane-icon',
        html: `<img src="/static/images/airplane.svg" style="width: 50px; height: 50px; transform: rotate(${angleDegrees}deg);">`,
        iconSize: [50, 50],
        iconAnchor: [25, 25]
    });
}

// Lasketaan ikonin kulma
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

// Siirtyminen kauppaan
function goToShop() {
    console.log("Siirrytään kauppaan...");
    window.location.href = "shop.html";
}

// Siirtyminen asiakassivulle
function goToCustomers() {
    console.log("Siirrytään matkustajiin...");
    window.location.href = "customers.html";
}

// Tallennetaan ja lopetetaan peli
function quitAndSave() {
    console.log("Tallennetaan ja lopetetaan...");
    fetch("/quit_and_save", {method: "POST"})
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert("Peli tallennettu. Voit nyt sulkea tämän välilehden.");
                window.location.href = "/";
            } else {
                showNotification(data.message || "Virhe tallennuksessa", "error");
            }
        })
        .catch(error => {
            console.error("Virhe tallennuksessa:", error);
            showNotification("Yhteysvirhe tallennuksessa", "error");
        });
}

// Lopetetaan peli
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
            showNotification("Virhe pelin lopetuksessa", "error");
        });
}

// Lopetetaan peli ja kirjaudutaan ulos
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
            alert("Palvelin on suljettu ja olet kirjautunut ulos. Voit nyt sulkea tämän välilehden.");
        })
        .catch(error => {
            console.error("Virhe pelin lopetuksessa:", error);
            showNotification("Virhe pelin lopetuksessa ja uloskirjautumisessa", "error");
        });
}

// Päivitysajastimet
let userInfoTimer, inventoryTimer, weatherTimer;

// Käynnistetään ajastimet sivun latautuessa
window.onload = function() {
    // Haetaan sijainti ja käynnistetään jatkuva päivitys
    // (alkuperäinen logiikka oli fetchInitialLocation-funktiossa)
    fetchLocation();

     destinationCheckInterval = setInterval(() => {
        const currentIcao = sessionStorage.getItem('current_icao') || '';
        if (currentIcao) {
            console.log("Intervalli-tarkistus määränpäälle:", currentIcao);
            checkDestinationArrival(currentIcao);
        }
    }, 5000);

    // Haetaan muut tiedot heti alussa
    fetchUserInfo();
    fetchInventory();
    fetchWeather();
    
    // Asetetaan ajastimet säännölliselle päivitykselle
    userInfoTimer = setInterval(fetchUserInfo, 1000);     // Käyttäjätiedot 1 sekunnin välein
    inventoryTimer = setInterval(fetchInventory, 5000);   // Inventaario 5 sekunnin välein
    weatherTimer = setInterval(fetchWeather, 5000);       // Sää 5 sekunnin välein
    
    // Alkuperäisessä koodissa kutsuttiin myös tätä:
    setupDestinationMarker();
};

// Puhdistetaan ajastimet sivulta poistuttaessa
window.onbeforeunload = function() {
    clearInterval(userInfoTimer);
    clearInterval(inventoryTimer);
    clearInterval(weatherTimer);
    clearInterval(destinationCheckInterval);
}