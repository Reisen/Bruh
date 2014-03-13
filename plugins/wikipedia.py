"""
	Search and display Wikipedia articles
"""

from plugins.commands import command

from urllib.parse import quote_plus
from urllib.request import urlopen
from re import sub
import json

def wikisearch(msg):
	url = "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={}&srprop=timestamp&format=json"

	query = json.loads(urlopen(url.format(quote_plus(msg)), timeout = 7).read().decode('UTF-8'))
	query = [ x['title'] for x in query['query']['search'][:5] ]

	#removing the [] that surround our titles
	return str(query)[1:-1]


@command
def wikipedia(irc, nick, chan, msg, args):
	'''Search and display wikipedia articles'''
	
	if not msg:
		return "Need something to search for"
	
	
	try:
		command = msg.split(' ', 1)
		
		# because I am too lazy to find a nicer way
		# to avoid errors with split()
		if len(command) > 1:
			msg = command[1]
			command = command[0]
		else:
			command = ''
		commands = { 'search' : lambda: wikisearch(msg) }
		
		if command in commands:
			return commands[command]()
		else:
			msg = command + msg
		
		url = "https://en.wikipedia.org/w/api.php?format=json&action=query&prop=extracts&titles={}&redirects=true"

		text = json.loads(urlopen(url.format(quote_plus(msg)), timeout = 7).read().decode('UTF-8'))

		# one of the keys is just a random number that we can't/won't predict
		# we also need to remove all the html formatting from the text
		key = list(text['query']['pages'])[0]
		text = sub(r'\<.*?>|\n','', text['query']['pages'][key]['extract'])

		return "{}... - https://en.wikipedia.org/wiki/{}".format(text[:120],msg)

	except:
		return "Something went wrong"
