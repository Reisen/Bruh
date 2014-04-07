"""
    Attach a small sqlite3 connection to the database for this server.
"""
import os
import sqlite3
from plugins import event

connections = []

@event('BRUH')
def setup_db(irc):
    if not os.path.exists('data/'):
        os.mkdir('data/')

    irc.db = sqlite3.connect('data/{}.db'.format(irc.server['address']), check_same_thread = False)
    connections.append(irc.db)


@event('GETOUT')
def shutdown_db():
    for connection in connections:
        connection.commit()
        connection.close()
