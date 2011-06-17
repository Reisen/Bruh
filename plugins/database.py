"""
    This plugin provides an interface for other plugins to use to store info, as
    well as providing a set of simple commands for use in the channel.
"""

import sqlite3
from plugins.bruh import event

class Query(object):
    """An extremely simple ORM for accessing the database in plugins"""

    def __init__(self, server):
        print('Connecting to <db(%s)>' % server)

@event('BRUH')
def database(irc):
    irc.db = None
