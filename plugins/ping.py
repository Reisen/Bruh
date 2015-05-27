from bruh import command, regex
from walnut.drivers import Walnut


@command('echo')
def echo(irc):
    return 'echo: ' + irc.message


@Walnut.hook('INVITE')
def join_inviter(message):
    return 'JOIN {}'.format(message.args[1])


@Walnut.hook('PRIVMSG')
def ctcps(message):
    if '\x01' not in message.args[-1]:
        return None

    ctcp = message.args[-1].replace('\x01', '')
    ctcp, *ctcp_parts = ctcp.split(' ', 1)
    target = message.prefix.split('!', 1)[0]

    try:
        if ctcp != 'ACTION':
            print('Here we go')
            return 'NOTICE {} :\01{}\01'.format(target, {
                'VERSION': lambda: 'VERSION Bruh 1.0 (http://github.com/Reisen/Bruh)',
                'SOURCE':  lambda: 'SOURCE http://github.com/Reisen/Bruh',
                'PING':    lambda: 'PING {}'.format(ctcp_parts[0]),
            }[ctcp]())

    except Exception as e:
        return None
