import re
from bruh import command, r
from plugins.userlist import userlist
from drivers.walnut import Walnut


last_sender = {}


@command('karma')
@command('k')
def karma(irc):
    karma = []
    for k in r.hscan_iter(irc.key + ':karma'):
        karma.append(k)

    karma = sorted(karma, key = lambda v: v[1], reverse = True)
    return 'Top Karma: ' + ', '.join(map(lambda v: b': '.join(v).decode('UTF-8'), karma))


@Walnut.hook('PRIVMSG')
def match_karma(message):
    db_key  = '{}:{}'.format(message.parent.frm, message.args[0])
    nick    = message.prefix.split('!')[0]
    network = message.parent.frm
    channel = message.args[0]
    match   = re.match(r'([\w\[\]\\`_\^\{\}\|-]+)(\+\+|--)', message.args[-1])

    # Increment Karma through karma whoring means. Restricting this to every 30
    # minutes doesn't seem to stop people whoring, but It's here anyway.
    if match and match.group(1) in userlist[network][channel]:
        success = r.setnx(db_key + ':karma:{}'.format(nick), '')

        if success:
            r.expire(db_key + ':karma:{}'.format(match.group(1)), 1800)
            r.hincrby(db_key + ':karma', match.group(1), 1)
            output = '{0} gained karma. {0} now has {1}'.format(
                match.group(1),
                r.hget(db_key + ':karma', match.group(1)).decode('UTF-8')
            )

        else:
            output = 'You manipulated the waves too recently to affect {}\'s karma.'.format(match.group(1))

        return 'PRIVMSG {} :{}'.format(
            channel,
            output
        )

    # Catch passive thanks and increment karma from it.
    match = re.match(r'^thanks?(:?\syou)?(\s.+)?$', message.args[-1], re.I)
    if match:
        target  = match.group(2) if match.group(2) else last_sender.get(channel, 'DekuNut')
        success = r.setnx(db_key + ':thank:{}'.format(target.strip()), '')

        if success:
            r.expire(db_key + ':thank:{}'.format(target), 60)
            r.hincrby(db_key + ':karma', target, 1)
            return None

    # Store the last sender if no karma-whoring was done. This is so when users
    # thank without specifying a name, we can just grant the thanks to who we
    # are assuming the thankee is.
    last_sender[channel] = nick
