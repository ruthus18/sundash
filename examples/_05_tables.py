from sundash import App
from sundash.tables import Table

app = App()


COMPANIES = (
    # Headers
    ('company', 'contact', 'country'),
    # Data
    ('Alfreds Futterkiste', 'Maria Anders', 'Germany'),
    ('Centro comercial Moctezuma', 'Francisco Chang', 'Mexico'),
)


class CompanyView(Table):
    init_data = COMPANIES


run = lambda: app.run(layout=('<h1>📋 Tables</h1>', CompanyView))


if __name__ == '__main__':
    run()
