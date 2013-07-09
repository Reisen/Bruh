"""
    A plugin for querying the Reddit API. Can automatically parse reddit URL's
    linked and print them to channels.
"""
import re
from json import loads
from urllib.error import URLError
from urllib.request import urlopen
from plugins.commands import regex
from plugins.youtube import fetch_video

@regex(r'reddit\.com/r/([^/]+)/comments/([\w]+)')
def reddit_match(irc, nick, chan, match, args):
    listing = urlopen('http://reddit.com/r/{}/duplicates/{}.json'.format(match.group(1), match.group(2)))
    listing = loads(listing.read().decode('utf-8'))
    listing = listing[0]['data']['children'][0]['data']

    # Parse Youtube URL's out of Reddit Links.
    youtube_check = re.search(r'(?:youtube\..*?\?.*?v=([-_a-zA-Z0-9]+))', listing['url'])
    if youtube_check:
        return fetch_video(youtube_check.group(1), True)
