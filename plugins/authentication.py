"""
    Provide a user registration/login system for more personalised commands,
    such as for saving API keys for more user sensitive plugins. See the linode
    API plugin for example.
"""
import hmac, struct, hashlib, os, base64
from plugins import event
from functools import wraps
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


@event('BRUH')
def setup_auth(irc):
    # List of currently authed users. This is the users full username prefix, such
    # as: Bob!Bob@bobsicles.com
    irc.auth_list = set()


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


def authenticated(f):
    @wraps(f)
    def auth_wrapper(irc, nick, chan, msg, irc_args, *args, **kwargs):
        # Only allow the command to continue if we're sure the user is already
        # authenticated.
        if irc_args[0] not in irc.auth_list:
            return "You need to be logged in to use this command. Check .help login, or .help register"

        # The database contains a list of Key/Value pairs related to a user, we
        # populate these as a dictionary here, before the function call, and
        # then provide it as an extra argument to the resulting function.
        userid = irc.db.execute('SELECT * FROM users WHERE username = ?', (nick,)).fetchone()[0]
        pairs  = dict(irc.db.execute('SELECT key, value FROM user_properties JOIN users ON users.id = user_id WHERE users.id = ?', (userid,)).fetchall())

        result = f(irc, nick, chan, msg, irc_args, pairs, *args, **kwargs)

        # Any changes the user made to the dictionary should be updated in the
        # database so that future authed calls see the correct users state.
        for key, value in pairs.items():
            irc.db.execute('INSERT OR REPLACE INTO user_properties VALUES (?, ?, ?)', (
                userid,
                key,
                value
            ))
        irc.db.commit()

        return result

    return auth_wrapper


def do_authenticate(irc, nick, password):
    # Check to make sure the user actually exists first. If not we can warn the
    # user and leave early.
    user = irc.db.execute('SELECT * FROM users WHERE username = ?', (nick,)).fetchone()
    if not user:
        return False

    # Otherwise, we can go ahead and verify. Each user stores a 128 byte
    # authentication token in the database consisting of a salt and their
    # generated key.
    data = base64.b64decode(user[2])
    salt = data[:64]
    key  = data[64:]

    # Use the stored salt and their provided password to see if we get the same
    # stored key, if so authentication was successful.
    return DF(password.encode('UTF-8'), salt, 1000, 64) == key


@command
def logout(irc, nick, chan, msg, args):
    """
    Logout of the bot, ending an authenticated session.
    .logout
    """
    if args[0] not in irc.auth_list:
        return "You aren't logged in, so I can't really log you out."

    irc.auth_list.remove(args[0])
    return "You are now logged out."


@command
def login(irc, nick, chan, msg, args):
    """
    Authenticate with the bot.
    .login <password>
    """
    setup_db(irc)

    if args[0] in irc.auth_list:
        return "You're already logged in!"

    # Catch common problems while authing and warn the user. First we stop them
    # authing publicly.
    if chan.startswith('#'):
        return "You just tried to login in a channel, publicly. You should try and auth again in a PM, then change your password."

    # Also make sure they actually provided their password.
    if not msg:
        return "You need to provide a passworth when you login."

    try:
        if do_authenticate(irc, nick, msg):
            irc.auth_list.add(args[0])
            return "You're now logged in."

        return "Either your user doesn't exist, or your password is wrong."
    except Exception as e:
        print(e)
        return "There was an error logging in. This was an error in the bot, please report it."


@command
@authenticated
def destroy(irc, nick, chan, msg, args, user):
    """
    Removes your user from the database and destroys all data associated with it.
    .destroy <password>
    """
    userid = irc.db.execute('SELECT * FROM users WHERE username=?', (nick,)).fetchone()[0]
    irc.db.execute('DELETE FROM user_properties WHERE user_id=?', (userid,))
    irc.db.execute('DELETE FROM users WHERE id=?', (userid,))
    irc.db.commit()
    irc.auth_list.remove(args[0])
    return "Your user has been murdered."


@command
def register(irc, nick, chan, msg, args):
    """
    Register a new user with the bot.
    .register <password>
    """
    setup_db(irc)

    if not msg:
        return "You can't register without providing a password."

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

        return "You are now registered as {}. You can login now with .login <password>.".format(nick)
    except Exception as e:
        print(e)
        return "You seem to be already registered. Or someone with your nick already registered at least."
