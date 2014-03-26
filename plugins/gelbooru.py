"""
    A plugin to query the Gelbooru API. The comments are horrifying.
"""
from plugins.commands import command
from urllib.error import URLError
from urllib.request import urlopen
from xml.etree import ElementTree
from time import time

# Globals here aren't a good idea, should really be caching per channel,
# however in reality very few people are going to use this module so I'll fix
# it another day.
comment_count = 0
comment_delay = 0
comment_cache = None
posting_count = 0
posting_delay = 0
posting_cache = None


def gelbooru_comments():
    global comment_count, comment_cache, comment_delay
    if not comment_cache or comment_count > 25 or time() - comment_delay >= 21600:
        # To limit the API hits, we cache the result and print from it until 25
        # comments have been printed or 20 minutes has passed.
        listing       = urlopen('http://gelbooru.com/index.php?page=dapi&s=comment&q=index', timeout = 7).read().decode('UTF-8')
        listing       = ElementTree.fromstring(listing)

        # Check to see if the newest comment is actually new, if it is, check
        # if the last old comment is older than 5 new comments, otherwise make
        # the user wait a while.
        if comment_cache and listing[0].attrib['id'] != comment_cache[0].attrib['id']:
            for list_post in listing[:5]:
                if list_post.attrib['id'] == comment_cache[0].attrib['id']:
                    return "Not many new comments have been posted yet. Wait a little while."

        comment_cache = listing
        comment_count = 0
        comment_delay = time()

    comment_count += 1
    return "{} - by {}. ({})".format(
        comment_cache[comment_count].attrib['body'],
        comment_cache[comment_count].attrib['creator'],
        'http://gelbooru.com/index.php?page=post&s=view&id={}'.format(comment_cache[comment_count].attrib['post_id'])
    )


def gelbooru_posts(tags):
    global posting_count, posting_cache, posting_delay
    if not posting_cache or posting_count > 25 or time() - posting_delay >= 21600:
        # To limit the API hits, we cache the result and print from it until 25
        # posts have been printed or 20 minutes has passed.
        tags          = '&tags={}'.format(tags) if tags else ''
        listing       = urlopen('http://gelbooru.com/index.php?page=dapi&s=post&q=index{}'.format(tags), timeout = 7).read().decode('UTF-8')
        listing       = ElementTree.fromstring(listing)

        # Check to see if the newest post is actually new, if it is, check if
        # the last old post is older than 5 new posts, otherwise make the user
        # wait a while.
        if posting_cache and listing[0].attrib['id'] != posting_cache[0].attrib['id']:
            for list_post in listing[:5]:
                if list_post.attrib['id'] == posting_cache[0].attrib['id']:
                    return "Not many new posts have been posted yet. Wait a little while."

        posting_cache = listing
        posting_count = 0
        posting_delay = time()

    posting_count += 1
    return "Rated: {} - Tags: {}... - {}".format(
        posting_cache[posting_count].attrib['rating'],
        ', '.join(posting_cache[posting_count].attrib['tags'].split()[:5]),
        'http://gelbooru.com/index.php?page=post&s=view&id={}'.format(posting_cache[posting_count].attrib['id'])
    )


@command
def gelbooru(irc, nick, chan, msg, args):
    """
    Query the gelbooru API. No arguments returns a random comment.
    .gelbooru
    .gelbooru <tag>
    """
    if msg:
        return gelbooru_posts(msg)

    return gelbooru_comments()

