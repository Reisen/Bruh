import re
import random
from bruh import command, r
from plugins.userlist import userlist
from drivers.walnut import Walnut


def add_expression(irc, arg):
    try:
        matcher, result = arg.split('<=>')
        r.hset(irc.key + ':regular', matcher.strip(), result.strip())
        return "Expression successfully added."

    except Exception as e:
        return "Provide a proper expression. Syntax: expression <=> replacement"


def del_expression(irc, arg):
    matcher, process, result = try_expression(
        '{}:{}:regular'.format(irc.network, irc.channel),
        arg
    )

    if matcher:
        r.hdel(irc.key + ':regular', process)
        return "The expression matching your message has been deleted."

    return "No expressions matched this string."


def try_expression(key, message):
    for matchpair in r.hscan_iter(key):
        result  = matchpair[1].decode('UTF-8')
        process = matchpair[0].decode('UTF-8')
        matcher = re.match(process, message, re.I)
        if matcher:
            return (matcher, process, result)

    return (None, None, None)


@Walnut.hook('PRIVMSG')
def handle_regulars(message):
    network = message.parent.frm
    channel = message.args[0]
    nick    = message.prefix.split('!')[0]

    matcher, process, result = try_expression(
        '{}:{}:regular'.format(network, channel),
        message.args[-1]
    )

    if matcher:
        keyspace = {"\\" + str(k + 1): v for k, v in enumerate(matcher.groups())}
        keyspace = dict(keyspace.items() | {
            "channel": channel,
            "nick": nick,
            "rand1": lambda: random.sample(userlist[network][channel], 1)[0],
            "rand2": lambda: random.sample(userlist[network][channel], 1)[0],
            "rand3": lambda: random.sample(userlist[network][channel], 1)[0],
            "rand4": lambda: random.sample(userlist[network][channel], 1)[0],
            "rand5": lambda: random.sample(userlist[network][channel], 1)[0],
            "rand6": lambda: random.sample(userlist[network][channel], 1)[0]
        }.items())

        for k, v in keyspace.items():
            if callable(v):
                keyspace[k] = keyspace[k]()

        return "PRIVMSG {} :{}".format(
            channel,
            result.format(**keyspace)
        )


@command('re')
def regular(irc):
    if not irc.message:
        return None

    try:
        cmd, *args = irc.message.split(' ', 1)
        return {
            "add": add_expression,
            "del": del_expression
        }[cmd](irc, *args)

    except KeyError:
        return "Unknown subcommand: {}".format(cmd)
