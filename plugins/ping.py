from bruh import command, regex
from walnut.drivers import Walnut


@command('echo')
def echo(irc):
    return 'echo: ' + irc.message


@Walnut.hook('INVITE')
def join_inviter(message):
    return 'JOIN {}'.format(message.args[1])


@Walnut.hook('PING')
def ping(message):
    return 'PONG {}'.format(message.args[-1])
