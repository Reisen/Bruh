import json
from random import choice
from urllib.parse import quote_plus, unquote_plus
from urllib.request import urlopen, Request
from bruh import command


@command('porn')
@command('po')
@command('p')
def pornmd(irc):
    '''Return peoples live searches from PornMD'''
    orientation = 's'
    if irc.message and irc.message[0] in 'gts':
        orientation = irc.message[0]

    request = Request(
        'http://www.pornmd.com/getliveterms?orientation={}'.format(orientation),
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11'
        }
    )

    try:
        query = json.loads(urlopen(request, timeout = 7).read().decode('UTF-8'))
        query = [choice(query)['keyword'] for _ in range(6)]
        return 'Recent PornMD Searches: {}'.format(', '.join(query))

    except Exception as e:
        return str(e)
