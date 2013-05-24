"""
    Provides a URL that Github can use as a service hook for posting git commit
    info too. Channels can have these announced if they so wish to.
"""
from json import loads
from plugins import event
from bottle import route, request
from plugins.commands import command

# Dirty solution to route requests lacking context. Keep a list of all IRC
# objects and iterate through them on web-requests. This is akin to having
# a command run for every network at the same time.
irc_map = []

@event('BRUH')
def prepare_github(irc):
    irc_map.append(irc)


def setup_db(irc):
    irc.db.execute('''
        CREATE TABLE github_repos (
            id INTEGER PRIMARY KEY,
            channel TEXT,
            name TEXT
        );
    ''')
    irc.db.commit()


@route('/github/')
def index():
    payload = loads(request.params.payload)
    print(str(payload))
    #for irc in irc_map:
    #    interests = irc.db.execute('SELECT * FROM github_repos WHERE name=?', (request.query.repo)).fetchall()
    #    for interest in interests:
    #        irc.say(interest[1], request.query.status)

    return ''


@command
def github(irc, nick, chan, msg, args):
    """
    Manage tracked Github projects.
    .github add <repo>
    .github remove <repo>
    .github list
    """
    setup_db(irc)

    command, *args = msg.split(' ', 1)
    try:
        commands = {
            'add': lambda: add(irc, args[0])
        }
        return commands[command]()
    except KeyError:
        return "Tried to run unknown command '{}'.".format(command)
