"""
    This file implements plugin loading, connecting to IRC, and the actual main
    loop for dispatching events to plugins.
"""

import os, sys, signal, argparse, json

from bruh.irc import IRC, connectIRC
from plugins import hooks


# Collection of open server connections
servers = []


# Register a Ctrl+C Signal, allows plugins to receive a shutdown signal so they
# can clean up nicely.
def quit(signal, frame):
    print('\nSending shutdown warning to plugins...')
    for hook in hooks.get('GETOUT', []):
        hook()
    print('Done')

    sys.exit(0)

signal.signal(signal.SIGINT, quit)


if __name__ == '__main__':
    # Process commandline arguments, temporary until a proper configuration file is sorted.
    parser = argparse.ArgumentParser()

    parser.add_argument('-s', '--server', action='store', required=True, help='the IRC server (e.g. irc.rizon.net)')
    parser.add_argument('-p', '--port', action='store', default=6667, help='the IRC server port (usually 6667)')
    parser.add_argument('-c', '--channels', action='store', default=[], help='list of comma separated channels')
    parser.add_argument('-n', '--nick', action='store', default='brux', help='the nickname of the bot')
    parser.add_argument('-k', '--password', action='store', default=None, help='password to the server')

    args = parser.parse_args(sys.argv[1:])
    if args.channels:
        args.channels = args.channels.split(',')

    # Plugins need to be imported before IRC connections are made, as plugins
    # are used to handle core IRC messages.
    blacklist = ['__init__.py']
    plugins   = {}

    # A map of plugins and their names is kept so that inter-plugin operations
    # are possible. Useful for enforcing dependencies between plugins.
    for plugin in os.listdir('plugins'):
        # Ignore blacklisted files, or files not ending with .py
        if plugin in blacklist or not plugin.endswith('.py'):
            continue

        # __import__ uses pythons dot syntax to import, so remove the .py ext.
        name = plugin[:-3]
        plugins[name] = __import__('plugins.' + name, globals(), locals(), -1)

    # Connect to servers, explicitly connect to one for now, later this should
    # be done by dynamically reading configuration.
    servers += [connectIRC(args.server, args.port, args.nick, args.password)]

    # Assumes one server, later should be fixed to join channels from a
    # configuration on the correct corresponding server.
    for channel in args.channels:
        servers[0].raw('JOIN %s\r\n' % channel)

    # The bot provides a fake IRC event called 'BRUH'. It's faked here once
    # before server handling happens so plugins can do some form of initial
    # setup, this guarantees plugins that all other plugins have been loaded
    # before this message is sent.
    #
    # No plugins that depend on other plugins should use this.
    for server in servers:
        # Modify each server to expose the plugins dictionary to plugins that
        # receive them in events.
        server.plugins = plugins

        for hook in hooks['BRUH']:
            hook(server)

    # The IRC Loop.
    while True:
        # For each IRC connection we have open, look for incoming messages.
        for server in servers:
            # __call__ returns an iterable containing any recently receives
            # messages, pre-parsed into (prefix, command, args) as in the RFC.
            for prefix, command, args in server():
                # If no plugins have registered for this messages event event
                # type, it is not in the hooks dictionary and the message can
                # just be ignored.
                if command not in hooks:
                    continue

                # Otherwise, the hooks dictionary contains a list of functions
                # that have registered for that event.
                for hook in hooks[command]:
                    # The last message is also stored in the server itself.
                    # This state is useful when inspecting the server during
                    # messages. It's not necessarily useful for plugins
                    # themselves.
                    server.parsed_message = (prefix, command, args)
                    hook(server, *server.parsed_message)
