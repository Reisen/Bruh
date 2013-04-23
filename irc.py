"""
    This file implements functions and objects that actual deal with an IRC
    protocol itself. This abstracts it away from the bot.
"""

import socket
from ssl import wrap_socket, SSLError, CERT_NONE, CERT_REQUIRED

class IRC(object):
    """
    This class deals with IRC protocol messages coming from a connection
    object.
    """
    def __init__(self, nickname, connection, server, password = None):
        """Sets up the object so it can communicate with the server"""

        # IRC Specific information that relates to this particular connection.
        # Plugins have access to this data.
        self.nickname = nickname
        self.channel = []
        self.conn = connection
        self.message = ""
        self.server = server

        # Auth if required.
        if password:
            self.send('PASS %s' % password)

        # Set us up as a valid IRC user. Should move this to a plugin as well
        # in the future.
        self.raw('NICK %s\r\n' % nickname)
        self.raw('USER %s %s bruh :%s\r\n' % (nickname, nickname, nickname))

    def parse(self, msg):
        """Parses an IRC message into prefix, command, and arguments as per RFC"""
        if not msg: return None
        msg = msg.strip()

        # [Prefix] is optional, [trailing] is the :End part of the message
        prefix, trailing = '', []

        # Find prefix, command and arguments
        if msg[0] == ':':
            prefix, msg = msg[1:].split(' ', 1)

        if msg.find(' :') != -1:
            msg, trailing = msg.split(' :', 1)
            args = msg.split()
            args.append(trailing)
        else:
            args = msg.split()

        # Get the command from the front of the args list
        command = args.pop(0)
        return prefix, command, args

    def raw(self, message):
        """Send a properly encoded message to the server"""
        message = message.encode('UTF-8')
        print(message)
        self.conn.send(message)

    def send(self, message):
        """Deal with \r\n automatically."""
        self.raw(message + '\r\n')

    def recv(self):
        """
        More explicit way of receiving messages, returning the generator
        returned from __call__ to the caller.
        """
        return self()

    def __call__(self):
        """Parses incoming messages and returns parsed messages as a list."""
        # Assume IRC messages are being sent as UTF-8. If not, then in the case
        # of IRC It's mostly likely because someone sent letters not in the
        # first 127 characters of ASCII, so we can try decoding from
        # iso-latin-1, if that doesn't work, fuck that guy, his client sucks.
        try:
            data = self.conn.recv(1024)
            self.message += data.decode('UTF-8')
        except UnicodeDecodeError:
            self.message += data.decode('iso-8859-1', 'replace')
        except socket.timeout:
            return []

        # Get all the information in the buffer so far. And split it into
        # individual line-broken messages. The last message may not have been
        # fully received yet, so the last message is popped off the stack, and
        # pushed back onto the message buffer to be parsed later when it is
        # ready.
        parsable = self.message.split('\n')
        self.message = parsable.pop()
        parsable = map(self.parse, parsable)

        # Parse the available messages into prefix, command, args form.
        return parsable


def connectIRC(server, port, nick, password = None, ssl = False, ssl_verify = True):
    """Helper for creating new IRC connections"""
    # Create the connection object. If SSL is enabled, we wrap it in an SSL
    # wrapper but otherwise make no distinction. If possible, I am aiming to
    # expose as little information about the connection as I can to the rest of
    # the bot.
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if ssl:
        connection = wrap_socket(connection, cert_reqs = CERT_REQUIRED if ssl_verify else CERT_NONE)

    # Connect and pack the connection into an IRC object to handle the
    # connection and message parsing.
    connection.connect((server, int(port)))
    connection.settimeout(0.1)
    return IRC(nick, connection, server, password)
