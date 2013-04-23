"""
    Track user activity, and leave messages for users who aren't currently
    in the channel.
"""
from time import time
from plugins import event
from plugins.commands import command

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
    irc.db.execute('''CREATE UNIQUE INDEX IF NOT EXISTS idx_seen ON seen (nick, chan)''')
    irc.db.commit()


@command
def seen(irc, nick, chan, msg, args):
    """
    Check when a user was last seen.
    .seen <nick>
    """
    if not msg:
        return 'Who am I looking for?'

    # Try and see if we've even seen the person.
    setup_db(irc)
    user = irc.db.execute('SELECT * FROM seen WHERE nick = ? and chan = ?', (msg, chan)).fetchone()
    if not user:
        return 'I\'ve never seen {}.'.format(msg)

    # Distances contains a list of distances from longest to shortest, year to
    # minutes, we try each one to see if the distance is longer than each, and
    # if it is, we return just that distance.
    for distance in distances:
        current_distance = (time() - user[4]) // distance[0]
        if current_distance:
            return '{} was last seen {} {} ago saying: {}'.format(
                msg,
                int(current_distance),
                distance[1] + (['', 's'][current_distance > 1]),
                user[3]
            )

    return '{} was here just now, {} seconds ago saying: {}'.format(
        msg,
        int(time() - user[4]),
        user[3]
    )


@event('PRIVMSG')
def watch_channel(irc, prefix, command, args):
    if args[0][0] == '#':
        setup_db(irc)

        # Get relevant information to track when seeing users say things.
        nick = prefix.split('!')[0]
        chan = args[0]
        mesg = args[1]
        last = time()
        irc.db.execute('INSERT OR REPLACE INTO seen (nick, chan, message, seen) VALUES (?, ?, ?, ?)', (
            nick, chan, mesg, last
        ))
