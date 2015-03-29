import re
import random
from bruh import command, r, sink
from plugins.userlist import networks
from walnut.drivers import Walnut


def add_expression(irc, arg):
    try:
        matcher, result = arg.split('<=>')
        r.hset(irc.key + ':regular', matcher.strip(), result.strip())
        return "Expression successfully added."

    except Exception as e:
        return "Provide a proper expression. Syntax: expression <=> replacement"


def global_expression(irc, arg):
    try:
        matcher, result = arg.split('<=>')
        r.hset(irc.network + ':regular', matcher.strip(), result.strip())
        return "Expression successfully added."

    except Exception as e:
        return "Provide a proper expression. Syntax: expression <=> replacement"


def del_expression(irc, arg):
    matcher, process, result = try_expression(
        ['{}:{}:regular'.format(irc.network, irc.channel), irc.network + ':regular'],
        arg
    )

    if matcher:
        r.hdel(irc.key + ':regular', process)
        r.hdel(irc.network + ':regular', process)
        return "The expression matching your message has been deleted."

    return "No expressions matched this string."


def debug_expression(irc, arg):
    matcher, process, result = try_expression(
        ['{}:{}:regular'.format(irc.network, irc.channel), irc.network + ':regular'],
        arg
    )

    if matcher:
        return "The expression that matched: {}".format(process)

    return "No expressions matched this string."


def try_expression(keys, message):
    for key in keys:
        for matchpair in r.hscan_iter(key):
            result  = matchpair[1].decode('UTF-8')
            process = matchpair[0].decode('UTF-8')
            matcher = re.match(process, message, re.I)
            if matcher:
                return (matcher, process, result)

    return (None, None, None)


@sink
def regular_sink(irc):
    matcher, process, result = try_expression(
        ['{}:{}:regular'.format(irc.network, irc.channel), irc.network + ':regular'],
        irc.message
    )

    if matcher:
        keyspace = {"\\" + str(k + 1): v for k, v in enumerate(matcher.groups())}
        keyspace = dict(keyspace.items() | {
            "channel": irc.channel,
            "nick":    irc.nick,
            "rand1":   lambda: random.sample(networks[irc.network][irc.channel].users, 1)[0],
            "rand2":   lambda: random.sample(networks[irc.network][irc.channel].users, 1)[0],
            "rand3":   lambda: random.sample(networks[irc.network][irc.channel].users, 1)[0],
            "rand4":   lambda: random.sample(networks[irc.network][irc.channel].users, 1)[0],
            "rand5":   lambda: random.sample(networks[irc.network][irc.channel].users, 1)[0],
            "rand6":   lambda: random.sample(networks[irc.network][irc.channel].users, 1)[0]
        }.items())

        for k, v in keyspace.items():
            if callable(v):
                keyspace[k] = keyspace[k]()

        return result.format(**keyspace)


@command('re')
def regular(irc):
    if not irc.message:
        return None

    try:
        cmd, *args = irc.message.split(' ', 1)
        return {
            'add':    add_expression,
            'del':    del_expression,
            'global': global_expression,
            'debug':  debug_expression
        }[cmd](irc, *args)

    except KeyError:
        return "Unknown subcommand: {}".format(cmd)
