"""
    Help choose a value for people who aren't able to make their own decisions
"""
import random
from plugins import mod

hook = mod.hook

@hook.command
def choose(irc, nick, chan, msg, args):
    """
    Chooses a value for you.
    .choose <value1>, <value2> ...
    """
    if not msg:
        return "Syntax: .choose <value>, <value>, ..."

    options = msg.split(',')
    return options[random.randint(0, len(options) - 1)].strip()
