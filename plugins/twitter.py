"""
  Retreives requested users latest tweet.
"""
from json import loads
from TwitterAPI import TwitterAPI
from plugins import mod

commands = mod.commands

@commands.command
def twitter(irc, nick, chan, msg, args):
    '''
    Retrieves requested users latest tweet.
    .twitter <username>
    '''

    if 'twitter' in irc.config['plugins']:
        consumer_key, consumer_secret, access_token_key, access_token_secret = irc.config['plugins']['twitter']['keys']

    else:
        return "No 'keys' set for twitter API. Check your config."

    if not msg:
        return ".twitter <username>"

    try:
        request = TwitterAPI(consumer_key, consumer_secret, access_token_key, access_token_secret)
        request = request.request('statuses/user_timeline', {'screen_name': msg, 'count': '1'})

        if request.status_code != 200:
            raise Exception("bad status code")

        # Removing the first and last characters because they are '[' and ']'
        request = loads(request.text[1:-1])
        return "{}  -  https://twitter.com/{}/status/{}".format(
            request['text'],
            request['user']['screen_name'],
            request['id']
        )

    except Exception as e:
        return "There was an error in this module."
