import json
from bruh import command
from random import randint
from urllib.parse import quote_plus, unquote_plus
from urllib.request import urlopen, Request
from html.parser import HTMLParser
from drivers.walnut import Walnut


@command('google')
@command('g')
def google(irc):
    if not irc.message:
        return ".g <search terms>"

    # Build the request. The Referer is required because of googles ToS.
    request = Request(
        'https://ajax.googleapis.com/ajax/services/search/web?v=1.0&q={}'.format(quote_plus(irc.message)),
        headers = {
            'Referer': 'http://github.com/Reisen/Walnut',
            'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11'
        }
    )

    # Then break it down to only the data we need (which is the first result of
    # our search.)
    try:
        # Searches are returned as JSON so we need to turn that into a
        # dictionary.
        query = json.loads(urlopen(request, timeout = 7).read().decode('UTF-8'))

        # Check for any statuses that aren't a successful search.
        if query['responseStatus'] != 200:
            return "Google returned: {}".format(query['responseStatus'])

        query = query['responseData']['results'][0]

        # Format the output for IRC.
        out = '{} -- \x02{}\x02: "{}"'.format(
            unquote_plus(query['url'], encoding='utf-8', errors='replace'),
            query['title'],
            query['content']
        )

        # Strip anything useless, replace HTML entities, and output.
        return HTMLParser().unescape(
            out.replace('<b>', '')
               .replace('</b>', '')
               .replace('\n', '')
               .strip()
        )

    except Exception as e:
        return 'No results found.'


@command('image')
@command('im')
@command('i')
def image(irc):
    if not irc.message:
        return "Syntax: .image <search terms>"

    url = 'https://ajax.googleapis.com/ajax/services/search/images?v=1.0&q={}&safe=off'

    # Searches are returned as JSON so we need to turn that into a dictionary
    query = json.loads(urlopen(url.format(quote_plus(irc.message)), timeout = 7).read().decode('UTF-8'))

    if query['responseStatus'] != 200:
        return query['responseStatus']

    # Then break it down to only the data we need in this case it's any of the
    # first 4 image results
    try:
        query = query['responseData']['results'][randint(0,3)]['url']
        return unquote_plus( query, encoding='utf-8', errors='replace' )

    except:
        return 'No results found'
