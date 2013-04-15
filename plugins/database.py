"""
    Attach a small sqlite3 connection to the database for this server.
"""
import sqlite3
from plugins import event

@event('BRUH')
def setup_db(irc):
    irc.db = sqlite3.connect('data/{}.db'.format(irc.server))
