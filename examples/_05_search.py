import random
from dataclasses import dataclass

from sundash import App
from sundash import Component
from sundash import on
from sundash.app import INPUT_UPDATED

app = App()


class Search(Component):
    html = '''
        <div style="width:90%;margin:auto">
            <br>
            <input
                name="search"
                placeholder="Type something and hit `Enter`"
            />
            <br>
            <p>{{ results }}</p>
            <br>
        </div>
    '''

    @dataclass
    class Vars:
        results: str = ''

    @on(INPUT_UPDATED)
    async def show_results(self, event: INPUT_UPDATED) -> None:
        n = random.randint(0, 10)
        self.vars.results = f'Found {n} results for "{event.value}"'

        await self.update_var('results', event=event)


app.run_sync(['<h1>🔎 Search</h1>', Search])
