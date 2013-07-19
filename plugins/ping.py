"""
    This plugin implements the PING response, and any other response that's
    'PING' like, such as version requests and highlights.
"""
from plugins import event
from plugins.commands import regex

# Handles server PINGS
@event('PING')
def ping(irc, prefix, command, args):
    irc.raw('PONG :{}\r\n'.format(args[0]))


# Respond to common CTCP's
@event('PRIVMSG')
def ctcps(irc, prefix, command, args):
    if args[0] != irc.nick:
        return None

    ctcp = args[1]
    target = prefix.split('!',1)[0]
    try:
        irc.ctcp(target, {
            '\x01VERSION\x01': 'VERSION Bruh 0.1-rc (http://github.com/Reisen/Bruh)',
            '\x01SOURCE\x01':  'SOURCE http://github.com/Reisen/Bruh'
        }[ctcp])
    except Exception as e:
        # TODO: Make this a more robust log later.
        print('Invalid CTCP Attempted: {} ({})'.format(ctcp[1:-1]), str(e))


# Users can 'ping' bruh by using 'bruh!' in a message for it to respond to.
@regex(r'$nick!')
def respond(irc, nick, chan, match, args):
    return nick + '!'
