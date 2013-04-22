"""Quotes plugin."""

import sys
import re
from random import choice, randrange, shuffle
from plugins.commands import command

def setup_db(irc):
    irc.db.execute('''
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY,
            chan TEXT,
            by TEXT,
            quote TEXT
        );
    ''')
    irc.db.commit()


def add_quote(irc, chan, nick, args):
    setup_db(irc)

    if not args:
        return "Missing a quote to add to the database."

    irc.db.execute('INSERT INTO quotes (chan, by, quote) VALUES (?, ?, ?)', (chan, nick, args[0]))
    irc.db.commit()
    return "Awesome, saved."


def colour_quote(quote):
    """Add colours to nicks in the quote."""
    nicks = set(re.findall(r'<([^>]+)>', quote))
    colours = [13, 10, 12, 2, 4, 14]
    shuffle(colours)

    # For each nick found, assign them a unique colour.
    for nick in nicks:
        coloured_nick = '\x03{}{}\x03'.format(colours.pop(), nick)
        quote = quote.replace(nick, coloured_nick)

    return quote


def get_quote(irc, chan, args):
    setup_db(irc)

    quotes = irc.db.execute('SELECT * FROM quotes WHERE chan = ?', (chan,)).fetchall()
    id, chan, by, quote = quotes[int(args[0]) - 1]
    return 'Quote [{}/{}]: {}'.format(args[0], len(quotes), colour_quote(quote))


def random_quote(irc, chan):
    setup_db(irc)

    try:
        quotes = irc.db.execute('SELECT * FROM quotes WHERE chan = ?', (chan,)).fetchall()
        index = randrange(0, len(quotes))
        id, chan, by, quote = quotes[index]
        return 'Quote [{}/{}]: {}'.format(index + 1, len(quotes), colour_quote(quote))
    except:
        return "No quotes found."


@command
def quote(irc, nick, chan, msg, args):
    """
    Manages a quotes database. No arguments fetch random quotes.
    .quote add <quote>
    .quote get <num>
    """
    command, *args = msg.split(' ', 1)

    try:
        commands = {
            'add':    lambda: add_quote(irc, chan, nick, args),
            'get':    lambda: get_quote(irc, chan, args)
        }
        return commands[command]()
    except:
        return random_quote(irc, chan)
