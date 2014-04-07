"""
    Search urban dictionary or some shit I don't even know anymore
"""
import json
from urllib.parse import quote_plus
from urllib.request import urlopen
from plugins import mod

commands = mod.commands

@commands.command
def urban(irc, nick, chan, msg, args):
    """
    Searches urban dictionary.
    .urban <terms>
    """
    url = 'http://api.urbandictionary.com/v0/define?term={}'

    if not msg:
        return "Syntax: .urban <terms>"

    try:
        # More json oh my god
        query = json.loads(urlopen(url.format(quote_plus(msg)), timeout = 7).read().decode('UTF-8'))

        # OH SHIT AND DICTIONARIES, AND LISTS TOO GOD DAMN
        query = query['list'][0]['definition']

        # It can't be over
        return "{} - {}".format(msg, query)

    except:
        return "No definition found."
