"""
    This plugin allows users in a channel to register for certain TV shows. The
    plugin will announce to the channel when those shows are airing.
"""

from time import time, mktime, sleep
from datetime import datetime
from plugins import event
from plugins.commands import command
from urllib.error import URLError
from urllib.request import urlopen
from urllib.parse import quote_plus
from xml.dom.minidom import parseString

def setup_db(irc):
    irc.db.execute('''
        CREATE TABLE IF NOT EXISTS shows (
            id INTEGER PRIMARY KEY,
            name TEXT,              -- Pretty name for the show.
            show_id INTEGER,        -- TV Rage ID for the show.
            airs INTEGER,           -- UNIX timestamp for show air-date.
            announce INTEGER,       -- Track announced status.
            title TEXT              -- Title of the next episode to air.
        );
    ''')
    irc.db.execute('''
        CREATE TABLE IF NOT EXISTS show_channels (
            show_id INTEGER,        -- Show ID this channel is tracking.
            channel TEXT,           -- The channel name.
            PRIMARY KEY (show_id, channel)
        );
    ''')
    irc.db.commit()


def RAGE(irc, show_id):
    """Fetch TVRage information about a series."""
    detail = 'http://services.tvrage.com/feeds/showinfo.php?sid={}'.format(show_id)
    detail = parseString(urlopen(detail).read())

    # Make sure the show is still airing, otherwise the rest of this function
    # is entirely purposeless.
    airstate = detail.getElementsByTagName('status')[0].firstChild.toxml()
    if 'Returning' not in airstate:
        raise ValueError

    episodes = 'http://services.tvrage.com/feeds/episode_list.php?sid={}'.format(show_id)
    episodes = parseString(urlopen(episodes).read())

    # Build a dictionary containing important information about the series.
    show_info = {}
    for item in ['showid', 'showname', 'seasons', 'started', 'airtime']:
        show_info[item] = detail.getElementsByTagName(item)[0].firstChild.toxml()

    show_info['episodes'] = []
    for episode in episodes.getElementsByTagName('episode'):
        episode_info = {}
        for item in ['epnum', 'seasonnum', 'airdate', 'title']:
            # Some episodes might not actually have some data, we'll just fail
            # cleanly and code that uses this data can deal with the
            # consequences of not having some type of information.
            try:    episode_info[item] = episode.getElementsByTagName(item)[0].firstChild.toxml()
            except: episode_info[item] = None

        # Provide a UNIX timestamp for the air date/time as well. TV Rage
        # returns dates literally as 00:00:00 for some reason for some
        # episodes, so we have to expect strptime to fail.
        try:
            timestamp = datetime.strptime('{} {}'.format(show_info['airtime'], episode_info['airdate']), '%H:%M %Y-%m-%d')
            timestamp = mktime(timestamp.timetuple())
            episode_info['timestamp'] = timestamp
        except:
            continue

        show_info['episodes'].append(episode_info)

    return show_info


def find(irc, show_name):
    """Fetch TVRage matches on a show name, and return the ID."""
    search = 'http://services.tvrage.com/feeds/search.php?show={}'.format(quote_plus(show_name))
    try:
        search = parseString(urlopen(search).read()).getElementsByTagName('show')[0]

        # Fetch relevant information about the series, including the ID.
        show_id = search.getElementsByTagName('showid')[0].firstChild.toxml()
        show_title = search.getElementsByTagName('name')[0].firstChild.toxml()
        show_date = search.getElementsByTagName('started')[0].firstChild.toxml()

        return '{} ({}) - ID: {}'.format(show_title, show_date, show_id)
    except:
        return 'There was an error finding information about that series.'


def add_tv(irc, chan, show_id):
    """Track a TV show for a channel."""
    show = irc.db.execute('SELECT * FROM shows WHERE show_id = ?', (show_id,)).fetchone()

    try:
        # If the show doesn't already exist in the database, fetch it from TV Rage
        # and add it to the database.
        if not show:
            show = RAGE(irc, show_id)
            irc.db.execute('INSERT OR REPLACE INTO shows (name, show_id, airs, announce, title) VALUES (?, ?, ?, ?, ?)', (
                '{} ({})'.format(show['showname'], show['started']),
                show['showid'],
                0,
                0,
                'Unknown'
            ))
            show = irc.db.execute('SELECT * FROM shows WHERE show_id = ?', (show_id,)).fetchone()

        irc.db.execute('INSERT INTO show_channels (show_id, channel) VALUES (?, ?)', (show_id, chan))
        irc.db.commit()
        return 'Now tracking show: {}'.format(show[1])
    except ValueError as e:
        raise e
        return 'That show has finished airing, you can\'t track it.'
    except:
        return 'You are already tracking {} in this channel.'.format(show[1])


LAST_CHECK = time()

@event('PING')
def announce(irc, prefix, command, args):
    """Announce series that are airing soon to the channel."""
    global LAST_CHECK
    setup_db(irc)

    # For each show, we need to make sure we have the right air date. Otherwise
    # we're tracking pointless information.
    for show in irc.db.execute('SELECT * FROM shows').fetchall():
        # If the timestamp is in the past, then the episode we WERE tracking
        # has already aired and we need to get the next episode.
        now, timestamp = time(), int(show[3])
        if timestamp - now <= 0 and (now - LAST_CHECK > 7200 or prefix == None):
            # Update check so we don't spam the API too much. Once every two
            # hours is enough.
            LAST_CHECK = time()

            # Fetch TV RAGE show information.
            try:
                details = RAGE(irc, show[2])

                # Update the time in the database to the next upcoming episode.
                next_episode = details['episodes'][-1]
                for episode in reversed(details['episodes']):
                    if (episode['timestamp'] > now and episode['timestamp'] < next_episode['timestamp']) or next_episode['timestamp'] < now:
                        next_episode = episode

                irc.db.execute('UPDATE shows SET airs = ?, title = ?, announce = 0 WHERE id = ?', (next_episode['timestamp'], next_episode['title'], show[0]))
                irc.db.commit()
            except ValueError:
                # ValueError should occur when a TV series is no longer
                # returning so we should just remove it from the database.
                irc.db.execute('DELETE FROM shows WHERE show_id = ?', (show[2],))
                irc.db.commit()

        # Now that we're sure we have the right air-date, we just need to find
        # out if we're close enough to mention that to any channels who care
        # about it.
        airs, *details = irc.db.execute('SELECT airs FROM shows WHERE show_id = ?', (show[2],)).fetchone()
        if show[4] == 0 and 0 < int(airs) - now < 3600:
            # Fetch channels and update the announce field so we don't spam
            # channels with announcements every 10 minutes.
            irc.db.execute('UPDATE shows SET announce = 1 WHERE id = ?', (show[0],))
            channels = irc.db.execute('SELECT * FROM show_channels WHERE show_id = ?', (show[2],)).fetchall()

            # Finally, lets tell people their show is airing soon.
            for channel in channels:
                irc.say(channel[1], 'The next episode of {}, "{}" will be airing in a few hours.'.format(show[1], show[5]))


def list_tv(irc, chan, nick):
    """List currently tracked TV series."""
    announce(irc, None, None, None)
    shows = irc.db.execute('SELECT shows.*, show_channels.* FROM show_channels JOIN shows ON shows.show_id = show_channels.show_id WHERE channel = ?', (chan,)).fetchall()
    for show in shows:
        time_until = int((show[3] - time()) / 86400)
        if len(shows) > 3:
            if time_until < 0: irc.notice(nick, 'No upcoming episodes of {} have been announced.'.format(show[1]))
            else:              irc.notice(nick, 'The next episode of {}, "{}", airs in {} days.'.format(show[1], show[5], time_until))
        else:
            if time_until < 0: irc.reply('No upcoming episodes of {} have been announced.'.format(show[1]))
            else:              irc.reply('The next episode of {}, "{}", airs in {} days.'.format(show[1], show[5], time_until))

        sleep(0.4)


@command
def tv(irc, nick, chan, msg, args):
    """Channel alerts about TV series."""
    setup_db(irc)

    command, *args = msg.split(' ', 1)
    try:
        commands = {
            'add':    lambda: add_tv(irc, chan, *args),
            'find':   lambda: find(irc, *args),
            'force':  lambda: announce(irc, None, None, None),
            'list':   lambda: list_tv(irc, chan, nick)
        }
        return commands[command]()
    except KeyError:
        return list_tv(irc, chan, nick)
