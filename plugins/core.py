"""
    This plugin is one of the earliest plugins to be loaded. It takes a server
    object and patches it at runtime to include some extra useful methods that
    will allow other plugins to more easily use the IRC protocol.
"""
from plugins import event

def reply(self, message):
    """Replies to the channel a message was sent from."""
    prefix, command, args = self.parsed_message

    # Determine whether the message was from a query, or a channel.
    target = args[0] if args[0].startswith('#') else prefix.split('!')[0]
    self.raw('PRIVMSG %s :%s\r\n' % (target, message))


def say(self, channel, message):
    """Sends a message to the channel the event was received from."""
    self.raw('PRIVMSG %s :%s\r\n' % (channel, message))


def notice(self, user, message):
    """Sends a notice to the channel an event was received from"""
    self.raw('NOTICE %s :%s\r\n' % (user, message))


@event('BRUH')
def addCoreFunctionality(irc):
    """
    Called when a server is first created, and adds our new userful methods to
    the object for use in other plugins.
    """
    container = type(irc)

    # Bind the new methods to the IRC class
    container.reply  = reply
    container.say    = say
    container.notice = notice
