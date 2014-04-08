"""This plugin implements a lot of functionality of infobot."""
import random, re
from plugins import mod

hook = mod.hook
auth = mod.auth

def setup_db(irc):
    irc.db.execute('''
        CREATE TABLE IF NOT EXISTS factoids (
            id INTEGER PRIMARY KEY,
            key TEXT UNIQUE,
            value TEXT
        );
    ''')
    irc.db.commit()


@hook.command
def remember(irc, nick, chan, msg, args):
    """
    Adds new facts to the database.
    .remember <key> <value>
    """
    setup_db(irc)

    if not msg:
        return "Syntax: .remember <key> <value>"

    key, *value = msg.split(' ', 1)
    if not value:
        return "Syntax: .remember <key> <value>"

    # See if an object with this key already exists. If it does, overwrite the
    # value instead of creating a new entry.
    fact = irc.db.execute('SELECT * FROM factoids WHERE key = ?', (key,)).fetchone()

    # Update existing keys.
    if fact is not None:
        # Append new data to the definition if the fact already exists.
        if fact[2] == value[0]:
            return "I already knew that. Tell me something I don't know."

        irc.db.execute('UPDATE factoids SET value = value || ? WHERE key = ?', (', ' + value[0], key))
        irc.db.commit()
        return "I'll remember that too."

    # Add the new keys to the database.
    irc.db.execute('INSERT INTO factoids (key, value) VALUES (?, ?)', (key, value[0]))
    irc.db.commit()
    return "I'll remember that."


@hook.command
@auth.logged_in
def forget(irc, nick, chan, msg, args, user):
    """
    Remove facts from the database.
    .forget <key>
    """
    if not msg:
        return "Syntax: .forget <key>"

    irc.db.execute('DELETE FROM factoids WHERE key = ?', (msg,))
    irc.db.commit()
    return "I've forgotten about {}.".format(msg)


@hook.regex(r'^\?([^\s]+)$')
def get_fact(irc, nick, chan, match, args):
    """
    Parses ?A messages to retrieve facts.
    """
    setup_db(irc)

    # Look for a matching key in the database.
    key = match.groups()[0]
    query = irc.db.execute('SELECT * FROM factoids WHERE key = ?', (key,)).fetchone()
    if query is None:
        return None

    # Preprocess returned response. These are all stolen from infobot.
    query = query[2]
    query = query.replace('$nick', nick)
    query = query.replace('$chan', chan)

    # Replace extra randoms first, because $rand1 will be replaced by the $rand
    # replacement below otherwise.
    randoms = set(re.findall(r'\$rand\d', query))
    for random_nick in randoms:
        query = query.replace(random_nick, random.sample(irc.userlist[chan], 1)[0])

    # Do the default random replacement.
    query = query.replace('$rand', random.sample(irc.userlist[chan], 1)[0])

    # Action messages and shit should actually print actions.
    if query.startswith('@a'):
        query = "\01ACTION " + query[2:].strip() + "\01"
        return query

    # Send messages back raw without the connector,
    if query.startswith('@r'):
        return query[2:].strip()

    return '{}: {} '.format(key, query)
