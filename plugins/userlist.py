from bruh import command
from drivers.walnut import Walnut
from redis import StrictRedis
from collections import defaultdict
from itertools import dropwhile, takewhile


userlist = defaultdict(lambda: defaultdict(set))
usermap  = defaultdict(dict)


def current(network, nick):
    return usermap[network].get(nick.lower(), nick)


@Walnut.hook('PRIVMSG')
def user_check(message):
    if message.args[0] not in userlist[message.parent.frm]:
        return 'NAMES {}'.format(message.args[0])

    if message.prefix.split('!')[0] not in userlist[message.parent.frm][message.args[0]]:
        return 'NAMES {}'.format(message.args[0])


@Walnut.hook('353')
def user_join_rply(message):
    network = message.parent.frm
    channel = message.args[2]
    for user in message.args[3].split():
        name, modes = map(lambda v: ''.join(v(lambda u: u in '~&@%+', user)), (dropwhile, takewhile))
        userlist[network][channel].add(name)
        usermap[network][name.lower()] = name


@Walnut.hook('JOIN')
def user_join(message):
    name    = message.prefix.split('!')[0]
    network = message.parent.frm
    channel = message.args[0]
    userlist[network][channel].add(name)
    usermap[network][name.lower()] = name


@Walnut.hook('PART')
def user_part(message):
    name = message.prefix.split('!')[0]
    network = message.parent.frm
    channel = message.args[0]
    if name in userlist[network][channel]:
        userlist[network][channel].remove(name)
        del usermap[network][name.lower()]


@Walnut.hook('KICK')
def user_kick(message):
    name    = message.args[1]
    network = message.parent.frm
    channel = message.args[0]
    if name in userlist[network][channel]:
        userlist[network][channel].remove(name)
        del usermap[network][name.lower()]


@Walnut.hook('QUIT')
def user_quit(message):
    name    = message.prefix.split('!')[0]
    network = message.parent.frm
    for channel in userlist[network]:
        if name in userlist[network][channel]:
            userlist[network][channel].remove(name)
            del usermap[network][name.lower()]


@Walnut.hook('NICK')
def user_nick(message):
    name     = message.prefix.split('!')[0]
    network  = message.parent.frm
    new_name = message.args[0]
    for channel in userlist[network]:
        if name in userlist[network][channel]:
            userlist[network][channel].remove(name)
            userlist[network][channel].add(new_name)
            usermap[network][name.lower()] = name
            del usermap[network][name.lower()]


@command('users')
def print_userlist(irc):
    return str(userlist[irc.network][irc.channel])
