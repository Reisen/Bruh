"""
    This creates a single event handler that will allow the bot to respond
    to invite requests by joining the channel automatically
"""

from plugins import event

@event('INVITE')
def invite(irc, prefix, command, args):
    irc.raw('JOIN %s\r\n' % args[1])
