from starlette.applications import Starlette
from starlette.responses import RedirectResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles


async def index_redirect(_) -> RedirectResponse:
    return RedirectResponse('/index.html')


app = Starlette(debug=True, routes=[
    Route('/', index_redirect),
    Mount('/', app=StaticFiles(directory='static'), name='static'),
])
