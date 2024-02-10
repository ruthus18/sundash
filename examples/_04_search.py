import random
from dataclasses import dataclass

from sundash import App
from sundash import Component
from sundash.app import INPUT_UPDATED

app = App()
on = app.on


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
    async def show_results(self, sig: INPUT_UPDATED) -> None:
        n = random.randint(0, 10)
        print(f'INPUT NAME: {sig.name}')
        results = f'Found {n} results for "{sig.value}"'

        await self.set('results', results)


def run():
    app.run_sync(['<h1>🔎 Search</h1>', Search])


if __name__ == '__main__':
    run()
