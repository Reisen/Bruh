"""
    Do calculations with Google calculator.
"""
from re import sub
from json import loads
from plugins.commands import command
from urllib.request import urlopen
from urllib.parse import quote_plus
from html.parser import HTMLParser

@command
def calculate(irc, nick, chan, message, args):
    """
    Use Google's Calculator
    .calc <equation>
    """
    # Fetch and fix-up invalid JSON.
    try:
        result = urlopen('http://www.google.com/ig/calculator?q={}'.format(quote_plus(message)))
        result = HTMLParser().unescape(result.read().decode('unicode-escape'))
        result = result.replace('<sup>', '^(').replace('</sup>', ')')
        result = loads(sub(r'([a-z]+):', '"\\1":', result))
        return result['rhs']
    except:
        return "Google couldn't calculate this."
