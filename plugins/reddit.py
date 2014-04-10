"""
    A plugin for querying the Reddit API. Can automatically parse reddit URL's
    linked and print them to channels.
"""
import re
from json import loads
from urllib.error import URLError
from urllib.request import urlopen
from plugins import mod

hook = mod.hook

@hook.regex(r'reddit\.com/r/([^/]+)/comments/([\w]+)')
def reddit_match(irc, nick, chan, match, args):
    # Only bother doing the request if the Youtube plugin exists. Otherwise
    # this whole function is a no-op.
    if 'youtube' in irc.plugins:
        try:
            listing = urlopen('http://reddit.com/r/{}/duplicates/{}.json'.format(match.group(1), match.group(2)), timeout = 7)
            listing = loads(listing.read().decode('utf-8'))
            listing = listing[0]['data']['children'][0]['data']

            # Parse Youtube URL's out of Reddit Links.
            youtube_check = re.search(r'(?:youtube\..*?\?.*?v=([-_a-zA-Z0-9]+))', listing['url'])
            if youtube_check:
                return irc.plugins['youtube'].fetch_video(youtube_check.group(1), True)

        except Exception as e:
            pass
