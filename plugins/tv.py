"""
    This plugin allows users in a channel to register for certain TV shows. The
    plugin will announce to the channel when those shows are airing.
"""
import re
import time
import urllib.request
import html.entities
from json import loads
from plugins import event
from urllib.error import URLError
from plugins.commands import command
from xml.dom.minidom import parseString

API_KEY = "469B73127CA0C411"

class TVSubscription(object):
    """
    This object represents a TV subscription. Bruh will check periodically to
    see when this episode is airing.
    """
    id      = Integer(primary_key = True)
    channel = String()
    series  = String()
    date    = String()

    def __init__(self, channel = None, series = None, date = None):
        if channel is None:
            return

        self.channel = channel
        self.series = series
        self.date = date


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


def when(irc, channel, show):
    # Get the current time, we want to find the next episode airing after this
    # date.
    now = time.strftime('%d %m %y', time.gmtime(time.time()))
    now = list(map(int, now.split(' ')))
    now.reverse()
    print(now)

    results = urllib.request.urlopen("http://www.thetvdb.com/api/GetSeries.php?seriesname={}".format(show.replace(' ', '+')))
    results = parseString(results.read())
    series  = results.childNodes[0].getElementsByTagName('Series')

    # We always return the first result, which hopefully is the closest to what
    # the user searched.
    if len(series) > 0:
        series = series[0]
        showid = series.getElementsByTagName('seriesid')[0].firstChild.toxml()
        title = series.getElementsByTagName('SeriesName')[0].firstChild.toxml()

    else:
        return "Didn't find anything for that series."

    # Parse dates out of that page.
    results = urllib.request.urlopen("http://thetvdb.com/?tab=seasonall&id={}&lid=7".format(showid)).read()
    dates   = re.findall(r'td class.+?>(\d{4}-\d{2}-\d{2})<', results.decode('UTF-8'))

    # For each date in the page, we search to find a date that's in the future
    # from us.
    for tvdate in dates:
        # Do a hacky date parse to get our date into numbers, pretty horrible.
        date = time.strftime('%d %m %y', time.strptime(tvdate, '%Y-%m-%d'))
        dateOutput = time.strftime('%d %B, %Y', time.strptime(tvdate, '%Y-%m-%d'))
        date = list(map(int, date.split(' ')))
        date.reverse()

        # Lets see if It's airing today.
        if now == date:
            return "That show is airing today."

        # If today is less than the date, then that date is in the future. Lets
        # print this to the channel.
        if now < date:
            # See if the show is already being tracked.
            show = irc.db.query(TVSubscription).where(TVSubscription.channel == channel) \
                                               .where(TVSubscription.series == title).one()

            if show is None:
                show = TVSubscription(channel, title, dateOutput)
                irc.db.add(show)

            return "Next episode of {} will air on {}, I'll remind you when it airs.".format(title, dateOutput)

    return "No idea when that's airing, probably never."


@event('BRUH')
def trackTV(irc):
    """Start tracking TV air dates."""
    irc.db.map(TVSubscription)

    # Setup timed callback to check when episodes are airing. Should check every hour.
    def checkTV():
        print('Checking TV Series.')
        series = irc.db.query(TVSubscription).all()
        now    = time.strftime('%d %B, %Y', time.gmtime(time.time()))

        for s in series:
            print('Checking {}.'.format(s.series))
            print('Now is: {}'.format(now))
            print('Series airs: {}'.format(s.date))
            if s.date == now:
                irc.say(s.channel, "{} is going to air today.".format(s.series))

    # Periodic check to see if a series is airing today.
    dq.insert(checkTV, 3600, True)


@command
def tv(irc, nick, chan, msg, args):
    """
    Register for TV show announcements.
    .tv next <show>
    .tv search <show>
    """
    try:
        command, show = msg.split(' ', 1)

    except ValueError:
        command, show = None, msg

    try:
        commands = {
            'search': lambda: search(show),
            'next': lambda: when(irc, chan, show)
        }
        return commands[command]()

    except KeyError:
        # If the command wasn't found, we'll just look up when something airs
        # as that's the most common use for this plugin.
        return when(irc, chan, msg)
