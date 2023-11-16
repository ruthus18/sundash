let socket = new WebSocket("ws:/127.0.0.1:5000/");

let Command = {
    clear_layout: "clear_layout",
    append_component: "append_component",
    update_var: "update_var",
}


socket.onopen = event => {
    console.log(`[WS] CONN_OPEN: ${event.target.url}`)
}

socket.onmessage = event => {
    console.log(`[WS] DATA_RECV: ${event.data}`)
    let [name, ...data] = event.data.split(" ")
    data = data.join(" ")
    if (data != undefined) {
        data = JSON.parse(data)
    }

    if (name == Command.clear_layout) {
        clear_layout()
    }
    else if (name == Command.append_component) {
        append_component(data)
    }
    else if (name == Command.update_var) {
        update_var(data)
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


const el = document.getElementById("app")


function clear_layout() {
    el.innerHTML = ""
    socket.send('LAYOUT_CLEAN {}')
}


function append_component(data) {
    el.innerHTML += data.html
    socket.send('LAYOUT_UPDATED {}')

    el._orig_html = el.innerHTML
}


function update_var(data) {
    el.innerHTML = el._orig_html.replace(`{{ ${data.name} }}`, data.value)
    socket.send('VAR_UPDATED {}')
}
