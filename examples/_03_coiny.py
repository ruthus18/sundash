from sundash import App
from sundash import Component
from sundash import on
from sundash.app import BUTTON_CLICK


app = App()


class CoinyMenu(Component):
    html = f"""
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
    """

    @on(BUTTON_CLICK)
    async def on_click(self, event: BUTTON_CLICK) -> None:
        session = event._ctx.session
        await app.switch_page(event.button_id, session=session)


coiny = lambda body: [CoinyMenu, body]


def run():
    app.run_sync(
        routed_pages={
            'main': coiny('<p>Main Page</p>'),
            'trading': coiny('<p>Trading Page</p>'),
            'goals': coiny('<p>Goals Page</p>'),
        }
    )


if __name__ == '__main__':
    run()
