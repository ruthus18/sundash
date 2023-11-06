let socket = new WebSocket("ws:/127.0.0.1:5000/");

let Command = {
    clear_layout: "clear_layout",
    append_component: "append_component",
    update_var: "update_var",
}


socket.onopen = event => {
    console.log(`[WS] CONN_OPEN: ${event.target.url}`)
    socket.send('LOGIN')
}

socket.onmessage = event => {
    console.log(`[WS] DATA_RECV: ${event.data}`)
    if (event.data === 'LOGIN OK') {
        return
    }

    let [name, ...data] = event.data.split(" ")
    data = data.join(" ")

    if (name == Command.clear_layout) {
        clear_layout()
    }
    else {
        console.error(`dispatching error: ${event.data}`)
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


function clear_layout(data) {
    console.log(`need to clear layout: ${data}`)
}
