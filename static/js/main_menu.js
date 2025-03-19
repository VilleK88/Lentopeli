function showUserNameInput() {
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