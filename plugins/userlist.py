"""
    This plugin keeps track of user lists for channels that the bot is idling
    in, these are exposed to other plugins through the irc object.
"""
from plugins import event
from plugins.commands import command
from collections import defaultdict


@event('BRUH')
def prepare_userlist(irc):
    """Load a userlist dict into irc objects."""
    # Attach a userlist dict to each server. The keys are channels and the
    # values are sets of users.
    irc.userlist = defaultdict(lambda: set())


@event('353')
def parse_names(irc, prefix, command, args):
    """Parse RPLNAMREPLY messages in response to /NAMES or a join."""

    # Begin adding users to the userlist from responses.
    for user in args[3].split(' '):
        # Remove status characters.
        if user[0] in '!+&%@~':
            user = user[1:] 

        irc.userlist[args[2]].add(user)


@event('JOIN')
def join_userlist(irc, prefix, command, args):
    """Add users to the userlist when they join."""
    nick, chan = prefix.split('!')[0], args[0]

    # Add the user to the set, if the user is already in the set nothing
    # happens.
    irc.userlist[chan].add(nick)


@event('PART')
def part_userlist(irc, prefix, command, args):
    """Remove users from the userlist when they part."""
    nick, chan = prefix.split('!')[0], args[0]

    # If we're not tracking the user, we can't remove them.
    if nick in irc.userlist[chan]:
        irc.userlist[chan].remove(nick)


@event('KICK')
def kick_userlist(irc, prefix, command, args):
    """Remove users from the userlist when they are kicked."""
    nick, chan = args[1], args[0]

    # If we're not tracking the user, we can't remove them.
    if nick in irc.userlist[chan]:
        irc.userlist[chan].remove(nick)


@event('QUIT')
def quit_userlist(irc, prefix, command, args):
    """Removes users from all userlists if they quit."""
    nick = prefix.split('!')[0]

    # Unlike other events, we don't know which channel a QUIT event comes from,
    # so we just try and remove them from ALL channels.
    for userlist in irc.userlist.values():
        if nick in userlist:
            userlist.remove(nick)
