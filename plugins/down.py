"""
    Check if a website is down.
"""
import urllib.request
from urllib.error import URLError
from plugins.commands import command

@command
def down(irc, nick, chan, msg, args):
    """
    Check if a website is down.
    .down <url>
    """
    try:
        if len(msg) == 0:
            return "Yeah let me just go ahead and guess what website you meant. It's probably down."

        if 'http://' not in msg:
            msg = 'http://' + msg

        urllib.request.urlopen(msg, timeout = 7)
    except URLError:
        return "It's not just you, {} seems to be down.".format(msg)

    return "It's just you, {} is up.".format(msg)
