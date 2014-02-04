"""
    Search urban dictionary or some shit I don't even know anymore
"""
from plugins.commands import command

from urllib.parse import quote_plus
from urllib.request import urlopen
import json

@command
def urban(irc, nick, chan, msg, args):
    '''searches urban dictionary'''
    url = 'http://api.urbandictionary.com/v0/define?term={}'

    if not msg:
        return "Need something to search for."

    try:
        # More json oh my god
        query = json.loads(urlopen(url.format(quote_plus(msg)), timeout = 7).read().decode('UTF-8'))

        # OH SHIT AND DICTIONARIES, AND LISTS TOO GOD DAMN
        query = query['list'][0]['definition']

        # It can't be over
        return "{} - {}".format(msg, query)
    except:
        return "No definition found."
