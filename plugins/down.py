"""
    Check if a website is down.
"""
from urllib.error import URLError
from plugins.commands import command
import urllib.request

@command
def down(irc, nick, chan, msg, args):
    """Check if a website is down."""

    try:
        if len(msg) == 0:
            return "Yeah let me just go ahead and guess what website you meant. It's down."

        if 'http://' not in msg:
            msg = 'http://' + msg

        urllib.request.urlopen(msg)

    except URLError:
        return "It's not just you, {} seems to be down.".format(msg)

    return "It's just you, {} is up.".format(msg)
