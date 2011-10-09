"""
    This plugin starts a new thread that will handle timers. Timers are simly
    lightweight counters that count down minutes (no second based timers).
"""
from plugins.commands import command
from plugins.database import *
from plugins.bruh import event
import threading, time, datetime
import re

class TimeGod(threading.Thread):
    """God of time, will kill you whenever it feels like it."""
    def __init__(self, irc):
        threading.Thread.__init__(self)

        # Timers are stored in a dict, the keys are the number of seconds
        # until the event occurs, the values are lists of messages to be
        # sent.
        self.irc = irc
        self.timers = {}
        self.unstoppable = True

    def stop(self):
        self.unstoppable = False

    def run(self):
        while self.unstoppable:
            time.sleep(10)

            # First we print all values stored in 0, as these timers
            # have expired.
            if 0 in self.timers.keys():
                for message in self.timers[0]:
                    # Messages are stored as (channel, message) tuples, say
                    # accepts arguments in this order.
                    self.irc.say(*message)

                # Delete key 0 so it doesn't move into negatives.
                del self.timers[0]

            # Now, we shift all messages down 10 seconds.
            for key in sorted(self.timers):
                self.timers[key - 10] = self.timers[key]
                del self.timers[key]


timegods = {}

@event('BRUH')
def setup_timers(irc):
    """Sets up the timer thread."""
    # Each server has its own timegod, master of time, slaughterer of children.
    timegod = TimeGod(irc)
    timegod.start()
    timegods[irc.server] = timegod


@event('GETOUT')
def shutdown_timers():
    print('Timers: Shutting down timer threads.')
    for timegod in timegods.values():
        timegod.stop()


@command
def timer(irc, nick, chan, msg, args):
    """
    Add a timer to bruh, timers are in multiples of 5 seconds.
    .timer <length> <message>
    .timer 2h5s This will be sent in 2 hours and 5 seconds.
    """
    timegod = timegods[irc.server]
    if len(msg) == 0:
        return "There are {:d} active timers".format(len(timegod.timers.keys()))

    # Find out the kind of time being parsed.
    if ':' in msg:
        try:
            # This kind of time is a full timestamp, I.E 03/04/2011 11:30
            pieces = msg.split(' ', 2)
            if len(pieces) < 3:
                return "Not enough arguments asshole."

            # Reconstruct the list so It's the same as if we weren't receiving a timestamp.
            pieces = [" ".join(pieces[:2]), pieces[2]]
            print(pieces)

            expiration = datetime.datetime.strptime(pieces[0], '%d/%m/%Y %H:%M:%S')
            seconds = int(time.mktime(expiration.timetuple())) - int(time.mktime(datetime.datetime.now().timetuple()))

        except ValueError:
            return "That's not a proper date you idiot."

        except OverflowError:
            return "What kind of date are you trying to give me, jesus."

    else:
        # Round timer to nearest multiple of 10
        try:
            pieces = msg.split(' ', 1)
            days, hours, minutes, seconds = re.match(r'(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?', msg.split(' ', 1)[0]).groups()
            days    = int(days) * 86400 if days else 0
            hours   = int(hours) * 3600 if hours else 0
            minutes = int(minutes) * 60 if minutes else 0
            seconds = int(seconds) if seconds else 0
            seconds = seconds + minutes + hours + days
            seconds = int(10 * round(float(seconds)/10))

            expiration = datetime.datetime.now() + datetime.timedelta(seconds = seconds)

        except OverflowError:
            return "What kind of date are you trying to give me, jesus."

    if seconds not in timegod.timers:
        timegod.timers[seconds] = []

    timegod.timers[seconds].append((chan, pieces[1]))
    return "Timer set to go off at {}, {:d} seconds from now.".format(expiration.strftime('%b %d %Y, %H:%M:%S'), seconds)
