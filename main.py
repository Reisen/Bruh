"""
    This file implements plugin loading, connecting to IRC, and the actual main
    loop for dispatching events to plugins.
"""

import os
import sys
import signal
import argparse

from bruh.irc import IRC, connectIRC
from plugins import bruh


# Collection of open server connections
servers = []


# Register a Ctrl+C Signal, allows plugins to receive a shutdown signal so they
# can clean up nicely.
def quit(signal, frame):
    print('Sending shutdown warning to plugins...')
    for hook in bruh.hooks['GETOUT']:
        hook()

    sys.exit(0)

signal.signal(signal.SIGINT, quit)


if __name__ == '__main__':
    #---------------------------------------------------------------------------
    # Process commandline arguments
    #---------------------------------------------------------------------------

    parser = argparse.ArgumentParser()

    parser.add_argument('-s', '--server', action='store', required=True, help='the IRC server (e.g. irc.rizon.net)')
    parser.add_argument('-p', '--port', action='store', default=6667, help='the IRC server port (usually 6667)')
    parser.add_argument('-c', '--channels', action='store', default=[], help='list of comma separated channels')
    parser.add_argument('-n', '--nick', action='store', default='bruv', help='the nickname of the bot')

    args = parser.parse_args(sys.argv[1:])
    if args.channels:
        args.channels = args.channels.split(',')

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
    servers += [connectIRC(args.server, args.port, args.nick)]

    for channel in args.channels:
        servers[0].raw('JOIN %s\r\n' % channel)

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
