console.log("Hello Sundate!!!")

let socket = new WebSocket("ws:/127.0.0.1:5000/");

let Signal = {
    CLIENT_CONNECTED: "CLIENT_CONNECTED",
    CLIENT_DISCONNECTED: "CLIENT_DISCONNECTED",
    LAYOUT_CLEAN: "LAYOUT_CLEAN",
    LAYOUT_UPDATED: "LAYOUT_UPDATED",
    EVERY_SECOND: "EVERY_SECOND",
    VAR_UPDATED: "VAR_UPDATED",
}

let Command = {
    clear_layout: "clear_layout",
    append_component: "append_component",
    update_var: "update_var",
}


function _handle_signal(signal, data) {
    
}


function on_clear_layout() {


}


function _handele_command(command, data) {
    let callback = Command[command]
    console.log(callback)
}


socket.onopen = event => {
    console.log(event)
    console.log(`[WS] CONN_OPEN: ${event.target.url}`)

    const msg = Signal.CLIENT_CONNECTED + ' ' + JSON.stringify({'user': 'default'})
    socket.send(msg)
    console.log(`[WS] DATA_SENT: ${msg}`)
}

socket.onmessage = event => {
    console.log(`[WS] DATA_RECV: ${event.data}`)

    let [name, ...data] = event.data.split(" ")
    data = data.join(" ")

    if (name[0] == name[0].toUpperCase()) {
        _handle_signal(name, data)
    }
    else if (name[0] == name[0].toLowerCase()){
        _handle_command(name, data)
    }
    else {
        alert('dispatching error')
    }
}


socket.onclose = event => {
    if (event.wasClean) {
        console.log(`[WS] CONN_CLOSED: code=${event.code} reason=${event.reason}`)

    } else {
       // например, сервер убил процесс или сеть недоступна; обычно в этом случае event.code 1006
        console.log('[WS] CONN_ABORTED')
    }
}


socket.onerror = error => {
    console.log(`[WS] ERROR`)
    console.log(error)
}