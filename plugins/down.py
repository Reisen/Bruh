import urllib.request
from urllib.error import URLError
from bruh import command

@command('down')
@command('d')
def down(irc):
    try:
        if not irc.message:
            return "Syntax: .down <url>"

        if not irc.message.startswith('http://'):
            irc.message = 'http://' + irc.message

        urllib.request.urlopen(irc.message, timeout = 7)
        return "It's just you, {} is up.".format(irc.message)

    except URLError:
        return "It's not just you, {} seems to be down.".format(irc.message)

    except Exception as e:
        print(e)
        return "I'm not sure, something went wrong requesting the page but it might be my side."
