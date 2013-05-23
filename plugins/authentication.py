"""
    Provide a user registration/login system for more personalised commands,
    such as for saving API keys for more user sensitive plugins. See the linode
    API plugin for example.
"""
import hmac, struct, hashlib, os, base64
from plugins.commands import command


def DF(password, salt, c, dkLen):
    def F(password, salt, c, i):
        # Initial run of U_n
        U = hmac.new(
            password,
            salt + struct.pack(">i", i),
            hashlib.sha512
        ).digest()
        U_n = U

        # Subsequent runs of U_n.
        for n in range(c - 1):
            U = hmac.new(
                password,
                U,
                hashlib.sha512
            ).digest()

            # Perform U_1 ^ U_2 ^ ... ^ U_c operation.
            U_n = bytes(a ^ b for a, b in zip(U_n, U))

        return U_n

    result = b''
    iterations = int(dkLen / hashlib.sha512().digest_size + 1)
    for i in range(iterations):
        T = F(password, salt, c, i + 1)
        result += T

    return result[:dkLen]


def setup_db(irc):
    irc.db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
        );
    ''')
    irc.db.execute('''
        CREATE TABLE IF NOT EXISTS user_properties (
            user_id INTEGER,
            key TEXT UNIQUE,
            value TEXT
        );
    ''')
    irc.db.commit()


@command
def register(irc, nick, chan, msg, args):
    """Register a new user with the bot."""
    setup_db(irc)

    # Users may be dumb and register in a public channel, if they are the best
    # choise is to not register and force them to try again in a PM.
    if chan.startswith('#'):
        return "You seem to be registering in a channel which is public. You should PM me and try again, with a new password people haven't already seen."

    # Generate User's Key.
    salt = os.urandom(64)
    key  = DF(msg.encode('UTF-8'), salt, 1000, 64)
    data = salt + key
    try:
        irc.db.execute('INSERT INTO users (username, password) VALUES (?, ?)', (nick, base64.b64encode(data)))
        irc.db.commit()

        return "Welcome {}. You are now registered. You can authenticate now with .authenticate (In a PM).".format(nick)
    except Exception as e:
        print(e)
        return "You seem to be already registered. Or someone with your nick already registered at least."
