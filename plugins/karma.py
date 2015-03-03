import re
from bruh import command, regex, sink, r
from plugins.userlist import userlist, current
from drivers.walnut import Walnut


last_sender = {}


@command('karma')
@command('k')
def karma(irc):
    karma = []
    for k in r.hscan_iter(irc.key + ':karma'):
        karma.append(k)

    karma = sorted(karma, key = lambda v: int(v[1]), reverse = True)

    karmees = []
    for karmee in karma[:5]:
        nick   = current(irc.network, karmee[0].decode('UTF-8'))
        amount = karmee[1].decode('UTF-8')
        karmees.append((nick, amount))

    return 'Top Karma: ' + ', '.join(map(lambda v: ': '.join(v), karmees))


@regex(r'([\w\[\]\\`_\^\{\}\|-]+)(\+\+|--)')
def match_karma(irc, match):
    if match.group(1) not in userlist[irc.network][irc.channel]:
        return None

    timeout = r.setnx(irc.key + ':karma:' + irc.nick.lower(), '')
    if not timeout:
        return 'You meddled with karma too recently to affect {}.'.format(match.group(1))

    direction   = 1 if match.group(2) == '++' else -1
    incremented = r.hincrby(irc.key + ':karma', match.group(1).lower(), direction)
    r.expire(irc.key + ':karma:' + irc.nick.lower(), 1800)

    return '{0} {1} karma. {0} now has {2}.'.format(
        match.group(1),
        'gained' if direction == 1 else 'lost',
        incremented
    )
