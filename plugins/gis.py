"""
    Search google for some useless shit no one cares about
"""
from plugins.commands import command
from random import randint

from urllib.parse import quote_plus, unquote_plus
from urllib.request import urlopen
import json

@command
def gis(irc, nick, chan, msg, args):
    '''Google image search (returns any of the first 4 results)'''
        
    url = 'https://ajax.googleapis.com/ajax/services/search/images?v=1.0&q=%s&safe=off'

    #Searches are returned as JSON so we need to turn that into a dictionary
    query = json.loads( urlopen( url % quote_plus( msg ) ).read().decode('UTF-8') )
    if query['responseStatus'] != 200:
        return query['responseStatus']

    #Then break it down to only the data we need
    #in this case it's any of the first 4 image results
    query = query['responseData']['results'][randint(0,3)]['url']

    return unquote_plus( query, encoding='utf-8', errors='replace' )
