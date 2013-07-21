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
    if args[0] != irc.nick or '\x01' not in args[1]:
        return None

    ctcp = args[1].replace('\x01', '')
    ctcp, *ctcp_parts = ctcp.split(' ', 1)
    target = prefix.split('!',1)[0]
    try:
        irc.ctcp(target, {
            'VERSION': lambda: 'VERSION Bruh 0.1-rc (http://github.com/Reisen/Bruh)',
            'SOURCE':  lambda: 'SOURCE http://github.com/Reisen/Bruh',
            'PING':    lambda: 'PING {}'.format(ctcp_parts[0]),
        }[ctcp]())
    except Exception as e:
        # TODO: Make this a more robust log later.
        irc.ctcp(target, 'ERRMSG There was an error handling that CTCP message.')


# Users can 'ping' bruh by using 'bruh!' in a message for it to respond to.
@regex(r'$nick!')
def respond(irc, nick, chan, match, args):
    return nick + '!'
