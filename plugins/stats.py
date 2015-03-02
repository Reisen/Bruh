from bruh import r, command
from drivers.walnut import Walnut


def stat(name, value, *key): r.hset('{}:stats'.format(':'.join(key).lower()), name, value)
def incr(name, count, *key): r.hincrby('{}:stats'.format(':'.join(key).lower()), name, count)


@Walnut.hook('PRIVMSG')
def stat_handler(message):
    network = message.parent.frm
    channel = message.args[0]
    nick    = message.prefix.split('!')[0]
    incr('messages', 1, network, channel)
    incr('messages', 1, network, channel, nick)
    incr('words', len(message.args[-1].split()), network, channel, nick)


@command('stat')
def get_stat(irc):
    if not irc.message:
        return None

    return 'Statistic Value: {}'.format(
        r.hget('{}:stats'.format(':'.join([irc.network, irc.channel])), irc.message).decode('UTF-8')
    )
