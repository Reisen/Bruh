import json
from urllib.parse import quote_plus
from urllib.request import urlopen
from re import sub
from bruh import command

def wikisearch(irc, msg):
    try:
        url   = "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={}&srprop=timestamp&format=json"
        query = json.loads(urlopen(url.format(quote_plus(msg)), timeout = 7).read().decode('UTF-8'))
        query = [x['title'] for x in query['query']['search'][:5]]

        # Removing the [] that surround our titles for channel printing.
        return str(query)[1:-1]

    except:
        return "No articles were found for those search terms."


def wikiget(irc, msg):
    try:
        url  = "https://en.wikipedia.org/w/api.php?format=json&action=query&prop=extracts&titles={}&redirects=true"
        text = json.loads(urlopen(url.format(quote_plus(msg)), timeout = 7).read().decode('UTF-8'))

        # One of the keys is just a random number that we can't/won't predict.
        key = list(text['query']['pages'])[0]

        return "{}... - https://en.wikipedia.org/wiki/{}".format(
            sub(r'\<.*?>|\n','', text['query']['pages'][key]['extract'])[:400],
            text['query']['pages'][key]['title'].replace(' ', '_')
        )

    except Exception as e:
        return "No article was found with that title."


@command('wikipedia')
@command('wiki')
@command('wik')
@command('w')
def wikipedia(irc):
    if not irc.message:
        return "Syntax: .wiki <Article Title>"

    try:
        cmd, *args = irc.message.split(' ', 1)
        return {
            'search': wikisearch
        }[cmd](irc, *args)

    except Exception as e:
        return wikiget(irc, irc.message)
