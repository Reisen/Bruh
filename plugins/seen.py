from time import time
from bruh import command, sink, r
from walnut.drivers import Walnut

distances = (
    (60 * 60 * 24 * 365, 'year'),
    (60 * 60 * 24 * 30, 'month'),
    (60 * 60 * 24 * 7, 'week'),
    (60 * 60 * 24, 'day'),
    (60 * 60, 'hour'),
    (60, 'minute')
)


def setup_db(irc):
    irc.db.execute('''
        CREATE TABLE IF NOT EXISTS seen (
            id INTEGER PRIMARY KEY,
            nick TEXT,
            chan TEXT,
            message TEXT,
            seen INTEGER
        );
    ''')
    irc.db.execute('''
        CREATE TABLE IF NOT EXISTS tell (
            id INTEGER PRIMARY KEY,
            nick TEXT,
            chan TEXT,
            message TEXT
        );
    ''')
    irc.db.execute('''CREATE UNIQUE INDEX IF NOT EXISTS idx_seen ON seen (nick, chan);''')
    irc.db.commit()


@command('tell')
def tell(irc):
    # Check the arguments given are actually correct.
    if not irc.message:
        return None

    msg, *args = irc.message.split(' ', 1)
    if not args:
        return "Syntax: .tell <nick> <msg>"

    # Save the message in the database to be sent at a later time.
    r.lpush(irc.key + ':{}:tell'.format(msg.lower()), 'From {}: {}'.format(irc.nick, args[0]))
    return 'I will pass that along.'


@command('seen')
def seen(irc):
    if not irc.message:
        return None

    # Try and see if we've even seen the person.
    user = r.hget(irc.key + ':seen', irc.message.lower())
    if not user:
        return 'I\'ve never seen {}.'.format(irc.message)

    # Distances contains a list of distances from longest to shortest, year to
    # minutes, we try each one to see if the distance is longer than each, and
    # if it is, we return just that distance.
    timedist, message = user.decode('UTF-8').split('|', 1)
    for distance in distances:
        current_distance = (time() - float(timedist)) // distance[0]
        if current_distance:
            return '{} was last seen {} {} ago saying: {}'.format(
                irc.message,
                int(current_distance),
                distance[1] + (['', 's'][current_distance > 1]),
                message
            )

    return '{} was here just now, {} seconds ago saying: {}'.format(
        irc.message,
        int(time() - float(timedist)),
        message
    )


@command('last')
def seen(irc):
    if not irc.message:
        return r.lindex(irc.key + ':last', 0).decode('UTF-8')

    count = int(irc.message)
    return b' '.join(reversed(r.lrange(irc.key + ':last', 0, count - 1))).decode('UTF-8')


@sink
def seen_sink(irc):
    if irc.channel[0] != '#':
        return None

    r.hset(irc.key + ':seen', irc.nick.lower(), '{}|{}'.format(time(), irc.message))
    r.lpush(irc.key + ':last', '<{}> {}'.format(irc.nick, irc.message))
    r.ltrim(irc.key + ':last', 0, 10)

    # Check if any messages need to be passed on.
    tell_key = irc.key + ':{}:tell'.format(irc.nick.lower())
    if r.llen(tell_key) > 0:
        return lambda: 'NOTICE {} :{}'.format(irc.nick, r.lpop(tell_key).decode('UTF-8'))
