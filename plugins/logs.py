"""
    Implement Logging for bots to use. Logs store information about which
    plugins were involved in logging as well.
"""

import inspect
from plugins import event

# Log Levels
WARNING = 0
IMPORTANT = 1
ERROR = 2

def setup_db(irc):
    irc.db.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY,
            plugin TEXT,
            message TEXT,
            severity INTEGER
        )
    ''')
    irc.db.commit()


def log(irc, message, severity = WARNING):
    # Get the current status of the calling plugin from the stack.
    setup_db(irc)

    # Find out who called us and from what function.
    s = inspect.stack()[1]
    plugin_name = s[1].rsplit('/', 1)[1].split('.')[0]

    irc.db.execute('INSERT INTO logs (plugin, message, severity) VALUES (?,?,?)', (
        plugin_name,
        '{}-{}: {}'.format(s[3], s[2], message),
        severity
    ))
