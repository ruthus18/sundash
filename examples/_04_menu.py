from sundash import App
from sundash import Component
from sundash import on
from sundash.app import ButtonClick

app = App()


class CoinyMenu(Component):
    html = '''
    <header>
        <h1>🪙 Coiny</h1>
        <div id="menu">
            <button id="main"><b>Main</b></button>
            <b>|</b>
            <button id="trading"><b>Trading</b></button>
            <b>|</b>
            <button id="goals"><b>Goals</b></button>
        </div>
    </header>
    '''

    @on(ButtonClick)
    async def on_click(self, event: ButtonClick):
        await app.switch_page(event.button_id)


coiny = lambda body: [CoinyMenu, body]


app.run_sync(
    routed_pages={
        'main': coiny('<p>Main Page</p>'),
        'trading': coiny('<p>Trading Page</p>'),
        'goals': coiny('<p>Goals Page</p>'),
    }
)
