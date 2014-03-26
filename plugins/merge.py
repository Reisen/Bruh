"""
    Merge with the bot with a channel. All messages from the channel are
    forwarded through a PRIVMSG from the bot, all messages to the bot to the
    channel. Used to spoof identity as the bot.
"""
from time import sleep
from plugins import event
from plugins.commands import command
from plugins.authentication import authenticated
from collections import defaultdict

merge_list = defaultdict(lambda:set())

@event('PRIVMSG')
def merge_thru(irc, prefix, command, args):
    global merge_list
    if args[1].startswith(irc.config.get('prefix', '.')):
        return None

    username = prefix.split('!')[0]

    # Pipe messages from channel -> user.
    if args[0].startswith('#') or username in merge_list:
        target = args[0] if args[0].startswith('#') else username
        for target in merge_list[target]:
            irc.say(target, '<{}:{}> {}'.format(args[0], username, args[1]))
            sleep(0.1)

    # Pipe messages from user -> channel.
    elif args[0] == irc.nick:
        # Find all targets that the user currently is merged to.
        mergers = []
        for key in merge_list:
            if username in merge_list[key]:
                mergers.append(key)

        # If we're using more than one target, we don't want to spam all
        # channels so we just disallow it.
        if len(mergers) > 1:
            irc.say(username, 'You are merged to more than one channel. Talking only works with one marge target.')
            return None

        if len(mergers) == 1:
            irc.say(mergers[0], args[1])


@command
@authenticated(['Admin', 'Moderator'])
def merge(irc, nick, chan, msg, args, user):
    """
    Merge with the bot.
    .merge <chan>
    """
    global merge_list

    if not msg:
        targets = []
        for target in merge_list:
            if nick in merge_list[target]:
                targets.append(target)

        return 'Currently merged to: {}'.format(', '.join(targets))

    merge_target = merge_list[msg]
    if nick in merge_target:
        merge_target.remove(nick)
        return 'Removed merging with channel: {}'.format(msg)

    merge_target.add(nick)
    return 'Merged with channel: {}'.format(msg)
