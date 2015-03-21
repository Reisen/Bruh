import re
from drivers.walnut import Walnut
from bruh import r, c as commands, e as expressions, s as sinks


class IRCMessage:
    def __init__(self, message = None):
        if message:
            self.nick    = message.prefix.split('!')[0]
            self.channel = message.args[0] if message.args[0].startswith('#') else self.nick
            self.network = message.parent.frm
            self.message = message.args[-1]
            self.key     = '{}:{}'.format(self.network, self.channel)

    def raw(self, message):
        Walnut.ipc(
            'proxy',
            self.network,
            'forward',
            message
        )


@Walnut.method('command')
def handle_command(message):
    if message.to not in commands:
        return None

    db_key = '{}:{}'.format(message.args[-3], message.args[-2])
    prefix = r.get('{}:prefix'.format(db_key))
    prefix = prefix.decode('UTF-8') if prefix else '.'

    # Extract and execute the command in question.
    msg      = message.payload.decode('UTF-8')
    pieces   = re.findall(r'\{0}(.*?)(?:\|\s*(?=\{0})|$)'.format(prefix), msg)
    c, *args = pieces[0].split(' ', 1)

    # Unless the command is blacklisted that is.
    if r.sismember('{}:blacklist'.format(db_key), c):
        pieces = []
        result = 'The {} command has been blacklisted in this channel.'.format(c)

    else:
        env         = IRCMessage()
        env.key     = db_key
        env.nick    = message.args[-1]
        env.channel = message.args[-2]
        env.network = message.args[-3]
        env.message = args[0] if args else ''

        result = commands[message.to](env)
        result = result if result else ''

    # If there are still commands to process, carry on forwarding.
    if len(pieces) > 1:
        # Append the result to the end of the next command in the chain.
        pieces[1] = pieces[1] + ' ' + result
        next_cmd  = pieces[1].split(' ', 1)[0]
        full_cmd  = prefix + ('|' + prefix).join(pieces[1:])

        Walnut.ipc(
            'command',
            next_cmd,
            'command',
            full_cmd,
            message.args[-3],
            message.args[-2],
            message.args[-1],
        )

    elif result:
        Walnut.ipc(
            'proxy',
            message.args[-3],
            'forward',
            'PRIVMSG {} :{}'.format(
                message.args[-2],
                result
            )
        )


@Walnut.hook('PRIVMSG')
def privmsg_handler(message):
    irc = IRCMessage(message)

    outputs = []

    # Prefixed Commands
    # --------------------------------------------------------------------------
    prefix = r.get(irc.key + ':prefix')
    prefix = prefix.decode('UTF-8') if prefix else '.'
    if irc.message.startswith(prefix) and len(irc.message) >= 2:
        pieces = re.findall(r'\{0}(.*?)(?:\|\s*(?=\{0})|$)'.format(prefix), irc.message)
        Walnut.ipc(
            'command',
            pieces[0].split(' ', 1)[0],
            'command',
            irc.message,
            irc.network,
            irc.channel,
            irc.nick
        )

    # Sinks
    # --------------------------------------------------------------------------
    for callback in sinks:
        result = callback(irc)
        if result:
            outputs.append('PRIVMSG {} :{}'.format(
                irc.channel,
                result
            ))

    # Regular Expressions
    # --------------------------------------------------------------------------
    for expression, callback in expressions.items():
        result = re.search(expression, irc.message, re.I)
        if not result:
            continue

        result = callback(irc, result)
        if result:
            outputs.append('PRIVMSG {} :{}'.format(
                irc.channel,
                result
            ))

    return outputs
