import re
from drivers.walnut import Walnut
from bruh import r, c as commands


@Walnut.method('command')
def handle_command(message):
    if message.to in commands:
        db_key = '{}:{}'.format(message.args[-3], message.args[-2])
        prefix = r.get('{}:prefix'.format(db_key))
        prefix = prefix.decode('UTF-8') if prefix else '!'

        # Extract and execute the command in question.
        msg      = message.payload.decode('UTF-8')
        pieces   = re.findall(r'\{0}(.*?)(?:\|\s*(?=\{0})|$)'.format(prefix), msg)
        c, *args = pieces[0].split(' ', 1)

        # Unless the command is blacklisted that is.
        if r.sismember('{}:blacklist'.format(db_key), c):
            pieces = []
            result = 'The {} command has been blacklisted in this channel.'.format(c)

        else:
            class IRC: pass
            env         = IRC()
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
def command_dispatcher(message):
    msg    = message.args[-1]
    prefix = r.get('{}:{}:prefix'.format(message.parent.frm, message.args[0]))
    prefix = prefix.decode('UTF-8') if prefix else '!'

    # Escape early for messages that only consist of the command character or
    # are not commands at all.
    if not msg.startswith(prefix) or len(msg) < 2:
        return None

    chan   = message.args[0]
    chan   = chan if chan[0].startswith('#') else message.prefix.split('!')[0]
    pieces = re.findall(r'\{0}(.*?)(?:\|\s*(?=\{0})|$)'.format(prefix), msg)

    # Dispatch the IPC call.
    Walnut.ipc(
        'command',
        pieces[0].split(' ', 1)[0],
        'command',
        msg,
        '0',
        message.parent.frm,
        chan,
        message.prefix.split('!')[0]
    )
