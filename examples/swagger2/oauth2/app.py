#!/usr/bin/env python3
'''
Basic example of a resource server
'''

import specific


def get_secret(user) -> str:
    return 'You are: {uid}'.format(uid=user)


if __name__ == '__main__':
    app = specific.FlaskApp(__name__)
    app.add_api('app.yaml')
    app.run(port=8080)
