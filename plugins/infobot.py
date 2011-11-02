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
    id        = Integer(primary_key = True)
    key       = String()
    value     = String()
    connector = String()

    def __init__(self, key = None, value = None, connector = 'is'):
        self.key = key
        self.value = value
        self.connector = connector


@regex(r'^\?(.*?)\s+(is|can|has|are|was|will\sbe|also\sis)\s+(.*)$')
def add_fact(irc, nick, chan, match, args):
    """
    Parses ?A is B messages into factoids.
    """
    # If the table is unmapped, map it here. This will also create a table if
    # one doesn't exist.
    irc.db.map(Factoid)

    key, connector, value = match.groups()

    # Preprocess the key, if the is keyword was escaped, we should store it
    # without the backslash.
    key = key.replace('\\is', 'is').lower()

    # See if an object with this key already exists. If it does, overwrite the
    # value instead of creating a new entry.
    fact = irc.db.query(Factoid).where(Factoid.key == key).one()

    if fact is not None:
        # If the connector is 'is also', append the definition with a pipe
        # instead.
        if connector == 'also is':
            fact.value += '|' + value
            fact.save()
            return "Got that as well."

        if fact.value == value:
            return "I already knew that. Tell me something I don't know."

        fact.value = value
        fact.save()
        return "Oh ok, I'll remember that."

    # Add the new key to the database.
    irc.db.add(Factoid(key, value, connector))
    return "I'll remember that."

    return "Ok then {}".format(nick)


@regex(r'^\?(.+)$')
def get_fact(irc, nick, chan, match, args):
    """
    Parses ?A messages to retrieve facts.
    """
    irc.db.map(Factoid)

    try:
        # Transitive lookups will search the database again for a description
        # if the found value also has a definition.
        key = match.groups()[0]
        transitive = False
        if key[0] == '?':
            transitive = True
            key = key[1:]

        query = irc.db.query(Factoid).where(Factoid.key == key.lower()).one()
        if query is None:
            return None

        # Keep looking up values until we find one that doesn't have
        # a definition, or if random returns 0.
        while transitive:
            if random.randint(0,1) == 0:
                transitive = False

            # Check if the value is piped, if so there's multiple ways we
            # could branch our search here.
            value = query.value
            if '|' in value:
                value = value.split('|')
                value = value[random.randint(0, len(value) - 1)]

            next_query = irc.db.query(Factoid).where(Factoid.key == value.lower()).one()

            if next_query is not None:
                query = next_query
            else:
                transitive = False

        query, connector = query.value, query.connector

        # Preprocess returned response. These are all stolen from infobot.
        query = query.replace('$nick', nick)
        query = query.replace('$chan', chan)
        query = query.replace('$rand', random.sample(irc.userlist[chan], 1)[0])

        # Pick a random response if multiple responses are available
        if '|' in query:
            query = query.split('|')
            query = query[random.randint(0, len(query) - 1)]

        # Action messages and shit.
        if query.startswith('@a'):
            query = "\01ACTION " + query[2:].strip() + "\01"
            return query

        # Send messages back raw without the connector, and shit.
        if query.startswith('@r'):
            return query[2:].strip()

        return key + ' {} '.format(connector) + query

    except Exception as e:
        print('infobot.get_fact: ' + str(e))
