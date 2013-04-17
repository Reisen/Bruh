"""This plugin implements a lot of functionality of infobot."""
import random
from plugins.commands import regex, command
from plugins.database import *

def setup_db(irc):
    irc.db.execute('''
        CREATE TABLE IF NOT EXISTS factoids (
            id INTEGER PRIMARY KEY,
            key TEXT UNIQUE,
            value TEXT
        );
    ''')
    irc.db.commit()


@command
def remember(irc, nick, chan, msg, args):
    """
    Adds new commands to the database.
    """
    setup_db(irc)

    key, value = msg.split(' ', 1)

    # See if an object with this key already exists. If it does, overwrite the
    # value instead of creating a new entry.
    fact = irc.db.execute('SELECT * FROM factoids WHERE key = ?', (key,)).fetchone()

    # Update existing keys.
    if fact is not None:
        # Append new data to the definition if the fact already exists.
        if fact[2] == value:
            return "I already knew that. Tell me something I don't know."

        irc.db.execute('UPDATE factoids SET value = value || ? WHERE key = ?', (', ' + value, key))
        irc.db.commit()
        return "I'll remember that too."

    # Add the new keys to the database.
    irc.db.execute('INSERT INTO factoids (key, value) VALUES (?, ?)', (key, value))
    irc.db.commit()
    return "I'll remember that."


@regex(r'^\?([^\s]+)$')
def get_fact(irc, nick, chan, match, args):
    """
    Parses ?A messages to retrieve facts.
    """
    setup_db(irc)

    # Look for a matching key in the database.
    key = match.groups()[0]
    query = irc.db.execute('SELECT * FROM factoids WHERE key = ?', (key,)).fetchone()
    if query is None:
        return None

    # Preprocess returned response. These are all stolen from infobot.
    query = query[2]
    query = query.replace('$nick', nick)
    query = query.replace('$chan', chan)
    query = query.replace('$rand', random.sample(irc.userlist[chan], 1)[0])

    # Action messages and shit should actually print actions.
    if query.startswith('@a'):
        query = "\01ACTION " + query[2:].strip() + "\01"
        return query

    # Send messages back raw without the connector,
    if query.startswith('@r'):
        return query[2:].strip()

    return '{}: {} '.format(key, query)
