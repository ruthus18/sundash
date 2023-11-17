from .core import App

app = App()


if __name__ == '__main__':
    app.run(layout=(
        '<h1>Test App</h1>',
    ))
