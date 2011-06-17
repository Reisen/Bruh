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


# Setup signal handler
signal.signal(signal.SIGINT, quit)


# Start main loop
if __name__ == '__main__':
    #---------------------------------------------------------------------------
    # Sort out plugins before any IRC connections are made
    #---------------------------------------------------------------------------

    blacklist = ['__init__.py', 'bruh.py']
    plugins   = {} 

    # Search plugin directory
    for plugin in os.listdir('plugins'):
        if plugin in blacklist or not plugin.endswith('.py'):
            continue

        # Import plugin, hooks are inserted into a hook dictionary
        # in the bruh.py plugin
        name = plugin[:-3]
        plugins[name] = __import__('plugins.' + name, globals(), locals(), -1)

    #---------------------------------------------------------------------------
    # Connect to servers and start working.
    #---------------------------------------------------------------------------

    servers += [connectIRC('*', 31372, 'bruv')]
    servers[0].raw('JOIN #bruh\r\n')

    # The special event 'BRUH' specify modules that should be immediately
    # called, an IRC message is not passed for this. These are plugins that might
    # modify irc objects.
    #
    # Here we also make the plugins list available to servers.
    for server in servers:
        for item in bruh.hooks['BRUH']:
            item(server)
            print('Called %s with %s' % (repr(item), repr(server)))
            server.plugins = plugins

    # Forever!
    while True:
        # For each IRC connection we have open, look for incoming
        # messages, parse and respond. In the future, will look into
        # improving this by starting checks in greenlets.
        for server in servers:
            for message in server():
                # Hand off events to plugins
                prefix, command, args = message
                print(message)

                # Ignore unhandled events
                if command not in bruh.hooks:
                    continue

                # Hand hooks the event
                for hook in bruh.hooks[command]:
                    server.message = message
                    hook(server, *message)
