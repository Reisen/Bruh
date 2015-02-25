from bruh import command
from drivers.walnut import Walnut


@command('echo')
def echo(irc):
    return 'echo> ' + irc.message


@Walnut.hook('INVITE')
def join_inviter(message):
    return 'JOIN {}'.format(message.args[1])


@Walnut.hook('PRIVMSG')
def bruh(message):
    # TODO: Make core report username. Remove this hardcoding.
    if 'walnut!' == message.args[-1] or 'warlus!' == message.args[-1]:
        return 'PRIVMSG {} :{}!'.format(
            message.args[0],
            message.prefix.split('!')[0]
        )


@Walnut.hook('PING')
def ping(message):
    return 'PONG {}'.format(message.args[-1])
