"""
    Provide a way for users to authenticate themselves with the bot.
"""
from plugins.commands import command

@command
def authenticate(irc, nick, prefix, command, args):
    """
    Authenticate with the bot.
    .authenticate <password>
    .authenticate status
    """
    return 'Hello'
