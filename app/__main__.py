from sundash.core import App
from sundash.core import run

app = App()


# class CurrentTime(Component):
#     html = '<p style="padding: 30px">{{ value }}<p/>'

#     # Каждый инстанс должен хранить эти переменные в памяти и восстанавливать
#     value: Var[dt.time] = None

#     @app.on(sig.EVERY_SECOND)
#     def update(self):
#         self.value = dt.time.now()


# app.attach_to_layout(CurrentTime())

run(app)
