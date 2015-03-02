from time import time
from collections import defaultdict
from redis import StrictRedis
from flask import Flask, render_template

red     = StrictRedis(db = 4)
app     = Flask(__name__)
cached  = None
timeout = 0


def generate():
    global cached, timeout
    if time() - timeout < 600:
        return None

    timeout    = time()
    statistics = defaultdict(dict)

    # Parse the stats into our cacheable python dictionary which has a slightly
    # easier format to work with.
    for stat in red.scan_iter(match = 'irc.rizon.net:#*:stats'):
        _, chan, *parts = stat.decode('UTF-8').rsplit(':', 3)
        if parts[0] == 'stats': target = statistics[chan]
        else:                   target = statistics[chan].setdefault(parts[0], {})

        for k, v in red.hscan_iter(stat):
            target[k.decode('UTF-8')] = v.decode('UTF-8')

        cached = statistics

    # Do some post processing. So we know things like most active users.
    for stat in list(cached.keys()):
        for user in cached[stat]:
            if type(cached[stat][user]) != dict:
                continue

            # Count up all the users messages, so we can check their activity
            # over the whole network.
            ustate = cached.setdefault(user, {
                'messages': 0,
                'words': 0
            })

            for key in ustate.keys():
                if key not in cached[stat][user]:
                    continue

                ustate[key] += int(cached[stat][user][key])


@app.route('/')
def index():
    generate()
    return render_template('index.html', **{
        'stats': cached,
        'chans': sorted([(k,cached[k]['messages']) for k in cached], key = lambda v: int(v[1]), reverse = True)
    })


@app.route('/channel/<string:channel>/')
def view_channel(channel):
    generate()
    return render_template('channel.html', **{
        'stats': cached,
        'users': [(k,cached[k]) for k in cached if k.startswith('#')],
        'channel': channel
    })

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 27015, debug = True)
