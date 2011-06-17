"""
    Creates two decorators that are used by other plugins to create
    commands. The first creates a command based on the function name:

    @command
    def f(...):
        pass

    Will create a usable command: .f <arguments> in chat.


    The second decorator will allow a regex pattern to be matched:

    @regex('\?(\w+)')
    def f(...)
        pass

    This creates a function that will receive regex match objects for
    It's 'args' instead of a standard IRC <trailing> message.


    Finally the function defines a single @command, help, that provides
    information about other commands that are created
"""

from plugins.bruh import event
import re
import time

commandlist = {}
patternlist = []

def command(f):
    """Create new command entry"""
    commandlist[f.__name__] = f


def regex(pattern):
    """Create new regex pattern matching command"""
    def target(f):
        patternlist.append((pattern, f))

    return target


@event('PRIVMSG')
def commands(irc, prefix, command, args):
    """Provide other commands with .command style hooks"""
    if args[1][0] != '!':
        return None

    # Split arguments into pipeable pieces
    position = 0
    pieces = []
    for item in re.finditer(r'\|\s*!', args[1]):
        pieces.append(args[1][position:item.start()].strip())
        position = item.start() + 1

    # Append command in case of only one command, if more than one command,
    # this also makes sure the last command is appended properly.
    pieces.append(args[1][position:].strip())

    output = ""
    for item in pieces:
        # Get command information, starting with command name
        info = item.split(' ', 1)
        name = info[0][1:]

        # Create a fake args environment for the command based on current args
        environment = args[:]

        # Add the users nick to arguments (nonstandard, but will be useful)
        environment.append(prefix.split('!')[0])

        # If more than just the command was invoked, then the command should
        # receive the extra information as if it were the message itself, also
        # appending any output from the last command to the message. For example:
        # assuming '.test' outputs 'hello', then:
        #
        # .test | .reverse
        #
        # Should create: message = '' + 'hello', we do this by buffering each
        # commands output in 'output', and appending it on each loop.
        if len(info) > 1:   environment[1] = info[1] + " " + output
        else:               environment[1] = output

        # Find plugin to call, this allows partially named commands to work
        # such as .wik to .wikipedia
        if name in commandlist:
            output = commandlist[name](irc, prefix, command, environment)
        else:
            # Search for possible commands
            possibilities = []
            for possible in commandlist:
                if possible.startswith(name): possibilities.append(possible)

            # When no commands are found...
            if len(possibilities) == 0:
                irc.reply("Didn't find any commands like '%s'" % name)
                return None

            # When more than one potential command is found...
            if len(possibilities) > 1:
                irc.reply("Which did you want?  %s" % str(possibilities)[1:-1])
                return None

            output = commandlist[possibilities[0]](irc, prefix, command, environment)


        # Invoke plugin
        if output is None:
            output = ''

    if output != '':
        irc.reply(output)


@command
def help(irc, prefix, command, args):
    """
    Get help about a command.
    .help <command>
    .help <command> full
    .help list
    """
    if args[1] == '':
        return "Which command do you want help with?"


    # Try and get the help information from the command
    # dictionary
    try:
        cmd = args[1].split(' ')

        # Print out currently installed commands if 'list' is the command
        if cmd[0] == 'list':
            output = "Commands: "
            for item in commandlist.keys():
                output += item + ', '

            return output[:-2]

        # Otherwise load the command from the pluginlist
        info = commandlist[cmd[0]].__doc__.strip().split('\n')
    except KeyError:
        return "Command not found"

    # Notice the user if they want the full information
    if len(cmd) > 1 and cmd[1] == 'full' or cmd[0] == 'help':
        for line in info:
            irc.notice(args[2], line.strip())
            time.sleep(0.1)

        return None

    return info[0].strip()


@command
def test(irc, prefix, command, args):
    return "Received: " + args[1]


@command
def another(irc, prefix, command, args):
    return "Another Received: " + args[1]
