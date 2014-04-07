"""
    A plugin for searching youtube, and printing information about Youtube
    links sent to the channel.
"""
from json import loads
from urllib.error import URLError
from urllib.request import urlopen
from urllib.parse import quote_plus
from plugins import event, mod

commands = mod.commands

def setup_db(irc):
    irc.db.execute('''
        CREATE TABLE IF NOT EXISTS youtube_optout (
            channel TEXT,
            status INTEGER DEFAULT 1,
            PRIMARY KEY(channel)
        );
    ''')


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


@commands.regex(r'(?:youtube\..*?\?.*?v=([-_a-zA-Z0-9]+))')
def youtube_match(irc, nick, chan, match, args):
    setup_db(irc)
    try:
        status = irc.db.execute('SELECT status FROM youtube_optout WHERE channel = ?', (chan,)).fetchone()
        if status is None or status[0] != 0:
            return fetch_video(match.group(1))

    except Exception as e:
        # No row for records just means opt-in by default I guess.
        return fetch_video(match.group(1))


def youtube_toggle(irc, chan, status):
    setup_db(irc)
    irc.db.execute('INSERT OR REPLACE INTO youtube_optout (channel, status) VALUES (?, ?)', (chan, int(status)))
    irc.db.commit()
    return 'Auto-Youtube Information: {}'.format(status)


@commands.command
def youtube(irc, nick, chan, msg, args):
    """
    Search youtube, because you're too lazy to open your browser.
    .youtube <search terms>
    .youtube off - Turn off automatic youtube data.
    .youtube on  - Turn automatic youtube data back on.
    """
    if not msg:
        return "Syntax: .youtube <search terms>"

    command, *args = msg.split(' ', 1)
    try:
        commands = {
            'on':  lambda: youtube_toggle(irc, chan, True),
            'off': lambda: youtube_toggle(irc, chan, False),
        }
        return commands[command]()

    except KeyError:
        return fetch_video(msg, True)
