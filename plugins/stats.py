"""
    Keep track of statistics about users. Used for a PISG style statistics
    generator.
"""
import re
from plugins import event, mod

userlist = mod.userlist

def setup_db(irc):
    irc.db.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            nick TEXT COLLATE NOCASE,
            stat TEXT,
            chan TEXT,
            value TEXT,
            PRIMARY KEY(nick, stat, chan)
        );
    ''')
    #irc.db.execute('''CREATE UNIQUE INDEX IF NOT EXISTS idx_stats ON stats (nick, stat);''')


def record_stat(irc, nick, chan, stat, value = None, updater = None, default = None):
    """
    This function sets a stat for a certain user to a value. If an updater
    function is passed, it is passed the old value to be used to calculate a
    new value. If there was no old value, the updater value receives value
    passed in the default argument.
    """
    if updater:
        old_value = irc.db.execute('SELECT value FROM stats WHERE stat = ? AND nick = ? AND chan = ?', (stat, nick, chan)).fetchone()
        if old_value:
            default, = old_value

        value = updater(default)

    irc.db.execute('INSERT OR REPLACE INTO stats (nick, stat, chan, value) VALUES (?, ?, ?, ?)', (nick, stat, chan, value))


@event('PRIVMSG')
def message_stats(irc, prefix, command, args):
    try:
        if args[0][0] == '#':
            setup_db(irc)

            # Extract important information from the IRC args. The args argument is
            # the raw IRC message information so we have to get this out ourselves.
            nick = prefix.split('!')[0]
            chan = args[0]
            mesg = args[1]

            # Count total number of lines a user has said.
            def increment(old_value):
                return int(old_value) + 1

            record_stat(irc, nick, chan, 'Messages', updater = increment, default = 0)

            # Count total number of words a user has said.
            def count_words(old_value):
                return len(mesg.split()) + int(old_value)

            record_stat(irc, nick, chan, 'Words', updater = count_words, default = 0)

            # Count highlights for any highlight in the message.
            for username in irc.userlist[chan]:
                highlight = r'\b{}\b'.format(re.escape(username))
                if re.search(highlight, mesg, re.I):
                    record_stat(irc, username, chan, 'Highlight', updater = increment, default = 0)

            # Count questions asked.
            if mesg.endswith('?'):
                record_stat(irc, nick, chan, 'Questions', updater = increment, default = 0)

            # Count exclamations made.
            if mesg.endswith('!'):
                record_stat(irc, nick, chan, 'Yells', updater = increment, default = 0)

            # Count all uppercase messages.
            if mesg.upper() == mesg:
                record_stat(irc, nick, chan, 'Uppercase', updater = increment, default = 0)

            # Find racist users.
            slurs = [
                'nigger', 'negroid', 'nignog', 'nigga', 'honky', 'chink', 'kike',
                'cholo', 'abo', 'gringo', 'honkey', 'paki', 'sambo',
                'spearchucker', 'wetback'
            ]
            for slur in slurs:
                if re.search(r'\b{}'.format(re.escape(slur)), mesg, re.I):
                    record_stat(irc, nick, chan, 'Racist', updater = increment, default = 0)
                    break

            # Find gay users.
            slurs = [
                'gay', 'faggot'
            ]
            for slur in slurs:
                if re.search(r'\b{}'.format(re.escape(slur)), mesg, re.I):
                    record_stat(irc, nick, chan, 'Gay', updater = increment, default = 0)
                    break

            # TODO: Find emoticons used.
            print('Recording Stat')

            # Calculate average line length.
            def calculate_average(old_average):
                # Calculate the cumulative moving average, but only if we have a
                # line count.
                line_count = irc.db.execute('SELECT value FROM stats WHERE stat = ? AND nick = ? AND chan = ?', ('Messages', nick, chan)).fetchone()
                if not line_count:
                    return old_average

                i        = int(line_count[0])
                ca_last  = len(mesg) + i * float(old_average)
                ca_last /= i + 1
                return ca_last

            record_stat(irc, nick, chan, 'Average', updater = calculate_average, default = 0.0)

    except Exception as e:
        print(str(e))
