from sundash import App
from sundash.tables import Table

app = App()


class CompanyView(Table):
    table_data = (
        # Headers
        ('company', 'contact', 'country', 'employees'),
        # Data
        ('Alfreds Futterkiste', 'Maria Anders', 'Germany', 65),
        ('Centro comercial Moctezuma', 'Francisco Chang', 'Mexico', 349),
    )


app.run_sync(['<h1>📋 Tables</h1>', CompanyView])
