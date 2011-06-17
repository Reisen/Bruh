from plugins.bruh import event

# Handles server PINGS
@event('PING')
def ping(irc, prefix, command, args):
    # Make super sure the command is right
    if command == 'PING':
        irc.raw('PONG %s\r\n' % args[0])
