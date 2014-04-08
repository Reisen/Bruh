from plugins import event, mod
from plugins import modules
from imp import reload as reload_module
from sys import getrefcount
from collections import defaultdict

hook = mod.hook

@event('RELOAD')
def handle_reload(irc):
    pass


@hook.command
def reload(irc, nick, chan, msg, args):
    # Get old module and statistics.
    current_mod = modules[msg]['module']
    current_ref = getrefcount(current_mod)

    # Eliminate Old Hook References from Existing Module Dict.
    modules[msg]['hooks'] = defaultdict(list)

    # Perform Reload and get new module statistics.
    reload_mod  = reload_module(current_mod)
    reload_ref  = getrefcount(reload_mod)

    return 'Reloaded {}, Old Refs: {}, New Refs: {}, ID: {} -> {}'.format(
        msg,
        current_ref,
        reload_ref,
        id(current_mod),
        id(reload_mod)
    )
