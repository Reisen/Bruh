"""
    Provides a URL that Github can use as a service hook for posting git commit
    info too. Channels can have these announced if they so wish to.
"""
from json import loads
from plugins import event
from bottle import route, request, post
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


@post('/github/')
def index():
    # Parse Github's Payload.
    payload = loads(request.params.payload)
    repo_name = '{}/{}'.format(
        payload['repository']['owner']['name'],
        payload['repository']['name']
    )

    # Scan IRC objects looking for ones that contain interest in their github
    # databases.
    for irc in irc_map:
        interests = irc.db.execute('SELECT * FROM github_repos WHERE name=?', (repo_name,)).fetchall()
        for interest in interests:
            repo_status = '{} - {} commits pushed. {} ({}) - Pushed By {}'.format(
                repo_name,
                len(payload['commits']),
                payload['head_commit']['message'],
                payload['head_commit']['id'][:7],
                payload['head_commit']['author']['username']
            )

            irc.say(interest[1], repo_status)

    return ''


def github_add(irc, chan, name):
    irc.db.execute('INSERT INTO github_repos (channel, name) VALUES (?, ?)', (chan, name))
    irc.db.commit()
    return "Now tracking {}".format(name)


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
            'add': lambda: github_add(irc, chan, args[0])
        }
        return commands[command]()
    except KeyError:
        return "Tried to run unknown command '{}'.".format(command)
