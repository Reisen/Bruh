"""
    This plugin keeps track of user lists for channels that the bot is idling
    in, these are exposed to other plugins through the irc object.
"""
from plugins.bruh import event
from plugins.commands import command


@event('BRUH')
def prepare_userlist(irc):
    """Load a userlist dict into irc objects."""
    # Attach a userlist dict to each server.
    irc.userlist = {}


@event('353')
def parse_names(irc, prefix, command, args):
    """ Parse RPLNAMREPLY messages in response to /NAMES or onjoin."""
    # If the channel isn't being tracked yet, it should be. We use sets because
    # they just fit well here. Dupe users automatically removed etc.
    if args[2] not in irc.userlist:
        irc.userlist[args[2]] = set()

    print('Parsing users on JOIN')

    # Begin adding users to the userlist from responses.
    for user in args[3].split(' '):
        # Remove status characters.
        if user[0] in '!+&%@~':
            user = user[1:]

        irc.userlist[args[2]].add(user)

    print('Parsed incoming /names:\n\t', str(irc.userlist[args[2]]))


@event('JOIN')
def join_userlist(irc, prefix, command, args):
    """Add users to the userlist when they join."""
    nick, chan = prefix.split('!')[0], args[0]

    # If we aren't tracking a channel, we should be.
    if chan not in irc.userlist:
        irc.userlist[chan] = set()

    # If we're already tracking the user, we shouldn't re-add them.
    if nick not in irc.userlist[chan]:
        irc.userlist[chan].add(nick)

    print(irc.userlist[chan])


@event('PART')
def part_userlist(irc, prefix, command, args):
    """Remove users from the userlist when they part."""
    nick, chan = prefix.split('!')[0], args[0]

    # If we aren't tracking a channel, we should be.
    if chan not in irc.userlist:
        irc.userlist[chan] = set()

    # If we're already tracking the user, we shouldn't re-add them.
    if nick in irc.userlist[chan]:
        irc.userlist[chan].remove(nick)

    print(irc.userlist[chan])


@event('KICK')
def kick_userlist(irc, prefix, command, args):
    """Remove users from the userlist when they are kicked."""
    nick, chan = args[1], args[0]

    # If we aren't tracking a channel, we should be.
    if chan not in irc.userlist:
        irc.userlist[chan] = set()

    # If we're already tracking the user, we shouldn't re-add them.
    if nick in irc.userlist[chan]:
        irc.userlist[chan].remove(nick)

    print(irc.userlist[chan])


@event('QUIT')
def quit_userlist(irc, prefix, command, args):
    """Removes users from all userlists if they quit."""
    nick = prefix.split('!')[0]

    # Unlike other events, we don't know which channel a QUIT event comes from,
    # so we remove them from ALL channels.
    for userlist in irc.userlist.values():
        userlist.remove(nick)
