"""
    A plugin for searching youtube, and printing information about Youtube
    links sent to the channel.
"""
import re
from json import loads
from urllib.error import URLError
from urllib.request import urlopen
from urllib.parse import quote_plus
from bruh import command, regex, r
from plugins import stats
from walnut.drivers import Walnut

def calculate_length(length):
    pieces = re.findall(r'\d+[DHMS]', length)
    pieces = map(str.lower, pieces)
    return ' '.join(pieces)


def fetch_video(query):
    # https://developers.google.com/youtube/v3/docs/videos/list
    ytapi = r.get('keys:youtube').decode('UTF-8')
    query = quote_plus(query)
    video = urlopen('https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics,contentDetails&key={}&id={}'.format(ytapi, query), timeout = 7)
    video = loads(video.read().decode('utf-8'))

    # Pull out all the information we actually care about showing.
    video = video['items'][0]
    likes = int(video['statistics'].get('likeCount', 0))
    dislikes = int(video['statistics'].get('dislikeCount', 0))

    return '\x02{}\x02 - length \x02{}\x02 - liked by \x02{:.2f}%\x02 ({}/{}) - \x02{}\x02 views - {} {}'.format(
        video['snippet']['title'],
        calculate_length(video['contentDetails']['duration']),
        100 * likes / (likes + dislikes),
        likes,
        likes + dislikes,
        video['statistics'].get('viewCount', 0),
        video['snippet']['channelTitle'],
        '(https://www.youtube.com/watch?v={})'.format(video['id'])
    )


def search_video(query):
    # https://developers.google.com/youtube/v3/docs/search/list
    ytapi = r.get('keys:youtube').decode('UTF-8')
    query = quote_plus(query)
    video = urlopen('https://www.googleapis.com/youtube/v3/search?part=id&type=video&key={}&q={}'.format(ytapi, query), timeout = 7)
    video = loads(video.read().decode('utf-8'))
    return video['items'][0]['id']['videoId']


@regex(r'(?:youtube\..*?\?.*?v=|youtu\.be/)([-_a-zA-Z0-9]+)')
def youtube_match(irc, match):
    stats.incr('youtube', 1, irc.network, irc.channel, irc.nick)
    return fetch_video(match.group(1))


@command('youtube')
@command('yt')
@command('y')
def youtube(irc):
    if not irc.message:
        return None

    return fetch_video(search_video(irc.message))
