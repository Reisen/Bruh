"""
    Implement a web server in bruh. Allows serving bot content, and also
    providing URL's for other purposes such as Github's repo Service Hooks.
"""
from traceback import format_stack
from urllib.request import urlopen
from threading import Thread
from plugins import event
from bottle import route, run, template

# The web server will run in a seperate thread, which we can refer to later
# when the plugin is being shut down.
WThread = None
port = 8081


def run_server():
    srv = run(host='0.0.0.0', port = port)
    while run_server.running:
        srv.handle_request()


@event('BRUH')
def initialze_web(irc):
    global WThread, port

    print('Initializing Web Server, Debug Call Stack:')
    for line in format_stack():
        print('--> ' + line.strip())

    if 'web' in irc.core['config']['plugins']:
        port = irc.core['config']['plugins']['web'].get('port', 8081)

    WThread = Thread(target = run_server)
    run_server.running = True
    WThread.start()


@event('GETOUT')
def shutdown_web():
    # Sadly, even though I've made the switch to use bottle.py as the web
    # framework for the bot, by default it uses WSGIServer, which is a subclass
    # of HTTPServer, so we get to deal with the same retarded ass fucking
    # handle_request method which we need to force to return by forging a
    # request.
    #
    # TODO: Hire a genius to make this not shit.
    run_server.running = False
    try:
        urlopen('http://localhost:{}/'.format(port)).read()
    except:
        # Again, fuck HTTPServer, we're expecting an error here no matter what,
        # so lets just quit this shit. Fuck HTTPServer.
        WThread.join()
