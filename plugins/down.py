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
        if not msg:
            return "Syntax: .down <url>"

        if not msg.startswith('http://'):
            msg = 'http://' + msg

        urllib.request.urlopen(msg, timeout = 7)

    except URLError:
        return "It's not just you, {} seems to be down.".format(msg)

    return "It's just you, {} is up.".format(msg)
