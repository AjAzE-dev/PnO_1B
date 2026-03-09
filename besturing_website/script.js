let socket = undefined;

function connect_socket() {
    // Close any existing sockets
    disconnect_socket();

    socket = new WebSocket("ws://192.168.4.1:80/connect-websocket");

    // Connection opened
    socket.addEventListener("open", (event) => {
        document.getElementById("status").textContent = "Status: Connected";
    });

    socket.addEventListener("close", (event) => {
        socket = undefined;
        document.getElementById("status").textContent = "Status: Disconnected";
    });

    socket.addEventListener("message", (event) => {
        console.log(event.data)
    });

    socket.addEventListener("error", (event) => {
        socket = undefined;
        document.getElementById("status").textContent = "Status: Disconnected";
    });
}

function disconnect_socket() {
    if(socket != undefined) {
        socket.close();
    }
}

function sendCommand(command) {
    if(socket != undefined) {
        socket.send(command)
    } else {
        alert("Not connected to the PICO")
    }
}