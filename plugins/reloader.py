from plugins import event, mod
from plugins import modules
from imp import reload as reload_module
from sys import getrefcount
from collections import defaultdict

hook = mod.hook
auth = mod.auth

@event('RELOAD')
def handle_reload(irc):
    pass


@hook.command
@auth.logged_in(['Admin'])
def reload(irc, nick, chan, msg, args, user):
    try:
        # Make sure the module exists first of all.
        if msg not in modules:
            return "The '{}' module doesn't seem to be loaded, so I can't reload it.".format(msg)

        # Get old module and statistics.
        current_mod = modules[msg]['module']
        current_ref = getrefcount(current_mod)

        # Eliminate Old Hook References from Existing Module Dict.
        modules[msg]['hooks'] = defaultdict(list)

        # Perform Reload and get new module statistics.
        reload_mod  = reload_module(current_mod)
        reload_ref  = getrefcount(reload_mod)

        return 'Reloaded {}, Old Refs: {}, New Refs: {}'.format(
            msg,
            current_ref,
            reload_ref
        )

    except Exception as e:
        return str(e)
