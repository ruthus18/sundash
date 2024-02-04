from sundash import App


def run():
    components = [
        '<h1>⚙️ Sundash Demo</h1>',
        '<p>Hello world!</p>'
    ]
    App().run_sync(components)


if __name__ == '__main__':
    run()
