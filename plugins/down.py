"""
    Check if a website is down.
"""
from urllib.error import URLError
from plugins.commands import command
import urllib.request

@command
def down(irc, nick, prefix, command, args):
    """Check if a website is down."""

    try:
        if len(args[1]) == 0:
            return "Yeah let me just go ahead and guess what website you meant. It's down."

        if 'http://' not in args[1]:
            args[1] = 'http://' + args[1]

        urllib.request.urlopen(args[1])

    except URLError:
        return "It's not just you, {} seems to be down.".format(args[1])

    return "It's just you, {} is up.".format(args[1])
