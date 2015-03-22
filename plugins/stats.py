from bruh import command, sink, r
from walnut.drivers import Walnut


def stat(name, value, *key): r.hset('{}:stats'.format(':'.join(key).lower()), name, value)
def incr(name, count, *key): r.hincrby('{}:stats'.format(':'.join(key).lower()), name, count)


@sink
def stat_handler(irc):
    incr('messages', 1, irc.network, irc.channel)
    incr('messages', 1, irc.network, irc.channel, irc.nick)
    incr('words', len(irc.message.split()), irc.network, irc.channel, irc.nick)

    # Generate Word Cloud
    words = irc.message.split()
    pipe  = r.pipeline()
    for word in words:
        pipe.hincrby(irc.key + ':cloud', word, 1)

    pipe.execute()


@command('stat')
def get_stat(irc):
    if not irc.message:
        return None

    stat = r.hget('{}:stats'.format(':'.join([irc.network, irc.channel])), irc.message)
    if stat:
        return 'Statistic Value: {}'.format(stat.decode('UTF-8'))
