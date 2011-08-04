"""
    Plugin that scrapes the bold part out of googles search results, great for
    calculations and shit.
"""
from urllib.error import URLError
from urllib import request, parse
from plugins.commands import command
import re

@command
def calc(irc, nick, chan, msg, args):
    """
    Sends queries to googles calculator.
    .calc <query>
    """
    # Fetch the page information from google.
    url = parse.urlunparse(parse.ParseResult(
        scheme = 'http',
        netloc = 'google.com',
        path = '/search',
        params = '',
        query = 'q=' + parse.quote_plus(msg),
        fragment = ''
    ))

    # Google 403's requests without user-agents to prevent people from scraping
    # their pages, good thing I'm not doing that then.
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
    }
    url = request.Request(url, None, headers)
    
    data = request.urlopen(url).read().decode('UTF-8')

    # Disgustingly parse the HTML with regex
    match = re.search(r'<h2 class=r style="font-size:138%"><b>(.*?)</b>', data)

    if match is None:
        return "Could not calculate: " + msg

    return match.group(1).replace(r'<font size=-2> </font>', ',') \
            .replace(r' &#215; 10<sup>', 'E') \
            .replace(r'</sup>', '')

