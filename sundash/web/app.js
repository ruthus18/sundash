console.log("Hello Sundate!!!")

const el = document.getElementById("app")
// el.innerHTML = ""


let socket = new WebSocket("ws:/127.0.0.1:5000");

let Signal = {
    CLIENT_CONNECTED: "CLIENT_CONNECTED",
    CLIENT_DISCONNECTED: "CLIENT_DISCONNECTED",
    LAYOUT_CLEAN: "LAYOUT_CLEAN",
    LAYOUT_UPDATED: "LAYOUT_UPDATED",
    EVERY_SECOND: "EVERY_SECOND",
    VAR_UPDATED: "VAR_UPDATED",
}


socket.onopen = event => {
    console.log(event)
    console.log(`[WS] CONN_OPEN: ${event.target.url}`)

    const msg = Signal.CLIENT_CONNECTED + ' ' + JSON.stringify({'user': 'default'})
    socket.send(msg)
    console.log(`[WS] DATA_SENT: ${msg}]`)
};

socket.onmessage = event => {
    console.log(`[WS] DATA_RECV: ${event.data}`)
};


socket.onclose = event => {
    if (event.wasClean) {
        console.log(`[WS] CONN_CLOSED: code=${event.code} reason=${event.reason}`)

    } else {
    // например, сервер убил процесс или сеть недоступна; обычно в этом случае event.code 1006
        console.log('[WS] CONN_ABORTED')
    }
};


socket.onerror = error => {
    console.log(`[WS] ERROR`)
    console.log(error)
};