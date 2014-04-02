"""
    Do calculations with Google calculator.
"""
import re
from json import loads
from plugins.commands import command
from urllib.request import urlopen, Request
from urllib.parse import quote_plus
from html.parser import HTMLParser

@command
def calculate(irc, nick, chan, msg, args):
    """
    Use Google's Calculator
    .calc <equation>
    """
    if not msg:
        return "Syntax: .calculate <expression>"

    try:
        # Need to create a Request object because google goes nuts if you don't
        # have reasonable browser-looking headers.
        request = Request(
            'https://encrypted.google.com/search?hl=en&source=hp&biw=&bih=&q={}&btnG=Google+Search&gbv=1'.format(quote_plus(msg)),
            headers = {
                'Referer': 'http://github.com/Reisen/Bruh',
                'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11'
            }
        )

        # Try and parse out the result (Regex... I know, fuck it).
        result = urlopen(request, timeout = 7)
        result = HTMLParser().unescape(result.read().decode('unicode-escape'))
        result = re.findall('<h2 class="r".*?>(.*)</h2>', result, re.M | re.I | re.S)
        if result:
            return result[0].strip()

        return "Google couldn't calculate this."

    except Exception as e:
        return str(e)
        return "There was an error trying to calculate this."
