"""
    This file implements plugin loading, connecting to IRC, and the actual main
    loop for dispatching events to plugins.
"""

import os, sys, signal, argparse, json

from plugins import hooks
from irc import IRC, connectIRC


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


def loopDefault(server):
    """
    Default event loop handler for servers. By default just hands IRC events
    to plugin event handlers.
    """
    # __call__ returns an iterable containing any recently receives messages,
    # pre-parsed into (prefix, command, args) as in the RFC.
    for prefix, command, args in server():
        # If no plugins have registered for this messages event event type, it
        # is not in the hooks dictionary and the message can just be ignored.
        if command not in hooks:
            continue

        # Otherwise, the hooks dictionary contains a list of functions that
        # have registered for that event.
        for hook in hooks[command]:
            # The last message is also stored in the server itself.  This state
            # is useful when inspecting the server during messages. It's not
            # necessarily useful for plugins themselves.
            server.parsed_message = (prefix, command, args)
            hook(server, *server.parsed_message)


if __name__ == '__main__':
    # Parse configuration files, configuration is used for everything from
    # servers to plugin options. If no file exists at all, running the bot
    # generates one and tells the user to go and edit it.
    try:
        with open('config') as f:
            config = json.loads(f.read())
    except IOError:
        with open('config', 'w') as f:
            default_config = {
                'nick': 'bruh',
                'prefix': '.',
                'blacklist': [],
                'plugins': {},
                'servers': [
                    {
                        'address': 'irc.example.com',
                        'port': 6667,
                        'ssl': False,
                        'verify_ssl': True,
                        'nick': 'example_nick',
                        'password': None,
                        'channels': ['#bruh']
                    }
                ]
            }
            f.write(json.dumps(default_config, indent = 4, separators = (', ', ': ')))
            f.close()

            # Tell the user there was no configuration file and quit.
            print('There was no config file, one has been created.')
            print('Edit it and run the bot again.\n')
            sys.exit(0)
    except Exception as e:
        print('Failed to read configuration file:\n    ')
        print(e)
        sys.exit(0)

    # Check for some major configuration errors, things that should immediately
    # cause the bot to quit:
    #   * No servers defined
    #   * No default nick defined (real name and username can be blank)
    errors = [
        ('nick', 'A default nick must be defined, even if servers define their own.'),
        ('servers', 'No servers were provided, at least one should be given.')
    ]
    for key, error in errors:
        if key not in config:
            print('Error: {}'.format(error))
            sys.exit(0)

    # Plugins need to be imported before IRC connections are made, as plugins
    # are used to handle core IRC messages.
    blacklist = config.get('blacklist', [])
    blacklist.append('__init__.py')
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

    # Connect to all servers provided in the configuration. Plugins have a lot
    # of access to the bot core, and could potentially add more servers to this
    # list so don't rely on equivelence to the config.
    for server in config['servers']:
        connection = connectIRC(
            server['address'],
            server['port'],
            server.get('nick', config['nick']),
            server.get('password', None)
        )

        # Modify the server objects with any relevant information plugins might
        # end up using, such as plugin lists and other core information.
        connection.loop = loopDefault
        connection.core = {}
        connection.core['plugins'] = plugins
        connection.core['servers'] = servers
        connection.core['config'] = config
        connection.config = server

        # The bot provides a fake IRC event called 'BRUH' that is called when
        # the server first gets created. It's called here, now, and never again
        # to allow plugins to do any pre-server handling configuration. No
        # plugins are guaranteed to have been loaded at this point, don't use
        # this event for any inter-plugin operations (NO DATABASES).
        for hook in hooks.get('BRUH', []):
            hook(connection)

        # Save the server and finish joining channels.
        servers.append(connection)
        for channel in server.get('channels', []):
            connection.raw('JOIN %s\r\n' % channel)

    # The IRC Loop.
    while True:
        # For each IRC connection we have open, look for incoming messages.
        for server in servers:
            # Pass control to this servers event loop.
            server.loop(server)
