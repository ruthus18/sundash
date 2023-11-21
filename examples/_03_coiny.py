import typing as t

from sundash import App
from sundash import Component
from sundash.core import HTML
from sundash.core import on
from sundash.core import send_command
from sundash.layout import BUTTON_CLICK
from sundash.layout import UPDATE_LAYOUT
from sundash.logging import setup as _setup_logging

_setup_logging()


app = App()


class MenuButton(t.NamedTuple):
    name: str
    link: str


class Menu(Component):
    html = ''
    buttons: tuple[MenuButton]

    def __init__(self):
        super().__init__()
        self.html = self.get_layout_html()

    def get_layout_html(self, button_id: str = None) -> HTML:
        buttons_html = []
        for button in self.buttons:
            buttons_html.append(
                f'<button id="{button.link}"><b>{button.name}</b></button>'
            )

        menu_html = '<div id="menu">' + '<b>|</b>'.join(buttons_html) + '</div>'

        html = ''
        for comp in self.base_layout:
            if comp is not Ellipsis:
                html += comp
            else:
                html += menu_html

        if not button_id:
            button_id = tuple(self.layout.keys())[0]

        html += ''.join(self.layout[button_id])

        return html


class CoinyMenu(Menu):
    buttons = (
        MenuButton('Main', 'menu-main'),
        MenuButton('Trading', 'menu-trading'),
        MenuButton('Goals', 'menu-goals')
    )
    base_layout = ['<h1>🪙 Coiny</h1>', ...]
    layout = {
        'menu-main': ['<p>Main Page</p>'],
        'menu-trading': ['<p>Trading Page</p>'],
        'menu-goals': ['<p>Goals Page</p>',]
    }

    @on(BUTTON_CLICK)
    async def switch_layout(self, sig: BUTTON_CLICK) -> None:
        if sig.button_id not in self.layout:
            return

        new_layout = self.get_layout_html(sig.button_id)

        await send_command(UPDATE_LAYOUT(html=new_layout, vars={}))


run = lambda: app.run(layout=[CoinyMenu], title='Coiny')


if __name__ == '__main__':
    run()
