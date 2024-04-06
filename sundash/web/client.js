let socket = new WebSocket('ws:/127.0.0.1:5000/')

socket.onopen = event => {
    console.log(`[WS] CONN_OPEN: ${event.target.url}`)
}

socket.onmessage = event => {
    let [name, ...data] = event.data.split(' ')
    data = data.join(' ')
    console.log(`${name} ${data}`)

    if (data != undefined) {
        data = JSON.parse(data)
    }

    if (name == 'ClearLayout') {
        clear_layout()
    }
    else if (name == 'UpdateLayout') {
        update_layout(data)
    }
    else if (name == 'SetVar') {
        set_var(data)
    }
    else {
        console.error(`[!!!] dispatching error: ${event.data}`)
    }
}

socket.onclose = event => {
    if (event.wasClean) {
        console.log(
            `[WS] CONN_CLOSED: code=${event.code} reason=${event.reason}`
        )

    } else {
       // например, сервер убил процесс или сеть недоступна
       // обычно в этом случае event.code 1006
        console.log('[WS] CONN_ABORTED')
    }
}

socket.onerror = error => {
    console.log('[WS] ERROR:')
    console.log(error)
}


const app = document.getElementById('app')


function clear_layout() {
    app.innerHTML = ''
    socket.send('LayoutClean {}')
}


function _init_buttons() {
    const buttons = [...document.getElementsByTagName('button')]
    buttons.forEach(button => {
        button.onclick = () => {
            socket.send(`ButtonClick {"button_id": "${button.id}"}`)
        }
    })
}


function _init_inputs() {
    const inputs = [...document.getElementsByTagName('input')]
    inputs.forEach(input => {
        console.log(input)
        input.onchange = (e) => {
            socket.send(`InputUpdated {"name": "${input.name}", "value": "${input.value}"}`)
            e.target.value = ''
        }
    })
}


function update_layout(data) {
    app.innerHTML = ''
    app.__html = data.html
    app.__vars = data.vars

    let response_html = app.__html
    for (let key in app.__vars) {
        let value = app.__vars[key]
        response_html = response_html.replace(`{{ ${key} }}`, value)
    }

    app.innerHTML = response_html
    _init_buttons()
    _init_inputs()
    
    socket.send('LayoutUpdated {}')
}


function set_var(data) {
    app.__vars[data.name] = data.value
    app.innerHTML = app.__html.replace(`{{ ${data.name} }}`, data.value)
    _init_buttons()
    _init_inputs()
    
    socket.send('VarSet {}')
}
