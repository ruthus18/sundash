let socket = new WebSocket("ws:/127.0.0.1:5000/");

let Command = {
    CLEAR_LAYOUT: "CLEAR_LAYOUT",
    UPDATE_LAYOUT: "UPDATE_LAYOUT",
    UPDATE_VAR: "UPDATE_VAR",
}


socket.onopen = event => {
    console.log(`[WS] CONN_OPEN: ${event.target.url}`)
}

socket.onmessage = event => {
    let [name, ...data] = event.data.split(" ")
    data = data.join(" ")
    console.log(`${name} ${data}`)

    if (data != undefined) {
        data = JSON.parse(data)
    }

    if (name == Command.CLEAR_LAYOUT) {
        clear_layout()
    }
    else if (name == Command.UPDATE_LAYOUT) {
        update_layout(data)
    }
    else if (name == Command.UPDATE_VAR) {
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
    el.innerHTML = ''
    socket.send('LAYOUT_CLEAN {}')
}


function update_layout(data) {
    el.innerHTML = ''
    el.__html = data.html
    el.__vars = data.vars

    let response_html = el.__html
    for (let key in el.__vars) {
        let value = el.__vars[key]
        response_html = response_html.replace(`{{ ${key} }}`, value)
    }

    el.innerHTML = response_html
    socket.send('LAYOUT_UPDATED {}')

}


function update_var(data) {
    el.innerHTML = el._orig_html.replace(`{{ ${data.name} }}`, data.value)
    socket.send('VAR_UPDATED {}')
}
