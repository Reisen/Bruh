"""
    Provides a collection of text filters to filter output through, and an echo
    command that outputs its input.
"""
import codecs
from plugins.commands import command

rot13 = str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz', 'NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm')

@command
def filter(irc, nick, chan, msg, args):
    """
    Provides several text filters: rot13, rot26, lower, upper, reverse.
    !filter <filter> text
    """
    try:
        text_filter, msg = msg.split(' ', 1)

        filters = {
            'rot13':   lambda: msg.translate(rot13),
            'rot26':   lambda: msg,
            'lower':   lambda: msg.lower(),
            'upper':   lambda: msg.upper(),
            'reverse': lambda: msg[::-1]
        }
        return filters[text_filter]()
    except:
        return "Unknown filter."

@command
def echo(irc, nick, chan, msg, args):
    """Eats and shits"""
    return msg
