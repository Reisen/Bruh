"""
    A plugin for searching youtube, and printing information about Youtube
    links sent to the channel.
"""
import re
from json import loads
from urllib.error import URLError
from urllib.request import urlopen
from urllib.parse import quote_plus
from bruh import command
from plugins import stats
from drivers.walnut import Walnut


def calculate_length(seconds):
    timestring = ''

    # Length in Hours
    if seconds // 3600:
        timestring += '{}h '.format(seconds // 3600)

    # Minutes?
    if 0 != (seconds // 60) % 60:
        timestring += '{}m '.format((seconds // 60) % 60)

    # Append seconds always.
    return timestring + '{}s'.format(seconds % 60)


def fetch_video(query, search = False):
    # Fetch the first results Video information from the Youtube API. Details
    # on the response can be found here on the Youtube API reference:
    # https://developers.google.com/youtube/2.0/reference#Searching_for_videos
    query = quote_plus(query)
    query = '?q=' + query + '&' if search else query + '?'
    video = urlopen('https://gdata.youtube.com/feeds/api/videos/{}v=2&alt=jsonc'.format(query), timeout = 7)
    video = loads(video.read().decode('utf-8'))

    # Pull out all the information we actually care about showing.
    video = video['data']
    if 'items' in video:
        video = video['items'][0]

    return '\x02{}\x02 - length \x02{}\x02 - rated \x02{:.2f}/5.00\x02 ({}/{}) - \x02{}\x02 views - {} {}'.format(
        video['title'],
        calculate_length(video['duration']),
        video.get('rating', 0),
        video.get('likeCount', 0),
        video.get('ratingCount', 0),
        video.get('viewCount', 0),
        video['uploader'],
        '(https://www.youtube.com/watch?v={})'.format(video['id']) if search else ''
    )


@Walnut.hook('PRIVMSG')
def youtube_match(message):
    network = message.parent.frm
    channel = message.args[0]
    nick    = message.prefix.split('!')[0]
    match   = re.search(r'(?:youtube\..*?\?.*?v=([-_a-zA-Z0-9]+))', message.args[-1])

    if not match:
        return None

    stats.incr('youtube', 1, network, channel, nick)
    return 'PRIVMSG {} :{}'.format(
        channel,
        fetch_video(match.group(1))
    )


@command('youtube')
@command('yt')
@command('y')
def youtube(irc):
    if not irc.message:
        return "Syntax: .youtube <search terms>"

    return fetch_video(irc.message, True)

