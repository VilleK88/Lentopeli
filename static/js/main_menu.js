let users = [];
let currentPage = 0;
const usersPerPage = 10;

function showUserNameInput() {
    hideUserList();
    document.getElementById("username-container").style.display = "block";
    let usernameInput = document.getElementById("username_input");
    usernameInput.value = "";
    usernameInput.focus();
    usernameInput.removeEventListener("keydown", handleSelectUserEnter);
    usernameInput.addEventListener("keydown", handleSelectUserEnter);
}

function handleSelectUserEnter(event) {
    if(event.key === "Enter") {
        selectUser();
    }
}

function fetchUserInfo() {
    fetch("/get_user")
        .then(response => response.json())
        .then(data => {
            document.getElementById("user-info").innerText =
                `Käyttäjä: ${data.user_name}
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