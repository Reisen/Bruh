"""
    This creates a command that will reload other plugins at runtime so that
    the bot does not have to be restarted for each plugin change.
"""

from plugins.commands import command
from plugins.admin import authorized
import imp

@command
def reload(irc, prefix, command, args):
    """
    Reload plugins.
    .reload <plugin>
    """
    if not authorized(args[2]):
        return "Fucking sorting this out later nig"

    if args[1] == '':
        return "Might want to specify what plugin you want to reload."

    if args[1] == 'reload':
        return "Cannot reload myself, sorry"

    try:
        imp.reload(irc.plugins[args[1]])
        return "Reloading: %s" % str(irc.plugins[args[1]])
    except KeyError:
        return "Plugin not found."
