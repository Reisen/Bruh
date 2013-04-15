from plugins import event
from plugins.commands import regex

# Handles server PINGS
@event('PING')
def ping(irc, prefix, command, args):
    # Make super sure the command is right
    if command == 'PING':
        irc.raw('PONG %s\r\n' % args[0])


# Users can 'ping' bruh by using 'bruh!' in a message for it to respond to.
@regex(r'bruh!')
def respond(irc, nick, chan, match, args):
    return nick + '!'
