import random
from bruh import command, r


def random_quote(irc):
    count = r.llen(irc.key + ':quotes')
    index = random.randint(0, count - 1)
    quote = r.lindex(irc.key + ':quotes', index).decode('UTF-8')

    return 'Quote [{}/{}]: {}'.format(
        index + 1,
        count,
        quote
    )


def add_quote(irc, quote):
    r.rpush(irc.key + ':quotes', quote)
    return 'Awesome, saved.'


def del_quote(irc, quote):
    try:
        index = int(quote)
        r.lset(irc.key + ':quotes', index - 1, '_DELETE_')
        r.lrem(irc.key + ':quotes', 0, '_DELETE_')
        return 'Awesome, eliminated.'

    except:
        return "Make sure you are giving the quote's ID. I couldn't delete anything."


def search_quote(irc, quote):
    pieces = quote.split(' ', 1)

    try:
        if len(pieces) == 1 and pieces[0].isdigit():
            count = r.llen(irc.key + ':quotes')
            index = int(pieces[0]) - 1
            quote = r.lindex(irc.key + ':quotes', index).decode('UTF-8')
            reali = ''

        else:
            filtered = []
            unfiltered = r.lrange(irc.key + ':quotes', 0, -1)
            for target in unfiltered:
                target = target.decode('UTF-8')
                if pieces[len(pieces) - 1].lower() in target.lower():
                    filtered.append(target)

            count = len(filtered)
            index = int(pieces[0]) - 1 if pieces[0].isdigit() else random.randint(0, count - 1)
            quote = filtered[index]
            reali = ' ({})'.format(unfiltered.index(quote.encode('UTF-8')) + 1)

        return 'Quote [{}/{}]{}: {}'.format(
            index + 1,
            count,
            reali,
            quote
        )

    except Exception as e:
        return 'Could not find that quote.' + str(e)


@command('quote')
@command('q')
def quote(irc):
    if not irc.message:
        return random_quote(irc)

    try:
        cmd, *args = irc.message.split(' ', 1)
        return {
            'add':    add_quote,
            'del':    del_quote,
        }[cmd](irc, *args)

    except KeyError:
        return search_quote(irc, irc.message)
