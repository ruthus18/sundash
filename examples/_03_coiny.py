import logging
from sundash import App
from sundash import Component
from sundash.app import BUTTON_CLICK
# from sundash.app import UPDATE_LAYOUT
from sundash.core import HTML
from sundash.app import on

logger = logging.getLogger(__name__)


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
    async def switch_layout(self, event: BUTTON_CLICK) -> None:
        logger.info('switch layout')
        # btn_map = {btn.id: btn for btn in self.layout.keys()}
        # if event.button_id not in btn_map.keys():
        #     return

        # new_layout = self.get_layout_html(btn_map[event.button_id])

        # session = event._ctx.session
        # await session.send_command(UPDATE_LAYOUT(html=new_layout, vars={}))


def run():
    app.run_sync([CoinyMenu])


if __name__ == '__main__':
    run()
