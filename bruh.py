import os
import re
import queue
import collections
import functools
from drivers.walnut import Walnut
from redis import StrictRedis


r = StrictRedis(db=4)
c = {}


def command(name):
    def register_command(f):
        @functools.wraps(f)
        def handler(*args, **kwargs):
            return f(*args, **kwargs)

        c[name] = handler
        return handler

    return register_command


if __name__ == '__main__':
    for plugin in os.listdir('plugins'):
        if plugin.endswith('.py'):
            name   = plugin[:-3]
            plugin = __import__('plugins.' + name, globals(), locals(), -1)

    Walnut.run('bruh')
