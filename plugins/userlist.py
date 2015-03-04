from bruh import command
from drivers.walnut import Walnut
from redis import StrictRedis
from collections import defaultdict
from itertools import dropwhile, takewhile
from functools import wraps


class User:
    def __init__(self, nick, modes = []):
        self.nick = nick
        self.mode = modes
        self.auth = False

    def __repr__(self):  return self.nick
    def __hash__(self):  return hash(self.nick)
    def __ne__(self, o): return not (self == o)
    def __eq__(self, o):
        if isinstance(o, str):
            return self.nick.lower() == o.lower()

        return self.nick.lower() == o.nick.lower()


class Chan:
    def __init__(self):
        self.users = set()
        self.topic = ""


botsnick = None
networks = defaultdict(lambda: defaultdict(Chan))
lownicks = defaultdict(lambda: defaultdict(User))


def auth(f):
    @wraps(f)
    def check_auth(irc, *args, **kwargs):
        print(irc.nick, lownicks[irc.network][irc.nick.lower()].auth)
        if not lownicks[irc.network][irc.nick.lower()].auth:
            irc.raw('WHOIS {}'.format(irc.nick))
            return 'You triggered an auth check. Try again.'

        return f(irc, *args, **kwargs)

    return check_auth


def current(network, nick):
    return lownicks[network].get(nick.lower(), User(nick)).nick


@command('testauth')
@auth
def testauth(irc):
    return 'Auth Command Invoked!'


@Walnut.hook('PRIVMSG')
def user_check(message):
    network = message.parent.frm
    channel = message.args[0]

    if not channel.startswith('#'):
        return None

    if channel not in networks[network]:
        return 'NAMES {}'.format(channel)

    if message.prefix.split('!')[0] not in networks[network][channel].users:
        return 'NAMES {}'.format(channel)


@Walnut.hook('353')
def user_join_rply(message):
    network = message.parent.frm
    channel = message.args[2]
    for user in message.args[3].split():
        name, modes = map(lambda v: ''.join(v(lambda u: u in '~&@%+', user)), (dropwhile, takewhile))
        user = User(name, modes)
        networks[network][channel].users.add(user)
        lownicks[network][name.lower()] = user


@Walnut.hook('JOIN')
def user_join(message):
    name    = message.prefix.split('!')[0]
    network = message.parent.frm
    channel = message.args[0]
    user    = User(name)
    networks[network][channel].users.add(user)
    lownicks[network][name.lower()] = user


@Walnut.hook('PART')
def user_part(message):
    name    = message.prefix.split('!')[0]
    network = message.parent.frm
    channel = message.args[0]
    if name in networks[network][channel].users:
        networks[network][channel].users.remove(name)
        del lownicks[network][name.lower()]


@Walnut.hook('KICK')
def user_kick(message):
    name    = message.args[1]
    network = message.parent.frm
    channel = message.args[0]
    if name in networks[network][channel].users:
        networks[network][channel].users.remove(name)
        del lownicks[network][name.lower()]


@Walnut.hook('QUIT')
def user_quit(message):
    name    = message.prefix.split('!')[0]
    network = message.parent.frm
    for channel in networks[network]:
        if name in networks[network][channel].users:
            networks[network][channel].users.remove(name)
            del lownicks[network][name.lower()]


@Walnut.hook('NICK')
def user_nick(message):
    name     = message.prefix.split('!')[0]
    network  = message.parent.frm
    new_name = message.args[0]
    for channel in networks[network]:
        if name in networks[network][channel].users:
            user = User(new_name)
            networks[network][channel].users.remove(name)
            networks[network][channel].users.add(user)
            del lownicks[network][name.lower()]
            lownicks[network][new_name.lower()] = user


@command('users')
def print_userlist(irc):
    return str(networks[irc.network][irc.channel].users)


@command('channels')
def print_chanlist(irc):
    return str(set(networks[irc.network].keys()))


@command('authed')
def print_authed(irc):
    return 'Authed: ' + str(lownicks[irc.network][irc.nick.lower()].auth)


@Walnut.hook('319')
def parse_whois_channels(message):
    global botsnick
    if message.args[0] != message.args[1]:
        if botsnick is None:
            return 'WHOIS ' + message.args[0]

        return None

    else:
        botsnick = message.args[0]

    network = message.parent.frm
    for channel in message.args[-1].split():
        channel = '#' + channel.rsplit('#', 1)[-1]
        channel = networks[network][channel]


@Walnut.hook('307')
def parse_whois_auth(message):
    if 'identified' in message.args[-1]:
        network = message.parent.frm
        nick    = message.args[1]
        lownicks[network][nick.lower()].auth = True

        return 'NOTICE {} :You have been authorized by the bot.'.format(
            message.args[1]
        )
