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
    """This class deals with IRC protocol messages."""

    def __init__(self, nickname, connection, server):
        """Sets up the object so it can communicate with the server"""

        # IRC Specific information that relates to this particular connection.
        self.nickname = nickname
        self.channel = []
        self.conn = connection
        self.messages = ""
        self.server = server

        # Pass the IRC details the server needs
        self.raw('PASS %s\r\n' % '*')
        self.raw('NICK %s\r\n' % nickname)
        self.raw('USER %s %s bruh :%s\r\n' %
            ('Br', 'Uh', 'Bruh'))


    def raw(self, message):
        """Send a properly encoded message to the server"""
        message = message.encode('UTF-8')
        self.conn.send(message)


    def __call__(self):
        """Parses incoming messages from the connection and yields them as a generator"""
        self.messages += self.conn.recv(1024).decode('UTF-8')

        # Get the parsable messages, and store what isn't fully received
        # back into self.messages for later
        parsable = self.messages.split('\n')
        self.messages = parsable.pop()

        # Parse the available messages
        for message in parsable:
            message = parse(message)
            yield message


def connectIRC(server, port, nick):
    """Create a new IRC connection"""

    # Create a connection to the server
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.connect((server, port))

    # Create an IRC object to handle the protocol
    return IRC(nick, connection, server)
