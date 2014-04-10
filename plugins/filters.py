"""
    Provides a collection of text filters to filter output through, and an echo
    command that outputs its input.
"""
import codecs, hashlib, base64
from plugins import mod

hook = mod.hook

rot13 = str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz', 'NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm')

def rainbow(msg):
    output = ""
    colour_cycle = 2
    for character in msg:
        output += '\x03{:0>2d}{}'.format((colour_cycle % 13) + 2, character)
        colour_cycle += 1

    return output

@hook.command
def filter(irc, nick, chan, msg, args):
    """
    Provides several text filters: rot13, rot26, lower, upper, reverse, md5 (and others), rainbow, and base64.
    .filter <filter> text
    """
    try:
        text_filter, msg = msg.split(' ', 1)

        filters = {
            'rot13':   lambda: msg.translate(rot13),
            'rot26':   lambda: msg,
            'lower':   lambda: msg.lower(),
            'upper':   lambda: msg.upper(),
            'reverse': lambda: msg[::-1],
            'md5':     lambda: hashlib.md5(msg.encode('utf-8')).hexdigest(),
            'sha1':    lambda: hashlib.sha1(msg.encode('utf-8')).hexdigest(),
            'sha224':  lambda: hashlib.sha224(msg.encode('utf-8')).hexdigest(),
            'sha384':  lambda: hashlib.sha384(msg.encode('utf-8')).hexdigest(),
            'sha512':  lambda: hashlib.sha512(msg.encode('utf-8')).hexdigest(),
            'rainbow': lambda: rainbow(msg),
            'base64':  lambda: base64.b64encode(msg.encode('utf-8')).decode('utf-8')
        }
        return filters[text_filter]()
    except:
        return "Unknown filter."

@hook.command
def echo(irc, nick, chan, msg, args):
    """Eats and shits"""
    return msg
