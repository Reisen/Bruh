"""
    Provides a collection of text filters to filter output through.
"""
from plugins.commands import command
import codecs

rot13 = str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz', 'NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm')

@command
def filter(irc, nick, chan, msg, args):
    """
    Provides several text filters.
    """
    text_filter, msg = msg.split(' ', 1)

    if text_filter == 'rot13':
        return msg.translate(rot13)

    elif text_filter == 'rot26':
        return msg

    elif text_filter == 'lower':
        return msg.lower()

    elif text_filter == 'upper':
        return msg.upper()

    elif text_filter == 'reverse':
        return msg[::-1]

    return "Unknown filter"
