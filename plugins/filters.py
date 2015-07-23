import codecs, hashlib, base64
from bruh import command

rot13 = str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz', 'NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm')

def rainbow(msg):
    output = ""
    colour_cycle = 2
    for character in msg:
        output += '\x03{:0>2d}{}'.format((colour_cycle % 13) + 2, character)
        colour_cycle += 1

    return output


@command('filter')
@command('f')
def filter(irc):
    """
    Provides several text filters: rot13, rot26, lower, upper, reverse, md5 (and others), rainbow, and base64.
    .filter <filter> text
    """
    try:
        text_filter, msg = irc.message.split(' ', 1)

        if not msg:
            return "No input to apply the filter to."

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

    except Exception as e:
        return None
