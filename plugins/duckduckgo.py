"""
    This module wraps the DDG Instant Answer API. A godamn badass API.  At some
    point this might be the default entry point for the .calc command instead
    of the google calculator.
"""
from urllib.parse import quote_plus, unquote_plus, urlencode
from urllib.request import urlopen, Request
from plugins import mod
import json

commands = mod.commands

def handle_exclusive(query):
    return query['Answer']


def handle_article(query):
    return query['AbstractText']


def handle_disambiguation(query):
    # DDG Figured out a probable result for us.
    if query['AbstractText']:
        return query['AbstractText']

    # Or maybe a probable definition.
    if query['Definition']:
        return '{} (Source: {})'.format(
            query['Definition'],
            query['DefinitionSource'] if query['DefinitionSource'] else query['AbstractSource']
        )

    # Or maybe DDG figured out NOTHING, in which case lets just hope the first
    # related topic is sensible.
    return query['RelatedTopics'][0]['Text']


@commands.command(['ddg'])
def duckduckgo(irc, nick, chan, msg, args):
    """
    DuckDuckGo Instant API.
    .ddg <expression>
    """
    if not msg:
        return "Syntax: .ddg <expression>"

    # Build the request. DuckDuckGo requires an app name parameter for request
    # attribution, so don't remove this.
    request = Request(
        'https://api.duckduckgo.com/?{}'.format(urlencode({
            'q': msg,
            'format': 'json',
            'pretty': 1,
            'no_redirect': 1,
            'no_html': 1
        })),
        headers = {
        }
    )

    try:
        query = json.loads(urlopen(request, timeout = 7).read().decode('UTF-8'))

        # Dispatch to a function that understands the format type returned.
        output = {
            'E': lambda: handle_exclusive(query),
            'A': lambda: handle_article(query),
            'D': lambda: handle_disambiguation(query)
        }[query['Type']]()

        if output:
            return output

    except Exception as e:
        return "No decent results found for those terms."
