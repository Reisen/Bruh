"""
    Search google for some useless shit no one cares about
"""
from plugins.commands import command
from random import randint

from urllib.parse import quote_plus, unquote_plus
from urllib.request import urlopen
import json

@command(['g'])
def google(irc, nick, chan, msg, args):
    '''Google web search'''
    url = 'https://ajax.googleapis.com/ajax/services/search/web?v=1.0&q=%s'

    if not msg:
        return 'Need something to search for.'

    # Searches are returned as JSON so we need to turn that into a dictionary
    query = json.loads( urlopen( url % quote_plus( msg ) ).read().decode('UTF-8') )
    if query['responseStatus'] != 200:
        return query['responseStatus']

    # Then break it down to only the data we need (which is the first result of our search)
    try:
        query = query['responseData']['results'][0]

        # We have to cut out the bold tags in the title for some reason
        out = '%s -- \x02%s\x02: "%s"' % ( unquote_plus( query['url'], encoding='utf-8', errors='replace'), query['title'], query['content'] )

        return out.replace('<b>', '').replace('</b>', '')
    except:
        return 'No results found.'


@command
def image(irc, nick, chan, msg, args):
    '''Google image search (returns any of the first 4 results)'''
    url = 'https://ajax.googleapis.com/ajax/services/search/images?v=1.0&q=%s&safe=off'

    if not msg:
        return 'Need something to search for.'

    # Searches are returned as JSON so we need to turn that into a dictionary
    query = json.loads( urlopen( url % quote_plus( msg ) ).read().decode('UTF-8') )
    if query['responseStatus'] != 200:
        return query['responseStatus']

    # Then break it down to only the data we need in this case it's any of the
    # first 4 image results
    try:
        query = query['responseData']['results'][randint(0,3)]['url']

        return unquote_plus( query, encoding='utf-8', errors='replace' )
    except:
        return 'No results found'
