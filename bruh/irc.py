"""
    This file implements functions and objects that actual deal with an IRC
    connection itself. This abstracts it away from the bot.
"""

import socket

def parse(msg):
    """Parses an IRC message into prefix, command, and arguments as per RFC"""
    if not msg:
        return None

    msg = msg.strip()

    # [Prefix] is optional, [trailing] is the :End part of the message
    prefix = ''
    trailing = []

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


class IRC(object):
    """
    This class deals with IRC protocol messages coming from a connection
    object.
    """

    def __init__(self, nickname, connection, server):
        """Sets up the object so it can communicate with the server"""

        # IRC Specific information that relates to this particular connection.
        # Plugins have access to this data.
        self.nickname = nickname
        self.channel = []
        self.conn = connection
        self.message = ""
        self.server = server

        # Set us up as a valid IRC user. Should move this to a plugin as well
        # in the future.
        self.raw('NICK %s\r\n' % nickname)
        self.raw('USER %s %s bruh :%s\r\n' %
            ('Br', 'Uh', 'Bruh'))

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
        """Parses incoming messages and yields them as a generator"""
        # Assume IRC messages are being sent as UTF-8. If they aren't, It's
        # likely to be decodable as a subset anyway.
        self.message += self.conn.recv(1024).decode('UTF-8')

        # Get all the information in the buffer so far. And split it into
        # individual line-broken messages. The last message may not have been
        # fully received yet, so the last message is popped off the stack, and
        # pushed back onto the message buffer to be parsed later when it is
        # ready.
        parsable = self.message.split('\n')
        self.message = parsable.pop()

        # Parse the available messages into prefix, command, args form.
        for message in parsable:
            yield parse(message)


def connectIRC(server, port, nick):
    """Helper for creating new IRC connections"""
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.connect((server, port))

    # Pack the connection into an IRC object to handle the connection.
    return IRC(nick, connection, server)
