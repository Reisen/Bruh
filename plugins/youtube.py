"""
    A plugin for searching youtube, and printing information about Youtube
    links sent to the channel.
"""
from json import loads
from urllib.error import URLError
from urllib.request import urlopen
from urllib.parse import quote_plus
from plugins.commands import command, regex

def calculate_length(seconds):
    timestring = ''
    if seconds // 3600: timestring += '{}h '.format(seconds // 3600)
    if seconds // 60:   timestring += '{}m '.format(seconds // 60)
    return timestring + '{}s'.format(seconds % 60)


def fetch_video(query, search = False):
    # Fetch the first results Video information from the Youtube API. Details
    # on the response can be found here on the Youtube API reference:
    # https://developers.google.com/youtube/2.0/reference#Searching_for_videos
    query = quote_plus(query)
    query = '?q=' + query + '&' if search else query + '?'
    video = urlopen('https://gdata.youtube.com/feeds/api/videos/{}v=2&alt=jsonc'.format(query))
    video = loads(video.read().decode('utf-8'))
    print(video)

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
        '(https://www.youtube.com/watch?v={})'.format(video['id']) if not search else ''
    )
    

@regex(r'(?:youtube\..*?\?.*?v=([-_a-zA-Z0-9]+))')
def youtube_match(irc, nick, chan, match, args):
    print('Youtube matcher')
    return fetch_video(match.group(1))


@command
def youtube(irc, nick, chan, msg, args):
    """
    Search youtube, because you're too lazy to open your browser.
    .youtube <query>
    """
    if not msg:
        return 'Need something to search for.'

    return fetch_video(msg, True)
