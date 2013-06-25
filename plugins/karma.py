"""
    Provides a Karma Bot. Works the same as every other IRC Karma bot with
    username++/--.
"""
from time import time
from collections import defaultdict
from plugins.commands import command, regex

karma_timer = defaultdict(lambda: 0)

def setup_db(irc):
    irc.db.execute('''
        CREATE TABLE IF NOT EXISTS karma (
            username TEXT COLLATE NOCASE,
            channel TEXT,
            karma INTEGER,
            PRIMARY KEY (username, channel)
        );
    ''')
    irc.db.commit()


@regex(r'^(\w+)(\+\+|--)')
def catch_karma(irc, nick, chan, match, args):
    setup_db(irc)

    target = match.group(1)
    # Prevent Karma spamming.
    if time() - karma_timer[nick.lower()] < 1800:
        return 'You manipulated karma too recently to change {}\'s life.'.format(target)

    karma_timer[nick.lower()] = time()
    if target in irc.userlist[chan]:
        # Setup a row for the user if one doesn't already exist, being careful
        # not to overwrite their karma if they do.
        irc.db.execute('INSERT OR IGNORE INTO karma VALUES (?, ?, ?)', (
            target,
            chan,
            0
        ))

        operation = match.group(2)
        if operation == '++':
            irc.db.execute('UPDATE karma SET karma = karma + 1 WHERE username = ? AND channel = ?', (target, chan))
            return '{}, you gained karma.'.format(target)

        if operation == '--':
            irc.db.execute('UPDATE karma SET karma = karma - 1 WHERE username = ? AND channel = ?', (target, chan))
            return '{}, you lost karma.'.format(target)


@command
def karma(irc, nick, chan, msg, args):
    """
    Inspect users karma in the current channel.
    .karma
    .karma <nick>
    """
    # Handle the case where the user has provided a username to find Karma
    # about, and return that Karma.
    if msg:
        try:
            user_karma = irc.db.execute('SELECT karma FROM karma WHERE username = ? AND channel = ?', (msg, chan)).fetchone()
            return 'Current karma for {} is: {}'.format(msg, user_karma[0])
        except Exception as e:
            print(e)
            return 'I haven\'t got any karma records for {}.'.format(msg)

    # Otherwise, return a list of the top 5 Karma users in the channel.
    karma_string = 'Top Karma: '
    users_karma = irc.db.execute('SELECT username, karma FROM karma WHERE channel = ? ORDER BY karma DESC LIMIT 5', (chan,)).fetchall()
    for user in users_karma:
        karma_string += '{}: {}, '.format(*user)

    return karma_string[:-2]
