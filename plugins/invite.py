"""
    This creates a single event handler that will allow the bot to respond
    to invite requests by joining the channel automatically
"""
from time import time
from plugins import event
from collections import defaultdict

# If the bot has recently joined a channel, and then re-invited too quickly,
# then the bot has likely been kicked almost instantly. Recently I watched a
# group of users get the bot Killed from the network by repeatedly inviting and
# kicking the bot, putting a delay on joining should curb this.
#
# The below dictionary stores the last time an invite to a channel was made, it
# will only join if that was > 10 minutes.
join_tracker = defaultdict(lambda: 0)

@event('INVITE')
def invite(irc, prefix, command, args):
    # Make sure the channel we're being asked to join is not blacklisted in the
    # config file.
    if 'invite' in irc.core['config']['plugins']:
        if args[1] in irc.core['config']['plugins']['invite'].get('ignore', []):
            return

        # Only join if time since last join was 10 minutes.
        if time() - join_tracker[args[1]] > 600:
            join_tracker[args[1]] = time()
            irc.join(args[1])
        else:
            inviter = prefix.split('!')[0]
            irc.say(inviter, 'I was already recently invited to {}. I assume I have been kicked, I will not respond to invites for another 10 minutes to prevent rejoin spam.'.format(args[1]))
