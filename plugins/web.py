"""
    Implement a web server in bruh. Allows serving bot content, and also
    providing URL's for other purposes such as Github's repo Service Hooks.
"""
from threading import Thread
from plugins import event
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen
from urllib.parse import parse_qs
from re import search
from cgi import parse_multipart, parse_header, FieldStorage
from string import Template

handlers = {}

def template(filename, data):
    """Do simple python substitution on a template."""
    with open('plugins/templates/{}'.format(filename)) as f:
        return Template(f.read()).safe_substitute(data)


def route(path):
    """Binds routes to a method."""
    def hook(f):
        handlers[path] = f
        return f

    return hook


class BotHandler(BaseHTTPRequestHandler):
    """
    Handles URL requests and maps them to different bot functions which match
    the request via regex.
    """
    def do_GET(self):
        self.send_response(200)
        self.end_headers()

        path, *parameters = self.path.split('?', 1)
        if parameters:
            parameters = parse_qs(parameters[0])

        for handler in handlers:
            if search(handler, self.path):
                self.wfile.write(str(handlers[handler](parameters)).encode('UTF-8'))
                return None

        self.wfile.write('No plugins handled this request.'.encode('utf-8'))

    def do_POST(self):
        ctype, pdata = parse_header(self.headers['Content-type'])
        pdata = {k: v.encode('UTF-8') for k, v in pdata.items()}

        for handler in handlers:
            if ctype == 'application/x-www-form-urlencoded' and search(handler, self.path):
                data = self.rfile.read(int(self.headers['Content-Length']))
                parameters = parse_qs(data)
                if parameters:
                    self.send_response(301)
                    self.send_header('Location', '/post/create/')
                    self.end_headers()

                    parameters = {k.decode('UTF-8'): v[0].decode('UTF-8') for k, v in parameters.items()}
                    self.wfile.write(str(handlers[handler](parameters)).encode('UTF-8'))
                    return None

        self.send_response(500)
        self.end_headers()
        self.wfile.write('Error handling request. Expected form data.'.encode('UTF-8'))

HThread = None
Handler = None

@event('GETOUT')
def shutdown_web():
    global Handler
    Handler = None

    # This is some of the dirtiest shutdown mechanics I think I've ever had to
    # write. No timeout on handle_request apparantly so we need to fire off a
    # dummy request at _our own server_ to force it out of the loop.
    try:
        urlopen('http://localhost:8081').read()
    except:
        # This is bad practice but we're expecting an error here, and
        # HTTPServer is dumb. We just want to kill it.
        pass

    HThread.join()


def run_server():
    global Handler
    Handler = HTTPServer(('0.0.0.0', 8081), BotHandler)
    while Handler:
        Handler.handle_request()


@event('BRUH')
def initialze_web(irc):
    global HThread
    config = irc.core['config']['plugins'].get('web', {})

    HThread = Thread(target = run_server)
    HThread.start()
