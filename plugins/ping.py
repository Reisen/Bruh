from plugins import event
from plugins.commands import regex

# Handles server PINGS
@event('PING')
def ping(irc, prefix, command, args):
    irc.raw('PONG :{}\r\n'.format(args[0]))


# Users can 'ping' bruh by using 'bruh!' in a message for it to respond to.
@regex(r'$nick!')
def respond(irc, nick, chan, match, args):
    return nick + '!'
