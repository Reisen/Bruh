"""
    This module keeps track of recently seen messages, so they can be printed
    with commands list .last, It's useful for small channels where you are
    disconnected and want to see a short backlog.
"""
from time import sleep
from plugins import event, mod
from collections import defaultdict

authentication = mod.authentication
hook           = mod.hook

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

    # Ignore messages that begin with a command prefix. I don't think there's
    # any point in logging them, might change this if I'm wrong.
    try:
        if args[1][0] == irc.config.get('prefix', '.'):
            return

        # Append the message to the end of the current channels log, along with the
        # nick of the user who sent it. Any messages further back than the last 30
        # are removed.
        logs[channel].append((prefix.split('!')[0], args[1]))
        if len(logs[channel]) > 30:
            logs[channel].pop(0)
    except:
        return


@hook.command
def last(irc, nick, chan, msg, args):
    """
    Print messages the bot has recently seen.
    .last [nick] [count] [with_nicks: yes/no]
    """
    try:
        # In the special case where .last is sent by itself, It's extremely
        # likely the person wants the last message to manipulate it, we can
        # escape early here and return it. In other words, .last by itself
        # is equivelent to:
        #
        #   .last nick 1 no
        if not msg:
            return logs[chan][-1][1]

        # Split up the pieces of the command to decide how to format the
        # returned logged messages.
        pieces = msg.split(' ')

        # Deal with target nicks to extract.
        nick_targets = []
        if pieces:
            targets = pieces.pop(0)

            # If the targets is a number, we can assume look-a-head and push
            # the number right back onto the head of the list instead.
            if targets.isdigit():
                pieces.insert(0, targets)
            else:
                nick_targets += targets.split(',')

        # Deal with how many messages to go back, default to 1.
        distance = 1
        if pieces:
            print(pieces)
            distance = int(pieces.pop(0))

        # Find out whether or not to prepend each message with the users nick
        # in IRC style: <bruh> Yes - Defaults to Yes.
        prefix = True
        if pieces:
            prefix = True if pieces.pop(0) == 'yes' else False

        # Here we construct the returned message based on the above options
        # that we parsed.
        counter = 0
        results = []
        for lnick, lmessage in reversed(logs[chan]):
            if counter == distance:
                break

            if nick_targets and lnick not in nick_targets:
                continue

            counter += 1
            results.append('<{}> {}'.format(lnick, lmessage) if prefix else lmessage)

        return ' '.join(reversed(results))

    except Exception as e:
        print(e)
        return None


@hook.command
@authentication.authenticated
def repeat(irc, nick, chan, msg, args, user):
    """
    Repeat messages the bot has recently seen. Identical to .last, but per line.
    .repeat [nick] [count] [with_nicks: yes/no]
    """
    try:
        # See comments for .last command above, code identical to below. This
        # is not good, the reason for the command duplication is authentication
        # is applied per command.
        #
        # TODO: More fine grained authentication to merge this code with the
        # above.
        if not msg:
            return logs[chan][-1][1]

        pieces = msg.split(' ')

        nick_targets = []
        if pieces:
            targets = pieces.pop(0)

            if targets.isdigit():
                pieces.insert(0, targets)
            else:
                nick_targets += targets.split(',')

        distance = 1
        if pieces:
            print(pieces)
            distance = int(pieces.pop(0))

        prefix = True
        if pieces:
            prefix = True if pieces.pop(0) == 'yes' else False

        counter = 0
        results = []
        for lnick, lmessage in reversed(logs[chan]):
            if counter == distance:
                break

            if nick_targets and lnick not in nick_targets:
                continue

            counter += 1
            results.append('<{}> {}'.format(lnick, lmessage) if prefix else lmessage)

        for m in reversed(results):
            irc.reply(m)
            sleep(0.4)

    except Exception as e:
        print(e)
        return None
