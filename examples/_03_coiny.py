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


class Button:
    type ID = str
    type Name = str

    def __init__(self, name: Name, id: ID = None):
        self.name = name
        self.id = id or name.lower()

    @property
    def html(self) -> HTML:
        return f'<button id="{self.id}"><b>{self.name}</b></button>'


class Menu(Component):
    html = ''

    base_layout: list[Component | HTML]
    layout: dict[Button: list[Component | HTML]]

    def __init__(self):
        super().__init__()
        self.html = self.get_layout_html()

    def get_layout_html(self, button_pressed: Button = None) -> HTML:
        buttons = tuple(self.layout.keys())

        _menu_inner = '<b>|</b>'.join([btn.html for btn in buttons])
        menu_html = f'<div id="menu">{_menu_inner}</div>'

        html = ''
        for comp in self.base_layout:
            if comp is not Ellipsis:
                html += comp
            else:
                html += menu_html

        if not button_pressed: button_pressed = buttons[0]

        html += ''.join(self.layout[button_pressed])

        return html


class CoinyMenu(Menu):
    MAIN = Button('Main')
    TRADING = Button('Trading')
    GOALS = Button('Goals')

    base_layout = ['<h1>🪙 Coiny</h1>', ...]
    layout = {
        MAIN: ['<p>Main Page</p>'],
        TRADING: ['<p>Trading Page</p>'],
        GOALS: ['<p>Goals Page</p>',]
    }

    @on(BUTTON_CLICK)
    async def switch_layout(self, sig: BUTTON_CLICK) -> None:
        btn_map = {btn.id: btn for btn in self.layout.keys()}
        if sig.button_id not in btn_map.keys():
            return

        new_layout = self.get_layout_html(btn_map[sig.button_id])

        await send_command(UPDATE_LAYOUT(html=new_layout, vars={}))


run = lambda: app.run(layout=[CoinyMenu])


if __name__ == '__main__':
    run()
