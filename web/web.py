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


@app.route('/commands/')
def guide():
    return render_template('commands.html', **{
    })


@app.route('/guide/')
def commands():
    return render_template('guide.html', **{
    })


@app.route('/channel/<string:channel>/')
def view_channel(channel):
    from string import punctuation
    from itertools import repeat, chain

    generate()

    channel   = '#' + channel
    quotes    = map(lambda v: v.decode('UTF-8'), red.lrange('irc.rizon.net:{}:quotes'.format(channel), 0, -1))
    users     = sorted([(k, cached[channel][k]) for k in cached[channel] if isinstance(cached[channel][k], dict)], key = lambda v: int(v[1].get('messages', 0)), reverse = True)
    words     = []
    stopwords = ['i','me','my','myself','we','us','our','ours','ourselves','you','your','yours','yourself','yourselves','he','him','his','himself','she','her','hers','herself','it','its','itself','they','them','their','theirs','themselves','what','which','who','whom','whose','this','that','these','those','am','is','are','was','were','be','been','being','have','has','had','having','do','does','did','doing','will','would','should','can','could','ought','i\'m','you\'re','he\'s','she\'s','it\'s','we\'re','they\'re','i\'ve','you\'ve','we\'ve','they\'ve','i\'d','you\'d','he\'d','she\'d','we\'d','they\'d','i\'ll','you\'ll','he\'ll','she\'ll','we\'ll','they\'ll','isn\'t','aren\'t','wasn\'t','weren\'t','hasn\'t','haven\'t','hadn\'t','doesn\'t','don\'t','didn\'t','won\'t','wouldn\'t','shan\'t','shouldn\'t','can\'t','cannot','couldn\'t','mustn\'t','let\'s','that\'s','who\'s','what\'s','here\'s','there\'s','when\'s','where\'s','why\'s','how\'s','a','an','the','and','but','if','or','because','as','until','while','of','at','by','for','with','about','against','between','into','through','during','before','after','above','below','to','from','up','upon','down','in','out','on','off','over','under','again','further','then','once','here','there','when','where','why','how','all','any','both','each','few','more','most','other','some','such','no','nor','not','only','own','same','so','than','too','very','say','says','said','shall']

    for (k, v) in sorted(red.hgetall('irc.rizon.net:{}:cloud'.format(channel)).items(), key = lambda v: int(v[1].decode('UTF-8')), reverse = True):
        word = k.decode('UTF-8')

        if word in stopwords:
            continue

        if len(word) < 4:
            continue

        for l in punctuation:
            if l in word:
                break
        else:
            words.append((word, v.decode('UTF-8')))

    return render_template('channel.html', **{
        'stats': cached,
        'words': words[:100],
        'word_count': len(words),
        'messages': cached[channel]['messages'],
        'users': users[:100],
        'user_count': len(users),
        'quotes': quotes,
        'channel': channel
    })

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 27015, debug = True)
