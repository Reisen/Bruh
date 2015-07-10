from bruh import command, regex
from walnut.drivers import Walnut


@command('help')
@command('h')
def help(irc):
    return 'Help: http://bot.morphism.org/guide/'
