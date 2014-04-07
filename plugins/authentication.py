"""
    Provide a user registration/login system for more personalised commands,
    such as for saving API keys for more user sensitive plugins. See the linode
    API plugin for example.
"""
import hmac, struct, hashlib, os, base64
from plugins import event
from functools import wraps
from plugins import mod

commands = mod.commands

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
            key TEXT,
            value TEXT,
            PRIMARY KEY(user_id, key)
        );
    ''')
    irc.db.commit()


def authenticated(auth_arg):
    # We wrap the wrapper so that we can manipulate the wrappers arguments with
    # additional information.
    def wrap_wrapper(f):
        @wraps(f)
        def auth_wrapper(irc, nick, chan, msg, irc_args, *args, **kwargs):
            # Only allow the command to continue if we're sure the user is already
            # authenticated.
            if irc_args[0] not in irc.auth_list:
                return "You need to be logged in to use this command."

            # The database contains a list of Key/Value pairs related to a user, we
            # populate these as a dictionary here, before the function call, and
            # then provide it as an extra argument to the resulting function.
            userid = irc.db.execute('SELECT * FROM users WHERE username = ?', (nick,)).fetchone()[0]
            upairs = irc.db.execute('SELECT key, value FROM user_properties JOIN users ON users.id = user_id WHERE users.id = ?', (userid,)).fetchall()
            if upairs is None:
                upairs = []

            # Check if we have a list of authentication targets provided by the
            # outer wrapping.
            upairs = dict(upairs)
            if isinstance(auth_arg, list) and upairs.get('Rank', None) not in auth_arg:
                return 'You do not have the right rank to use this command.'

            result = f(irc, nick, chan, msg, irc_args, upairs, *args, **kwargs)

            # Any changes the user made to the dictionary should be updated in the
            # database so that future authed calls see the correct users state.
            for key, value in upairs.items():
                irc.db.execute('INSERT OR REPLACE INTO user_properties VALUES (?, ?, ?)', (
                    userid,
                    key,
                    value
                ))

            irc.db.commit()
            return result

        return auth_wrapper

    if isinstance(auth_arg, list):
        return wrap_wrapper
    else:
        return wrap_wrapper(auth_arg)


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


@commands.command
def logout(irc, nick, chan, msg, args):
    """
    Logout of the bot, ending an authenticated session.
    .logout
    """
    if args[0] not in irc.auth_list:
        return "You aren't logged in, so I can't really log you out."

    irc.auth_list.remove(args[0])
    return "You are now logged out."


@commands.command
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
        return "Syntax: .login <password>"

    try:
        if do_authenticate(irc, nick, msg):
            irc.auth_list.add(args[0])
            return "You're now logged in."

        return "Either your user doesn't exist, or your password is wrong. Check .register for the former."
    except Exception as e:
        print(e)
        return "There was an error logging in. This was an error in the bot itself, please report it."


@commands.command
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


@commands.command
@authenticated(['Admin'])
def modify(irc, nick, chan, msg, args, user):
    """
    Modify or view state stored about another user. Must be an admin.
    .modify <user> <key> [<value>]
    """
    try:
        if not msg:
            return "Syntax: .modify <user> <key> [<value>]"

        # Find user details provided by the command.
        target, key, *value = msg.split(' ', 2)
        userid = irc.db.execute('SELECT * FROM users WHERE username=?', (target,)).fetchone()[0]
        if not userid:
            return 'Couldn\'t find any user named {}.'.format(target)

        # Attempt to fetch current key value, or update key value to the new
        # value provided by the user.
        if value:
            irc.db.execute('INSERT OR REPLACE INTO user_properties VALUES (?, ?, ?)', (userid, key, value[0]))
            return 'Key Changed: {} = {} for {}'.format(key, value[0], target)

        value = irc.db.execute('SELECT * FROM user_properties WHERE user_id = ? AND key = ?', (userid, key)).fetchone()
        value = 'None' if not value else value[2]
        return 'Key Value: {} = {} for {}'.format(key, value, target)

    except ValueError:
        return 'You need to provide a key and a value to make changes. Or at least a key.'

    except Exception as e:
        return 'Error occured modifying user: {}'.format(str(e))


@commands.command
@authenticated
def password(irc, nick, chan, msg, args, user):
    """
    Change the password for your current login.
    .password <new>
    .password <new> <user>
    """
    # Make sure users aren't being dumb enough to login in a channel.
    if chan.startswith('#'):
        return "You are trying to change your password in a public channel. PM me and try again with a password people haven't already seen."

    if not msg:
        return "Syntax: .password <newpassword> [<user>]"

    # If a username was provided, we have to make sure they have the right rank
    # to modify other users.
    password, *username = msg.split(' ', 1)
    if username and user.get('Rank', None) != 'Admin':
        return "You need to be an admin to change other users passwords."

    # If the username isn't set at this point, set it to the current user as
    # that is the only user they should have permission to modify.
    if not username:
        username.append(nick)

    # Generate new hash to store for the user's password.
    salt = os.urandom(64)
    key  = DF(password.encode('UTF-8'), salt, 1000, 64)
    data = salt + key
    irc.db.execute('UPDATE users SET password = ? WHERE username = ?', (base64.b64encode(data), username[0]))
    irc.db.commit()

    return "Successfully changed password."


@commands.command
def register(irc, nick, chan, msg, args):
    """
    Register a new user with the bot.
    .register <password>
    """
    setup_db(irc)

    # Users may be dumb and register in a public channel, if they are the best
    # choise is to not register and force them to try again in a PM.
    if chan.startswith('#'):
        return "You seem to be registering in a channel where people can see your password. You should PM me and try again, with a new password people haven't already seen."

    # Check arguments were actually given.
    if not msg:
        return "Syntax: .register <password>"

    # Generate User's Key.
    salt = os.urandom(64)
    key  = DF(msg.encode('UTF-8'), salt, 1000, 64)
    data = salt + key
    try:
        irc.db.execute('INSERT INTO users (username, password) VALUES (?, ?)', (nick, base64.b64encode(data)))
        irc.db.commit()

        return "You are now registered as {}. You can login now with .login <password>.".format(nick)

    except Exception as e:
        return "You are already registered. Try logging in with .login <password>."
