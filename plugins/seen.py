from time import time
from bruh import command, r
from drivers.walnut import Walnut

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
        return "Syntax: .tell <nick> <msg>"

    msg, *args = irc.message.split(' ', 1)
    if not args:
        return "Syntax: .tell <nick> <msg>"

    # Save the message in the database to be sent at a later time.
    r.lpush(irc.key + ':{}:tell'.format(msg.lower()), 'From {}: {}'.format(irc.nick, args[0]))
    return 'I will pass that along.'


@command('seen')
def seen(irc):
    if not irc.message:
        return 'Who am I looking for?'

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
                msg,
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
        return r.lindex(irc.key + ':last', -1).decode('UTF-8')

    count = int(irc.message)
    return b' '.join(r.lrange(irc.key + ':last', 0, count - 1)).decode('UTF-8')


@Walnut.hook('PRIVMSG')
def watch_channel(message):
    if message.args[0][0] == '#':
        # Get relevant information to track when seeing users say things.
        nick = message.prefix.split('!')[0]
        chan = message.args[0]
        key  = message.parent.frm + ':' + chan
        msg  = message.args[-1]
        r.hset(key + ':seen', nick.lower(), '{}|{}'.format(time(), msg))
        r.lpush(key + ':last', '<{}> {}'.format(nick, msg))
        r.ltrim(key + ':last', 0, 10)

        # Check if any messages need to be passed on.
        if r.llen(key + ':{}:tell'.format(nick.lower())) > 0:
            return 'NOTICE {} :{}'.format(
                nick,
                r.lpop(key + ':{}:tell'.format(nick.lower())).decode('UTF-8')
            )
        #messages = irc.db.execute('SELECT * FROM tell WHERE nick = ? and chan = ?', (nick.lower(), chan)).fetchall()
        #for message in messages:
        #    irc.notice(nick, message[3])
        #    irc.db.execute('DELETE FROM tell WHERE id = ?', (message[0],))


