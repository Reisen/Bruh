"""
    Search urban dictionary or some shit I don't even know anymore
"""
import json
from urllib.parse import quote_plus
from urllib.request import urlopen
from bruh import command

@command('urban')
@command('ud')
@command('u')
def urban(irc):
    url = 'http://api.urbandictionary.com/v0/define?term={}'

    if not irc.message:
        return "Syntax: .urban <terms>"

    try:
        query = json.loads(urlopen(url.format(quote_plus(irc.message)), timeout = 7).read().decode('UTF-8'))
        query = query['list'][0]['definition']
        return "{} - {}".format(irc.message, query[:400])

    except:
        return "No definition found."

