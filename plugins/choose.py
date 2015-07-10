from bruh import command
from random import choice

@command('choose')
def choose(irc):
    choices = irc.message.split(',')
    return choice(choices).strip()
