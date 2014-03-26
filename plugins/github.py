"""
    Provides a URL that Github can use as a service hook for posting git commit
    info too. Channels can have these announced if they so wish to.
"""
from json import loads
from plugins import event
from bottle import route, request, post
from plugins.commands import command

# Dirty solution to route requests lacking context. Keep a list of all IRC
# objects and iterate through them on web-requests. This is akin to having a
# command run for every network at the same time.
irc_map = []

@event('BRUH')
def prepare_github(irc):
    global irc_map
    irc_map.append(irc)


def setup_db(irc):
    irc.db.execute('''
        CREATE TABLE IF NOT EXISTS github_repos (
            channel TEXT,
            name TEXT,
            PRIMARY KEY(channel, name)
        );
    ''')
    irc.db.commit()


@post('/github/')
def index():
    # Parse Github's Payload.
    try:
        payload = loads(request.params.payload)
        repo_name = '{}/{}'.format(
            payload['repository']['owner']['name'],
            payload['repository']['name']
        )

        # Scan IRC objects looking for ones that contain interest in their github
        # databases.
        for irc in irc_map:
            setup_db(irc)

            interests = irc.db.execute('SELECT * FROM github_repos WHERE name=?', (repo_name,)).fetchall()
            if interests:
                for interest in interests:
                    repo_status = '{} - {} commits pushed. {} ({}) - Pushed By {}'.format(
                        repo_name,
                        len(payload['commits']),
                        payload['head_commit']['message'].split('\n')[0],
                        payload['head_commit']['id'][:7],
                        payload['head_commit']['author']['username']
                    )

                    irc.say(interest[0], repo_status)

        return ''

    except Exception as e:
        print(str(e))


def github_add(irc, chan, name):
    try:
        irc.db.execute('INSERT INTO github_repos (channel, name) VALUES (?, ?)', (chan, name))
        irc.db.commit()
        return "Now tracking {}".format(name)

    except:
        return "I am already tracking that repository."


def github_remove(irc, chan, name):
    irc.db.execute('DELETE FROM github_repos WHERE channel = ? AND name = ?', (chan, name))
    irc.db.commit()
    return "No longer tracking {}".format(name)


def github_list(irc, chan):
    repos = irc.db.execute('SELECT name FROM github_repos WHERE channel = ?', (chan,)).fetchall()
    if not repos:
        return "I am not tracking any respositories for this channel."

    return "Tracked repositories: {}".format(', '.join(map(lambda v: v[0], repos)))


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
            'add':    lambda: github_add(irc, chan, args[0]),
            'remove': lambda: github_remove(irc, chan, args[0]),
            'list':   lambda: github_list(irc, chan)
        }
        return commands[command]()

    except KeyError:
        return "Tried to run unknown github subcommand: {}.".format(command)
