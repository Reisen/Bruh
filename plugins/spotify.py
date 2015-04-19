import json
from urllib.parse import quote_plus, unquote_plus
from urllib.request import urlopen, Request
from bruh import command
from random import choice


def search_artist(irc, artist):
    request = Request(
        'https://api.spotify.com/v1/search?type=artist&q={}'.format(quote_plus(artist)),
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11'
        }
    )

    try:
        query  = json.loads(urlopen(request, timeout = 7).read().decode('UTF-8'))
        result = [artist['name'] for artist in query['artists']['items']]
        return 'Artists: ' + ', '.join(result[:5])

    except Exception as e:
        return str(e)


def search_album(irc, album):
    request = Request(
        'https://api.spotify.com/v1/search?type=album&q={}'.format(quote_plus(album)),
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11'
        }
    )

    try:
        query  = json.loads(urlopen(request, timeout = 7).read().decode('UTF-8'))
        result = query['albums']['items']
        if album.lower() in result[0]['name'].lower():
            request = Request(
                'https://api.spotify.com/v1/albums/{}'.format(quote_plus(result[0]['id'])),
                headers = {
                    'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11'
                }
            )

            query = json.loads(urlopen(request, timeout = 7).read().decode('UTF-8'))
            track = choice(query['tracks']['items'])
            return 'Album: \x02{}\x02 - By \x02{}\x02 - Released \x02{}\x02 - \x02{}\x02 Tracks - Length \x02{}ms\x02 - Random Track: \x02{}. {}\x02'.format(
                query['name'],
                query['artists'][0]['name'],
                query['release_date'],
                len(query['tracks']['items']),
                0,
                track['track_number'],
                track['name']
            )

        result = [album['name'] for album in query['albums']['items']]
        return 'Album Results: ' + ', '.join(result[:5])

    except Exception as e:
        return 'Could not find anything for that search.'


def search_song(irc, song):
    request = Request(
        'https://api.spotify.com/v1/search?type=track&q={}'.format(quote_plus(song)),
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11'
        }
    )

    try:
        query  = json.loads(urlopen(request, timeout = 7).read().decode('UTF-8'))
        result = query['tracks']['items']
        if song.lower() in result[0]['name'].lower():
            track = result[0]
            return 'Song: \x02{}\x02 - Album \x02{}\x02 - By \x02{}\x02 - Length \x02{}ms\x02'.format(
                track['name'],
                track['album']['name'],
                track['artists'][0]['name'],
                0
            )

        result = [song['name'] for song in query['tracks']['items']]
        return 'Song Results: ' + ', '.join(result[:5])

    except Exception as e:
        return 'Could not find anything for that search.'


@command('spotify')
@command('spot')
def spotify(irc):
    """Returns information about artists, albums, songs and spotify users."""
    try:
        cmd, *args = irc.message.split(' ', 1)
        return {
            'artist': search_artist,
            'album': search_album,
            'song': search_song
        }[cmd](irc, *args)

    except KeyError:
        return search_song(irc, irc.message)


@command('album')
def spotify_album(irc):
    try:
        return search_album(irc, irc.message)

    except Exception as e:
        pass


@command('song')
def spotify_song(irc):
    try:
        return search_song(irc, irc.message)

    except Exception as e:
        pass
