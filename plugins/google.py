"""
    Search google for some useless shit no one cares about
"""
from plugins.commands import command

from urllib.parse import quote_plus
from urllib.request import urlopen
import json

@command
def google(irc, nick, chan, msg, args):
    '''Google web search'''
    
    url = 'https://ajax.googleapis.com/ajax/services/search/web?v=1.0&q=%s'

    #Searches are returned as JSON so we need to turn that into a dictionary 
    query = json.loads( urlopen( url % quote_plus( msg ) ).read().decode('UTF-8') )
    if query['responseStatus'] != 200:
        return query['responseStatus']

    #Then break it down to only the data we need (which is the first result of our search)
    query = query['responseData']['results'][0]
    
    out = '%s -- \x02%s\x02: "%s"' % ( query['url'], query['title'], query['content'] )
    return out
