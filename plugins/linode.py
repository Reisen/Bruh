"""
    Provide access to the Linode API. Requires users to be authenticated and
    have provided their Linode key. This is of course a risky thing to do
    storing sensitive data.
"""
from base64 import b64decode
from json import loads
from urllib.request import urlopen
from plugins import mod

hook           = mod.hook
authentication = mod.authentication


def validate_key(key):
    if len(key) < 64:
        return False

    try:
        key = b64decode(key, validate = True)
        return True
    except Exception as e:
        return False


def linode_list(irc, linode_key):
    try:
        if not validate_key(linode_key):
            return "Your Linode Key is in a fucked up format. Can't make any requests with it."

        # Fetch API information from Linode, which returns a nice JSON response
        # to work with.
        api_response = loads(urlopen('https://api.linode.com/?api_key={}&api_action=linode.list'.format(linode_key)).read().decode('UTF-8'), timeout = 7)
        linode_list = 'Your Linodes: '
        for server in api_response['DATA']:
            linode_list += '\x02{}\x02 - HD Space: \x02{}\x02 - RAM: \x02{}\x02 - Bandwidth: \x02{}\x02, '.format(
                server['LABEL'],
                server['TOTALHD'],
                server['TOTALRAM'],
                server['TOTALXFER']
            )

        # Remove the comma from the end before returning.
        return linode_list[:-2]

    except Exception as e:
        return "Error occured performing API call."


@hook.command
@authentication.authenticated
def linode(irc, nick, chan, msg, args, user):
    """
    Provide access to control and display information about your linodes. Requires authentication.
    .linode list
    .linode key <key>
    """
    if not msg:
        return "Syntax: .linode <command> [<arg>, <arg>...]"

    # Try and setup a Linode Key first, in case the user is attempting to
    # provide that. Otherwise nothing else will work.
    command, *args = msg.split(' ', 1)
    if command == 'key' and args:
        user['linode_api_key'] = args[0]
        return "New key {} associated with your IRC user.".format(args[0])

    if 'linode_api_key' not in user:
        return "You need to associate a Linode API key with your user. Do this with .linode key <key>."

    linode_key = user['linode_api_key']
    try:
        commands = {
            'list': lambda: linode_list(irc, linode_key)
        }
        return commands[command]()

    except KeyError:
        return "Tried to run unknown command '{}'.".format(command)
