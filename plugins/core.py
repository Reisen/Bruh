"""
    This plugin is one of the earliest plugins to be loaded. It takes a server
    object and patches it at runtime to include some extra useful methods that
    will allow other plugins to more easily use the IRC protocol.
"""

from plugins.bruh import event

def reply(self, message):
    prefix, command, args = self.message
    self.raw('PRIVMSG %s :%s\r\n' % (args[0], message))


def say(self, message, channel):
    self.raw('PRIVMSG %s :%s\r\n' % (channel, message))


def notice(self, user, message):
    self.raw('NOTICE %s :%s\r\n' % (user, message))


@event('BRUH')
def addCoreFunctionality(irc):
    container = type(irc)

    # Bind the new methods to the IRC class
    container.reply     = reply
    container.say       = say
    container.notice    = notice
