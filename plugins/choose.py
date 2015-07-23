from bruh import command
from random import choice

@command('choose')
def choose(irc):
    if not irc.message:
        return None

    choices = irc.message.split(',')
    return choice(choices).strip()
