from plugins import event
from plugins.commands import command
from collections import defaultdict

logs = defaultdict(lambda: [])

@event('PRIVMSG')
def message_tracker(irc, prefix, command, args):
    """
    Keeps short logs of recently seen channels for substitution in other
    commands.
    """
    channel = args[0]
    if channel[0] != '#':
        return

    logs[channel].append(args[1])
    if len(logs[channel]) > 5:
        logs[channel] = logs[channel][1:]


@command
def last(irc, nick, chan, msg, args):
    try:    return logs[chan][-1]
    except: return None
