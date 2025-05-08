// Globaali muuttuja käteisen määrälle
let playerCash = 0;
let playerFuel = 0;

// Ladataan kaupan tuotteet palvelimelta
async function loadShopItems() {
  try {
    // Haetaan ensin pelaajan tiedot
    const userResponse = await fetch('/get_user');
    const userData = await userResponse.json();
    playerCash = userData.cash;
    playerFuel = userData.fuel;

    // Päivitetään pelaajan tiedot näytölle
    updatePlayerInfo(userData);

    // Haetaan tuotteet palvelimelta
    const response = await fetch('/get_shop_items');
    if (!response.ok) {
      throw new Error('Verkkovirhe');
    }

    const data = await response.json();

    // Tarkista, että tuotteet on saatu ja lisää ne sivulle
    if (data.products) {
      const itemsContainer = document.getElementById('shop-items');
      itemsContainer.innerHTML = ''; // Tyhjennetään alkuperäinen sisältö

      // Luodaan tuotekortit
      data.products.forEach(product => {
        const productCard = document.createElement('div');
        productCard.classList.add('product-card');

        // Lisätään tuotteen tiedot korttiin
        productCard.innerHTML = `
          <h3>${product.name}</h3>
          <p class="product-description">${product.description || ''}</p>
          <p class="product-price">${product.price}€</p>
          <button class="buy-button" onclick="buyProduct('${product.name}', ${product.price})">Osta</button>
        `;

        itemsContainer.appendChild(productCard);
      });
    } else {
      console.error('Tuotteita ei löytynyt');
    }
  } catch (error) {
    console.error('Virhe tuotteiden lataamisessa:', error);
    document.getElementById('shop-items').innerHTML = '<p class="error">Tuotteiden lataus epäonnistui. Yritä uudelleen myöhemmin.</p>';
  }
}

// Päivitetään pelaajan tiedot näytölle
function updatePlayerInfo(userData) {
  const infoElement = document.getElementById('player-info');
  if (infoElement) {
    infoElement.innerHTML = `
      <p>Pelaaja: ${userData.user_name}</p>
      <p>Käteinen: <span id="cash-amount">${userData.cash}</span>€</p>
      <p>Polttoaine: ${userData.fuel} litraa</p>
    `;
  }
}

// Ostetaan tuote
async function buyProduct(productName, price) {
  if (playerCash < price) {
    showNotification('Ei tarpeeksi rahaa!', 'error');
    return;
  }

  try {
    const response = await fetch('/buy_item', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ product_name: productName })
    });

    const data = await response.json();

    if (data.success) {
      // Päivitetään pelaajan käteinen
      playerCash -= price;
      document.getElementById('cash-amount').textContent = playerCash;

      showNotification(`Ostit tuotteen: ${productName}`, 'success');

      // Haetaan päivitetyt pelaajan tiedot
      refreshPlayerInfo();
    } else {
      showNotification(data.message || 'Osto epäonnistui', 'error');
    }
  } catch (error) {
    console.error('Virhe tuotteen ostamisessa:', error);
    showNotification('Virhe yhteydessä palvelimeen', 'error');
  }
}

// Näytetään ilmoitus käyttäjälle
function showNotification(message, type = 'info') {
  const notification = document.getElementById('notification') || createNotificationElement();

  notification.textContent = message;
  notification.className = 'notification ' + type;

  notification.style.display = 'block';

  // Piilotetaan ilmoitus 3 sekunnin kuluttua
  setTimeout(() => {
    notification.style.display = 'none';
  }, 3000);
}

// Luodaan ilmoituselementti, jos sitä ei ole
function createNotificationElement() {
  const notification = document.createElement('div');
  notification.id = 'notification';
  notification.className = 'notification';
  document.body.appendChild(notification);
  return notification;
}

// Päivitetään pelaajan tiedot
async function refreshPlayerInfo() {
  try {
    const response = await fetch('/get_user');
    const userData = await response.json();
    playerCash = userData.cash;
    playerFuel = userData.fuel;
    updatePlayerInfo(userData);
  } catch (error) {
    console.error('Virhe pelaajan tietojen päivittämisessä:', error);
  }
}

// Suoritetaan, kun sivu on latautunut
window.onload = function() {
  loadShopItems();
};