from sundash import App
from sundash import Component

app = App()


class Dummy(Component): ...


app.run(layout=[Dummy])
