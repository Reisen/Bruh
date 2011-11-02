"""
    This plugin allows users in a channel to register for certain TV shows. The
    plugin will announce to the channel when those shows are airing.
"""
from plugins.commands import command
from plugins.bruh import event
from plugins.database import *
from urllib.error import URLError
from xml.dom.minidom import parseString
import urllib.request
import re
import html.entities

API_KEY = "469B73127CA0C411"

# Function taken from http://effbot.org/zone/re-sub.htm#unescape-html
def unescape(text):
    def fixup(m):
        text = m.group(0)
        
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return chr(int(text[3:-1], 16))

                else:
                    return chr(int(text[2:-1]))

            except ValueError:
                pass
        else:
            # named entity
            try:
                text = chr(html.entities.name2codepoint[text[1:-1]])

            except KeyError:
                pass

        return text # leave as is

    return re.sub("&#?\w+;", fixup, text)


def search(show):
    results = urllib.request.urlopen("http://www.thetvdb.com/api/GetSeries.php?seriesname={}".format(show.replace(' ', '+')))
    results = parseString(results.read())
    series  = results.childNodes[0].getElementsByTagName('Series')

    # We always return the first result, which hopefully is the closest to what
    # the user searched.
    if len(series) > 0:
        series = series[0]
        title = series.getElementsByTagName('SeriesName')[0].firstChild.toxml()
        overview = series.getElementsByTagName('Overview')[0].firstChild.toxml()
        return unescape("{} - {}".format(title, overview))

    return "No series found."


class TVSubscription(object):
    """
    This object represents a TV subscription. Bruh will check periodically to
    see when this episode is airing.
    """
    id      = Integer(primary_key = True)
    channel = String()
    series  = String()

    def __init__(self, channel, series):
        self.channel = channel
        self.series = series


@event('BRUH')
def trackTV(irc):
    """Start tracking TV air dates."""
    irc.db.map(TVSubscription)


@command
def tv(irc, nick, chan, msg, args):
    """
    Register for TV show announcements.
    .tv subscribe <show>
    .tv unsubscribe <show>
    .tv search <show>
    """
    try:
        command, show = msg.split(' ', 1)

    except ValueError:
        return "Missing argument."

    try:
        commands = {
            'search': lambda: search(show),
            'register': lambda: search(show)
        }
        return commands[command]()

    except KeyError:
        return "Command not found."
