"""
    This plugin is one of the earliest plugins to be loaded. It takes a server
    object and patches it at runtime to include some extra useful methods that
    will allow other plugins to more easily use the IRC protocol.
"""
from plugins import event, mod

hook           = mod.hook
authentication = mod.authentication

def reply(self, message):
    """Replies to the channel a message was sent from."""
    prefix, command, args = self.parsed_message

    # Determine whether the message was from a query, or a channel.
    target = args[0] if args[0].startswith('#') else prefix.split('!')[0]
    self.raw('PRIVMSG {} :{}\r\n'.format(target, message))


def ctcp(self, target, message):
    """Send a ctcp response to a target."""
    self.send('NOTICE {} :\01{}\01'.format(target, message))


def say(self, channel, message):
    """Sends a message to the channel the event was received from."""
    self.raw('PRIVMSG {} :{}\r\n'.format(channel, message))


def notice(self, user, message):
    """Sends a notice to the channel an event was received from"""
    self.raw('NOTICE {} :{}\r\n'.format(user, message))


def action(self, channel, message):
    """Sends an action message to a target channel."""
    self.raw('PRIVMSG {} :\01ACTION {}\01\r\n'.format(channel, message))


def join(self, channel):
    """Join a target channel."""
    self.raw('JOIN {}\r\n'.format(channel))


def part(self, channel):
    """Leaves a channel."""
    self.raw('PART {}\r\n'.format(channel))


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
    container.action = action
    container.join   = join
    container.part   = part
    container.ctcp   = ctcp


# Implement commands wrapping core functionality of the bot. Allows controlling
# the bot more easily for regular IRC like behaviour.
@hook.command(['say'])
@authentication.authenticated(['Admin', 'Moderator'])
def _say(irc, nick, chan, msg, args, user):
    target, msg = msg.split(' ', 1)
    irc.say(target, msg)


@hook.command(['notice'])
@authentication.authenticated(['Admin', 'Moderator'])
def _notice(irc, nick, chan, msg, args, user):
    target, msg = msg.split(' ', 1)
    irc.notice(target, msg)


@hook.command(['action'])
@authentication.authenticated(['Admin', 'Moderator'])
def _action(irc, nick, chan, msg, args, user):
    target, msg = msg.split(' ', 1)
    print(repr(msg))
    irc.action(target, msg)


@hook.command(['join'])
@authentication.authenticated(['Admin', 'Moderator'])
def _join(irc, nick, chan, msg, args, user):
    irc.join(msg)


@hook.command(['part'])
@authentication.authenticated(['Admin', 'Moderator'])
def _part(irc, nick, chan, msg, args, user):
    irc.part(msg)


@hook.command(['kick'])
@authentication.authenticated(['Admin', 'Moderator'])
def _kick(irc, nick, chan, msg, args, user):
    target, *msg = msg.split(' ', 1)
    msg = 'Requested' if not msg else msg[0]
    irc.send('KICK {} {} :{}'.format(chan, target, msg))


@hook.command(['op'])
@authentication.authenticated(['Admin', 'Moderator'])
def _op(irc, nick, chan, msg, args, user):
    irc.send('MODE {} +o {}'.format(chan, msg))


@hook.command(['deop'])
@authentication.authenticated(['Admin', 'Moderator'])
def _deop(irc, nick, chan, msg, args, user):
    irc.send('MODE {} -o {}'.format(chan, msg))


@hook.command(['voice'])
@authentication.authenticated(['Admin', 'Moderator'])
def _voice(irc, nick, chan, msg, args, user):
    irc.send('MODE {} +v {}'.format(chan, msg))


@hook.command(['devoice'])
@authentication.authenticated(['Admin', 'Moderator'])
def _devoice(irc, nick, chan, msg, args, user):
    irc.send('MODE {} -v {}'.format(chan, msg))


# Preferably, don't use this. Adding it to test things on my own personal IRC
# instance. The bot being in oper mode is just bad news.
@hook.command(['oper'])
@authentication.authenticated(['Admin', 'Moderator'])
def _operator(irc, nick, chan, msg, args, user):
    irc.send('OPER {}'.format(msg))
