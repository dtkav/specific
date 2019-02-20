#!/usr/bin/env python3

import specific


def post_greeting(name: str) -> str:
    return 'Hello {name}'.format(name=name)

if __name__ == '__main__':
    app = specific.FlaskApp(__name__, port=9090, specification_dir='openapi/')
    app.add_api('helloworld-api.yaml', arguments={'title': 'Hello World Example'})
    app.run()
