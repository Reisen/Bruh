import os
import re
import sys
import queue
import collections
import functools
import argparse
from walnut.drivers import Walnut
from redislite import StrictRedis


def parse():
    parser = argparse.ArgumentParser(description = 'A Python3 IRC bot written for Walnut.')

    parser.add_argument(
        '-d',
        dest = 'data',
        action = 'store',
        help = 'location of the database file'
    )

    return parser.parse_args()


p = parse()
r = StrictRedis(p.data or 'data.rdb', db=4)
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
    print('Loading Plugins...')
    for plugin in os.listdir('plugins'):
        if plugin.endswith('.py'):
            name   = plugin[:-3]
            plugin = __import__('plugins.' + name, globals(), locals(), -1)

    print('Running')
    Walnut.run('bruh')
