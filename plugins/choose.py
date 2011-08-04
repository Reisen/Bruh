"""
    Help choose a value for people who aren't able to make their own decisions
"""
from plugins.commands import command
import random

@command
def choose(irc, nick, chan, msg, args):
    """
    Chooses a value for you.
    .choose <value1>, <value2> ...
    """
    options = msg.split(',')
    return options[random.randint(0, len(options) - 1)].strip()
