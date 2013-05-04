"""This plugins implements channel joining."""

from plugins import event

@event('BRUH')
def setup_channels(irc):
    for channel in irc.config.get('channels', []):
        irc.join(channel)
