"""
    This plugin implements a lot of functionality of infobot.

    Usage
    -----

"""
from plugins.commands import regex, command
from plugins.database import *
import random

class Factoid(object):
    """
    Object representing a Factoid. Mapped by the database plugin to a sqlite
    table.
    """
    id  = Integer(primary_key = True)
    key = String()
    val = String()

    def __init__(self, key = None, val = None):
        self.key = key
        self.val = val


@regex(r'^\?(.*?)\s+(?:is|are|was|will\sbe)\s+(.*)$')
def add_fact(irc, nick, chan, match, args):
    """
    Parses ?A is B messages into factoids.
    """
    # If the table is unmapped, map it here. This will also create a table if
    # one doesn't exist.
    irc.db.map(Factoid)

    key, val = match.groups()

    # Preprocess the key, if the is keyword was escaped, we should store it
    # without the backslash.
    key = key.replace('\\is', 'is').lower()

    # See if an object with this key already exists. If it does, overwrite the
    # value instead of creating a new entry.
    fact = irc.db.query(Factoid).where(Factoid.key == key).one()

    if fact is not None:
        return "Already exists as: <Factoid ({} -> {})>".format(fact.key, fact.val)

    # Add the new key to the database.
    irc.db.add(Factoid(key, val))

    return "Ok then {}".format(nick)


@regex(r'^\?(.*)$')
def get_fact(irc, nick, chan, match, args):
    """
    Parses ?A messages to retrieve facts.
    """
    irc.db.map(Factoid)

    try:
        query = irc.db.query(Factoid).where(Factoid.key == match.groups()[0].lower())
        query = query.one().val

        # Preprocess returned response. These are all stolen from infobot.
        query = query.replace('$who', nick)
        query = query.replace('$chan', chan)

        # Pick a random response if multiple responses are available
        if '|' in query:
            query = query.split('|')
            query = query[random.randint(0, len(query) - 1)]

        # Action messages and shit.
        if query.startswith('@a'):
            query = "\01ACTION " + query[2:].strip() + "\01"

        return query

    except Exception as e:
        print(e)
