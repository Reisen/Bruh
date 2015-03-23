from random import randint
from bruh import command, regex, r

@command('remember')
@command('r')
def remember(irc):
    if not irc.message:
        return "Syntax .remember <key> <value>"

    key, *value = irc.message.split(' ', 1)
    if not value:
        return "Syntax .remember <key> <value>"

    if key == 'rand':
        return "I can't remember random tings."

    facts = r.hget(irc.key + ':remember', key)
    if facts is None:
        r.hset(irc.key + ':remember', key, value[0])
        return "I'll remember that."

    facts = facts.decode('UTF-8')
    if facts == value[0]:
        return "I already knew that, tell me something I don't know."

    r.hset(irc.key + ':remember', key, facts + ', ' + value[0])
    return "Got it."


@regex(r'^\?([^\s]+)$')
def recall(irc, match):
    if match.group(1) == 'rand':
        maximum = r.hlen(irc.key + ':remember')
        index   = randint(0, maximum)
        counter = 0

        for k, v in r.hscan_iter(irc.key + ':remember'):
            k, v = k.decode('UTF-8'), v.decode('UTF-8')
            if counter == index:
                return '{}: {}'.format(k, v)

            counter += 1

        return None

    facts = r.hget(irc.key + ':remember', match.group(1))
    print('"{}" = "{}"'.format(match.group(1), facts))

    if facts is None:
        return None

    facts = facts.decode('UTF-8')
    facts = facts.replace('$nick', irc.nick)
    facts = facts.replace('$chan', irc.channel)

    if facts.startswith('@a'):
        return '\01ACTION ' + facts[:2] + '\01'

    if facts.startswith('@r'):
        return facts[:2]

    return '{}: {}'.format(match.group(1).strip(), facts)
