"""Quotes plugin."""

import sys
import re
from random import choice
from plugins.commands import command

def setup_db(irc):
    irc.db.execute('''
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY,
            by TEXT,
            quote TEXT
        );
    ''')
    irc.db.commit()


def add_quote(irc, nick, args):
    setup_db(irc)

    if not args:
        return "Missing a quote to add to the database."

    irc.db.execute('INSERT INTO quotes (by, quote) VALUES (?, ?)', (nick, args[0]))
    irc.db.commit()
    return "Awesome, saved."


def colour_quote(quote):
    """Add colours to nicks in the quote."""
    nicks = set(re.findall(r'<([^>]+)>', quote))
    colours = [13, 10, 12, 3, 2, 4]

    # For each nick found, assign them a unique colour.
    for nick in nicks:
        coloured_nick = '\x03{}{}\x03'.format(colours.pop(), nick)
        quote = quote.replace(nick, coloured_nick)

    return quote


def get_quote(irc, args):
    setup_db(irc)

    # Find a random quote if no search parameters are passed.
    print(args)
    if not args:
        quotes = irc.db.execute('SELECT * FROM quotes').fetchall()
        id, by, quote = choice(quotes)
        return colour_quote(quote)

    print('Oh no')


@command
def quote(irc, nick, chan, msg, args):
    """Manage a quotes database."""
    command, *args = msg.split(' ', 1)

    try:
        commands = {
            'add':    lambda: add_quote(irc, nick, args),
            'get':    lambda: get_quote(irc, args),
            'search': lambda: find_quote(irc, args)
        }
        return commands[command]()
    except:
        return str(sys.exc_info())
