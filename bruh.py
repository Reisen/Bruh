import os
import re
import queue
import collections
import functools
from drivers.walnut import Walnut
from redis import StrictRedis


r = StrictRedis(db=4)
c = {}
e = {}
s = []


def command(name):
    def register_command(f):
        c[name] = f
        return f

    return register_command


def regex(pattern):
    def register_command(f):
        e[pattern] = f
        return f

    return register_command


def sink(f):
    s.append(f)
    return f


if __name__ == '__main__':
    for plugin in os.listdir('plugins'):
        if plugin.endswith('.py'):
            name   = plugin[:-3]
            plugin = __import__('plugins.' + name, globals(), locals(), -1)

    Walnut.run('bruh')
