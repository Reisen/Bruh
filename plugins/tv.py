"""
    This plugin allows users in a channel to register for certain TV shows. The
    plugin will announce to the channel when those shows are airing.
"""
import re
import sys
import time
from plugins import event
from datetime import datetime
from urllib.error import URLError
from urllib.request import urlopen
from urllib.parse import quote_plus
from collections import defaultdict
from plugins.commands import command
from xml.dom.minidom import parseString

ACTIVITY = defaultdict(lambda: 0)
API_KEY = "469B73127CA0C411"
LAST_CH = 0
LAST_ID = 0
SHOW_DB = defaultdict(lambda: defaultdict(lambda: []))

def setup_db(irc):
    irc.db.execute('''
        CREATE TABLE IF NOT EXISTS shows (
            id INTEGER PRIMARY KEY,
            show_id INTEGER,
            channel TEXT
        );
    ''')
    irc.db.commit()


def find(args):
    """Search for a TV show by name."""
    global LAST_ID

    # Fetch listings of possible matching TV shows.
    target = 'http://services.tvrage.com/feeds/search.php?show={}'.format(quote_plus(args[0]))
    listing = urlopen(target).read()
    listing = parseString(listing)
    top_show = listing.getElementsByTagName('show')[0]

    # Helper method for pulling information out of the XML.
    def prop(name):
        return top_show.getElementsByTagName(name)[0].firstChild.toxml()

    # Update the LAST_ID constant so future commands can use it, if other
    # commands aren't given an ID to work with, LAST_ID is used.
    LAST_ID = prop('showid')
    return "Found show {} (ID: {})".format(prop('name'), prop('showid'))


def refresh(irc):
    """
    Do a full refresh on all shows in the database from TV Rage. Episode
    release dates are reloaded and any new shows are loaded for the first time.
    """
    setup_db(irc)

    global LAST_CH, SHOW_DB

    # Re-check listings and air-times once a day. This doesn't happen often, so
    # it doesn't hurt to rate limit the requests slightly so as not to hammer
    # the API unnecessarily (don't know what exactly would count as spam to TV
    # Rage).
    if time.time() - LAST_CH > 1 * 24 * 60 * 60:
        # Reset SHOW_DB to start fresh.
        LAST_CH = time.time()
        SHOW_DB = defaultdict(lambda: defaultdict(lambda: []))

        shows = irc.db.execute('SELECT * FROM shows').fetchall()
        for id, show_id, channel in shows:
            update = show_id in SHOW_DB
            SHOW_DB[show_id]['channels'].append(channel)

            # Skip if we've already re-populated this shows database.
            if update:
                continue

            # Find the next episode that airs, and when. Timezone handling is
            # pretty shitty so forget that for now, same day is good enough.
            target = 'http://services.tvrage.com/feeds/episode_list.php?sid={}'.format(show_id)
            episodes = urlopen(target).read()
            episodes = parseString(episodes)

            # Save show Name.
            SHOW_DB[show_id]['name'] = episodes.getElementsByTagName('name')[0].firstChild.toxml()

            # Find next episode that airs.
            episodes = episodes.getElementsByTagName('episode')
            SHOW_DB[show_id]['episode'] = episodes[0]

            for episode in episodes:
                airdate = episode.getElementsByTagName('airdate')[0].firstChild.toxml()
                airdate = time.mktime(datetime.strptime(airdate, '%Y-%m-%d').timetuple())
                episode.airdate = airdate

                # Update the air time for this show, but only if it is closer to the
                # current date than what's already there.
                current_airdate = SHOW_DB[show_id]['episode'].getElementsByTagName('airdate')[0].firstChild.toxml()
                current_airdate = time.mktime(datetime.strptime(current_airdate, '%Y-%m-%d').timetuple())

                # Store timestamp as well, just for ease of use in other functions.
                SHOW_DB[show_id]['episode'].airdate = current_airdate
                if airdate > time.time() and (airdate < current_airdate or current_airdate < time.time()):
                    SHOW_DB[show_id]['episode'] = episode

    # Spawn messages to be sent into IRC channels.
    messages = []
    for show in SHOW_DB:
        show = SHOW_DB[show]

        # Alert the relevent channels tracking this show.
        for channel in show['channels']:
            title = show['episode'].getElementsByTagName('title')[0].firstChild.toxml()
            if time.time() - show['episode'].airdate > 0 and ACTIVITY[channel] < 600 and 'announced' not in show:
                message = 'Next episode of {}, "{}", airs today.'.format(show['name'], title)
                messages.append((channel, message))
                show['announced'] = True

    return messages


def add_tv(irc, args, chan):
    """Add a TV show to be tracked by a channel."""
    setup_db(irc)

    global LAST_ID
    if args:
        LAST_ID = args[0]

    # Check the show isn't already being tracked by this channel.
    show = irc.db.execute('SELECT * FROM shows WHERE show_id=? AND channel=?', (LAST_ID, chan)).fetchone()
    if show:
        return "Already tracking this show."

    # Add unknown shows to the database.
    irc.db.execute('INSERT INTO shows (show_id, channel) VALUES (?, ?)', (LAST_ID, chan))
    irc.db.commit()

    return "Show added to tracker: " + str(LAST_ID)


def remove_tv(irc, args, chan):
    """Remove a TV show to be tracked by a channel."""
    return "Show removed from tracker: " + str(args)


def list_tv(irc, chan):
    """Returns a list of TV shows the bot is tracking for a channel."""
    setup_db(irc)
    shows = irc.db.execute('SELECT * FROM shows WHERE channel=?', (chan,)).fetchall()
    output = "Currently Tracking: "

    # Force an update if there hasn't been one.
    refresh(irc)

    # Find shows for this channel.
    for show in SHOW_DB:
        show = SHOW_DB[show]
        if chan in show['channels']:
            title = show['episode'].getElementsByTagName('title')[0].firstChild.toxml()
            days = int((show['episode'].airdate - time.time()) // (24 * 60 * 60))
            irc.reply('{}, next in {} days'.format(show['name'], days))
            time.sleep(0.1)

    return None


@event('PING')
def check_dates(irc, prefix, command, args):
    """
    Every time the server pings, do a quick check to see if any shows are
    coming up to air, and announce them if they are.
    """
    # Find information about upcoming episode alerts.
    setup_db(irc)
    messages = refresh(irc)

    # Send any alerts to channels that care about them.
    for channel, message in messages:
        irc.say(channel, message)
        time.sleep(0.1)


@event('PRIVMSG')
def monitor_activity(irc, prefix, command, args):
    """Monitor activity, the bot should only alert in channels where people are actually online."""
    chan = args[0]
    if chan.startswith('#'):
        ACTIVITY[chan] = time.time()


@command
def tv(irc, nick, chan, msg, args):
    """Alerts about TV series."""
    setup_db(irc)

    # Parse arguments from the command.
    command, *args = msg.split(' ', 1)
    try:
        commands = {
            'find':   lambda: find(args),
            'add':    lambda: add_tv(irc, args, chan),
            'remove': lambda: remove_tv(irc, args, chan),
            'list':   lambda: list_tv(irc, chan)
        }
        return commands[command]()
    except KeyError:
        if not args:
            return list_tv(irc, chan)

        return find([msg])
    except:
        return str(sys.exc_info())
