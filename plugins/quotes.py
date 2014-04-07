"""Quotes plugin."""

import sys
import re
from random import choice, randrange, shuffle
from plugins import mod

userlist = mod.userlist
commands = mod.commands

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


def del_quote(irc, nick, chan, quote):
    setup_db(irc)

    # Make sure the user is high enough mode to do this.
    if userlist.min_mode(irc, nick, chan, '%'):
        irc.db.execute('DELETE FROM quotes WHERE id = ?', (quote,))
        irc.db.commit()
        return "Quote #{} deleted.".format(quote)

    return "You need to be at least a half-op to do this."


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


def get_quote(irc, chan, arg):
    setup_db(irc)

    quotes = irc.db.execute('SELECT * FROM quotes WHERE chan = ?', (chan,)).fetchall()
    id, chan, by, quote = quotes[int(arg) - 1]
    return 'Quote [{}/{}]: {}'.format(arg, len(quotes), colour_quote(quote))


def random_quote(irc, chan):
    setup_db(irc)

    try:
        quotes = irc.db.execute('SELECT * FROM quotes WHERE chan = ?', (chan,)).fetchall()
        index = randrange(0, len(quotes))
        id, chan, by, quote = quotes[index]
        return 'Quote [{}/{}]: {}'.format(index + 1, len(quotes), colour_quote(quote))

    except:
        return "No quotes found."


def find_quote(irc, chan, arg, short = True):
    setup_db(irc)

    try:
        # Find all quotes, so that we can return valid quote indexes to the
        # channels copy of its quote DB.
        all_quotes = irc.db.execute('SELECT * FROM quotes WHERE chan = ?', (chan,)).fetchall()

        # Find matches quotes using globs or like depending on whether short
        # mode is used. Short mode is when no command is provided to .q
        if short:
            quotes = irc.db.execute(
                'SELECT * FROM quotes WHERE chan = ? AND quote LIKE ?',
                (chan, '%{}%'.format(arg))
            ).fetchall()
        else:
            quotes = irc.db.execute(
                'SELECT * FROM quotes WHERE chan = ? AND quote GLOB ?',
                (chan, '*{}*'.format(arg))
            ).fetchall()

        if not quotes:
            return 'No quotes found.'

        # Return either the first matching quote, or a list of matching quotes.
        id, chan, by, quote = quotes[0]
        if short:
            return 'Quote [1/{}]: {}'.format(len(quotes), colour_quote(quote))

        # Slice to a reasonable sized subset.
        sub_quotes = quotes[:10]

        # Scan the original list for matches so we have legit ID's.
        quote_ids = []
        for real_pos, real_quote in enumerate(all_quotes):
            for matched_quote in sub_quotes:
                if real_quote[0] == matched_quote[0]:
                    quote_ids.append(str(real_pos + 1))

        return 'Found {}, the first {} are: {}'.format(len(quotes), len(sub_quotes), ','.join(quote_ids))

    except Exception as e:
        return 'There was an error searching for that quote: ' + str(e)


@commands.command
def quote(irc, nick, chan, msg, args):
    """
    Manages a quotes database. No arguments fetch random quotes.
    .quote add <quote>
    .quote get <num>
    .quote del <num>
    .quote find <terms>
    """
    command, *args = msg.split(' ', 1)

    try:
        commands = {
            'add':  lambda: add_quote(irc, chan, nick, args),
            'get':  lambda: get_quote(irc, chan, args[0]),
            'del':  lambda: del_quote(irc, nick, chan, args[0]),
            'find': lambda: find_quote(irc, chan, args[0], False)
        }
        return commands[command]()

    except Exception as e:
        # Try and find a quote matching the text.
        if msg:
            return find_quote(irc, chan, command)

        return random_quote(irc, chan)
