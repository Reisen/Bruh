"""This plugins implements channel joining."""
from time import sleep
from plugins import event

@event('004')
def setup_channels(irc, prefix, command, args):
    print(irc.config)
    if 'identify' in irc.config:
        irc.say('nickserv', 'identify {}'.format(irc.config['identify']))
        sleep(2)

    for channel in irc.config.get('channels', []):
        irc.join(channel)
