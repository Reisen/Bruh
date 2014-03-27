"""
    This plugin keeps track of user lists for channels that the bot is idling
    in, these are exposed to other plugins through the irc object. As well as
    the current state of the user-list, it also provides hooking callbacks for
    when users leave or join.
"""
from plugins import event
from plugins.commands import command
from collections import defaultdict
from functools import wraps


def min_mode(irc, nick, chan, min_mode):
    # Only allow the command to continue if the user executing the command is
    # ofthe right mode level. The mode given is the minimum level to execute,
    # so if voice is the level then any user above can too.
    modes = irc.modelist[chan][nick]['mode']
    umode = 0
    for mode in modes:
        level = '+%@&~'.find(mode) + 1
        if level > umode:
            umode = level

    # Find out what the minimum mode level for this command is.
    req_mode = '+%@&~'.find(min_mode) + 1

    # If we're the right level, we're good to go.
    return umode >= req_mode


def mode(req_mode):
    def mode_function(f):
        @wraps(f)
        def mode_wrapper(irc, nick, chan, msg, irc_args, *args, **kwargs):
            if min_mode(irc, nick, chan, req_mode):
                return f(irc, nick, chan, msg, irc_args, *args, **kwargs)

            return "You need a mode of at least {}({}) to use this command.".format({
                '+': 'voiced',
                '%': 'hopped',
                '@': 'opped',
                '&': 'protected',
                '~': 'owner'
            }[req_mode], req_mode)

        return mode_wrapper

    return mode_function


@command
@mode('%')
def usercount(irc, nick, chan, msg, args):
    return "There are {} users in the channel currently.".format(len(irc.userlist[chan]))


@event('BRUH')
def prepare_userlist(irc):
    """Load a userlist dict into irc objects."""
    # Attach a userlist dict to each server. The keys are channels and the
    # values are sets of users.
    irc.userlist = defaultdict(set)

    # Same as previous, except with the addition of extra details such as the
    # users mode. Keys are still channels with dictionaries for the users and
    # their details.
    irc.modelist = defaultdict(dict)


@event('353')
def parse_names(irc, prefix, command, args):
    """Parse RPLNAMREPLY messages in response to /NAMES or a join."""
    for user in args[3].split(' '):
        # Remove status characters, and store them in a mode string. Sadly if
        # users have more than one mode some servers are retarded and will send
        # just @x instead of @+x. And so if a user who is @+x is deopped, we
        # will not know they are voiced. This issue is present in irssi too so
        # as far as I can tell It's a server-side fault that I really can't do
        # anything about.
        mode = set()
        while user[0] in '!+&%@~':
            mode.add(user[0])
            user = user[1:]

        irc.userlist[args[2]].add(user)
        irc.modelist[args[2]][user] = {
            'mode': mode
        }


@event('JOIN')
def join_userlist(irc, prefix, command, args):
    """Add users to the userlist when they join."""
    nick, chan = prefix.split('!')[0], args[0]

    # Add the user to the set, if the user is already in the set nothing
    # happens.
    irc.userlist[chan].add(nick)
    irc.modelist[chan][nick] = {
        'mode': set()
    }


@event('PART')
def part_userlist(irc, prefix, command, args):
    """Remove users from the userlist when they part."""
    nick, chan = prefix.split('!')[0], args[0]

    # If we're not tracking the user, we can't remove them.
    if nick in irc.userlist[chan]:
        irc.userlist[chan].remove(nick)
        del irc.modelist[chan][nick]


@event('KICK')
def kick_userlist(irc, prefix, command, args):
    """Remove users from the userlist when they are kicked."""
    nick, chan = args[1], args[0]

    # If we're not tracking the user, we can't remove them.
    if nick in irc.userlist[chan]:
        irc.userlist[chan].remove(nick)
        del irc.modelist[chan][nick]


@event('QUIT')
def quit_userlist(irc, prefix, command, args):
    """Removes users from all userlists if they quit."""
    nick = prefix.split('!')[0]

    # Unlike other events, we don't know which channel a QUIT event comes from,
    # so we just try and remove them from ALL channels.
    for channel, userlist in irc.userlist.items():
        if nick in userlist:
            userlist.remove(nick)

    for channel, modelist in irc.modelist.items():
        if nick in modelist:
            del modelist[nick]


@event('MODE')
def mode_userlist(irc, prefix, command, args):
    """Track changes in user modes in the channel."""
    try:
        chan, mode, *nicks = args
        nicks.reverse()

        mode_lookup = {
            'v': '+',
            'h': '%',
            'o': '@',
            'a': '&',
            'q': '~'
        }

        # Mode strings can consist of multiple flags, toggles, and arguments. We
        # just have to find the ones we care about though and make sure we track
        # them correctly.
        direction = False
        while mode:
            # Find out whether we're adding or removing flags, and eat the char.
            # Direction should persist until a new +/- is seen.
            if mode[0] in '+-':
                direction = True if mode[0] == '+' else False
                mode = mode[1:]

            # Voice(+), Halfop(%), Op(@), Protected(&), Owner(~)
            if mode[0] in 'vhoaq':
                target = nicks.pop()
                if direction:
                    irc.modelist[chan][target]['mode'].add(mode_lookup[mode[0]])
                else:
                    irc.modelist[chan][target]['mode'].remove(mode_lookup[mode[0]])

            # Eat the mode character and continue on.
            mode = mode[1:]

    except Exception as e:
        print(str(e))
