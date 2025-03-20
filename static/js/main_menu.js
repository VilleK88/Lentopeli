let users = [];
let currentPage = 0;
const usersPerPage = 10;

function showUserNameInput() {
    showInputContainer("username-container", "username_input", handleSelectUserEnter);
}

function showAddNewUserInput() {
    document.getElementById("add-user-message").innerText = "";
    showInputContainer("add-user-container", "new-username", handleNewUserEnter);
    document.getElementById("add-user-message").style.display = "block";
}

function showInputContainer(container, input_field, handleEnterFunction) {
    hideUserList();
    hideUserNameContainer();
    hideNewUserContainer();
    document.getElementById("add-user-message").style.display = "none";
    document.getElementById(container).style.display = "block";
    let usernameInput = document.getElementById(input_field);
    usernameInput.value = "";
    usernameInput.focus();
    usernameInput.removeEventListener("keydown", handleEnterFunction);
    usernameInput.addEventListener("keydown", handleEnterFunction);
}

function handleEnter(event, actionFunction) {
    if(event.key === "Enter") {
        actionFunction();
    }
}

function handleSelectUserEnter(event) {
    handleEnter(event, selectUser);
}

function handleNewUserEnter(event) {
    handleEnter(event, addUser);
}

function closeGame() {
    window.close();
}

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

function selectUser() {
    let userName = document.getElementById("username_input").value;
    let command = "select_user";

    fetch("/select_user", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({user_name: userName, command: command})
    })
        .then(response => response.json())
        .then(data => {
            if(data.success) {
                document.getElementById("user-info").innerText = data.message;
                fetchUserInfo();
                document.getElementById("username-container").style.display = "none";
            }
        })
        .catch(error => {
            console.error("Virhe:", error);
            document.getElementById("user_info").innerText = "Virhe käyttäjän valinnassa";
        });
}

function addUser() {
    let name = document.getElementById("new-username").value.trim();

    if (!name) {
        document.getElementById("add-user-message").innerText = "Nimi ei voi olla tyhjä!";
        return;
    }

    fetch("/add_user", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({name: name})
    })
        .then(response => response.json())
        .then(data => {
            document.getElementById("add-user-message").innerText = data.message;
            document.getElementById("add-user-container").style.display = "none";

            if(data.success) {
                document.getElementById("new-username").value = "";
            }
        })
        .catch(error => {
            console.error("Virhe käyttäjän lisäyksessä:", error);
            document.getElementById("add-user-message").innerText = "Käyttäjän lisääminen tietokantaan epäonnistui.";
        });
}

function fetchUsers() {
    fetch("/get_users")
        .then(response => response.json())
        .then(data => {
            users = data;
            currentPage = 0;
            displayUsers();
            let userListContainer = document.getElementById("user-list-container");
            userListContainer.style.display = "block";
        })
        .catch(error => {
            console.error("Virhe käyttäjälistan haussa:", error);
            document.getElementById("user-list").innerText = "Virhe käyttäjälistan haussa.";
        });
}

function displayUsers() {
    hideUserNameContainer();
    hideNewUserContainer();
    let userListContainer= document.getElementById("user-list");
    userListContainer.innerHTML = ""
    let start = currentPage * usersPerPage;
    let end = start + usersPerPage;
    let paginatedUsers = users.slice(start, end);

    if(paginatedUsers.length > 0) {
        paginatedUsers.forEach(user => {
            let listItem = document.createElement("li");
            listItem.textContent = user.screen_name;
            userListContainer.appendChild(listItem);
        });
    } else {
        userListContainer.innerText = "Ei käyttäjiä.";
    }
    updatePaginationButtons();
}

function nextPage() {
    if((currentPage + 1) * usersPerPage < users.length) {
        currentPage++;
        displayUsers();
    }
}

function prevPage() {
    if(currentPage > 0) {
        currentPage--;
        displayUsers();
    }
}

function updatePaginationButtons() {
    document.getElementById("prev-page").style.display = currentPage > 0 ? "inline-block" : "none";
    document.getElementById("next-page").style.display = (currentPage + 1) * usersPerPage < users.length ? "inline-block" : "none";
}

function hideUserList() {
    document.getElementById("user-list-container").style.display = "none";
}

function hideUserNameContainer() {
    document.getElementById("username-container").style.display = "none";
}

function hideNewUserContainer() {
    document.getElementById("add-user-container").style.display = "none";
}