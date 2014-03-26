"""This plugin implements channel joining."""
from time import sleep
from plugins import event

@event('004')
def setup_channels(irc, prefix, command, args):
    # Identify Before Joining any Channels
    if 'identify' in irc.server:
        irc.say('nickserv', 'identify {}'.format(irc.server['identify']))
        sleep(2)

    for channel in irc.server.get('channels', []):
        irc.join(channel)
