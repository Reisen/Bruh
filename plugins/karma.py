import re
from bruh import command, regex, sink, r
from plugins.userlist import networks, current
from walnut.drivers import Walnut


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
def karma_match(irc, match):
    if match.group(1) not in networks[irc.network][irc.channel].users:
        return None

    if match.group(1) == 'Warpten':
        return None

    if match.group(1) == 'Moto-chan' and match.group(2) == '--':
        return 'WAI!? How could you!? :<'

    if match.group(1) == 'hreb' and match.group(2) == '++':
        return 'There is no redemption for hreb, there can be no return from the path to karma hell.'

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
