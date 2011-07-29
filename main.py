"""
    This file implements plugin loading, connecting to IRC, and the actual main
    loop for dispatching events to plugins.
"""
import signal
import sys
import os

from bruh.irc import IRC, connectIRC
from plugins import bruh

# Collection of open server connections
servers = []


# Register a Ctrl+C Signal
def quit(signal, frame):
    print('Quitting')
    sys.exit(0)

signal.signal(signal.SIGINT, quit)


if __name__ == '__main__':
    #---------------------------------------------------------------------------
    # Import plugins before any IRC connections are made. This is important
    # because plugins need to be able to handle EVERY message from the server,
    # so they should be ready before connections are made.
    #---------------------------------------------------------------------------

    blacklist = ['__init__.py', 'bruh.py']
    plugins   = {} 

    # The plugins dictionary maps plugin names to python module objects. Here
    # we load module objects directly into the plugins dictionary.
    for plugin in os.listdir('plugins'):
        # Ignore blacklisted files, or files not ending with .py
        if plugin in blacklist or not plugin.endswith('.py'):
            continue

        # __import__ uses pythons dot syntax to import, so remove the .py ext.
        name = plugin[:-3]
        plugins[name] = __import__('plugins.' + name, globals(), locals(), -1)

    #---------------------------------------------------------------------------
    # Connect to servers and start working.
    #---------------------------------------------------------------------------

    # Test server connection, need some proper dynamic configuration, but that
    # can come later.
    servers += [connectIRC('', 6667, 'bruv')]
    servers[0].raw('JOIN #bruh\r\n')

    # Plugins work by hooking IRC events. Bruh provides one non-IRC related
    # event, 'BRUH'. Plugins that hook this event are called with the server
    # object immediately -- this allows them to do things such as modify the
    # server object before other plugins can access them. Here is where we call
    # those plugins.
    for server in servers:
        # Attach the plugins dictionary here, so that plugins have access to
        # it.  It happens before 'BRUH' hooks so those hooks can process
        # plugins in some way if required.
        server.plugins = plugins

        for hook in bruh.hooks['BRUH']:
            hook(server)

    # The IRC Loop.
    while True:
        # For each IRC connection we have open, look for incoming messages.
        for server in servers:
            # __call__ returns an iterable containing any recently receives
            # messages, pre-parsed into (prefix, command, args) as in the RFC.
            for prefix, command, args in server():
                # If no plugins have registered for an event, it is not in the
                # hooks dictionary.
                if command not in bruh.hooks:
                    continue

                # Otherwise, the hooks dictionary contains a list of functions
                # that have registered for that event.
                for hook in bruh.hooks[command]:
                    # The last message is also stored in the server itself.
                    # This allows the server to access messages as well as
                    # plugins.
                    server.parsed_message = (prefix, command, args)
                    hook(server, *server.parsed_message)
