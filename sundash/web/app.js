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

    if (name == 'CLEAR_LAYOUT') {
        clear_layout()
    }
    else if (name == 'UPDATE_LAYOUT') {
        update_layout(data)
    }
    else if (name == 'SET_VAR') {
        set_var(data)
    }
    else {
        console.error(`dispatching error: ${event.data}`)
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
    socket.send('LAYOUT_CLEAN {}')
}


function _init_buttons() {
    const buttons = [...document.getElementsByTagName('button')]
    buttons.forEach(button => {
        button.onclick = () => {
            socket.send(`BUTTON_CLICK {"button_id": "${button.id}"}`)
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
    
    socket.send('LAYOUT_UPDATED {}')
}


function set_var(data) {
    app.__vars[data.key] = data.value
    app.innerHTML = app.__html.replace(`{{ ${data.key} }}`, data.value)
    _init_buttons()
    
    socket.send('VAR_SET {}')
}
