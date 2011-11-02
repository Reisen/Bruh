"""
    Creates three decorators that are used by other plugins to create commands,
    and a single 'help' command for providing help about particular commands by
    sending docstrings to the user. Multiline docstring support works by only
    sending the first line, unless the user requests 'all'.

    The first decorator creates a command based on the function name, commands
    are passed 4 arguments, the irc server that called it, the nick, channel,
    the users input and the parsed IRC message.

    @command
    def example(irc, nick, channel, msg, args):
        pass

    This will create a usable command: .example <arguments> in chat. The bot
    automatically matches shortened commands, so .exam will also call this
    function, unless more than one command matches.


    The second decorator will allow a regex pattern to be matched, these
    functions receive regular expression match objects.

    @regex('\?(\w+)')
    def f(irc, nick, channel, match, args):
        pass

    The final decorator will allow a plugin to receive ALL messages that are
    being parsed. This is similar to just hooking @event('PRIVMSG'), except the
    command plugin will parse nick/channel/msg parts so that the function
    prototype is consistent.
"""

from plugins.bruh import event
import re
import time

commandlist = {}
patternlist = []

def command(f):
    """This decorator creates new command entry."""
    commandlist[f.__name__] = f
    return f


def regex(pattern):
    """This decorator creates a new pattern matching entry."""
    def wrapper(f):
        patternlist.append((pattern, f))
        return f

    return wrapper


def commands(irc, prefix, command, args):
    """
    This command hooks message events, and acts as a second layer of plugin
    dispatching depending on the command. This wrapper also provides the
    ability to pipe commands to each other, and match regular expressions.
    """

    # Find the users nick, useful enough in plugins that this can be passed as
    # an extra argument.
    nick = prefix.split('!')[0]

    # Find the channel the message was received from, also useful in commands.
    chan = args[0] if args[0].startswith('#') else prefix.split('!')[0]

    # If messages don't start with a command character, attempt regex parsing
    # instead.
    if args[1][0] != '!':
        for pattern, callback in patternlist:
            match = re.search(pattern, args[1])
            if match is not None:
                output = callback(irc, nick, chan, match, args)

                if output is not None:
                    return output

                return None
        else:
            return None

    # Split arguments into pipeable pieces, using '|' characters found directly
    # before another command as the splitting point.
    pieces = re.findall(r'!(.*?)(?:\|\s*(?=!)|$)', args[1])

    output = ""
    for item in pieces:
        cmd, *input = item.strip().split(' ', 1)

        # Create a fake args environment for the command based on current args,
        # this stops plugins from trashing the default args, and also allows
        # modifying of the args submitted to the plugin.
        sandbox_args = args[:]

        # The output of the last command is appended to the input of the next
        # command, this is done in the fake args environment.
        if len(input) > 0 and output is not None:
            sandbox_args[1] = (input[0] + " " + output).strip()
        else:
            sandbox_args[1] = output

        # Find the plugin to call. If it isn't in the list, then we search the
        # entire list for partial matches.
        if cmd in commandlist:
            output = commandlist[cmd](irc, nick, chan, sandbox_args[1], (prefix, command, sandbox_args))

        else:
            # Search for possible commands
            possibilities = []
            for candidate in commandlist:
                if candidate.startswith(cmd): possibilities.append(candidate)

            # When no commands are found...
            if len(possibilities) == 0:
                return "Didn't find any commands like '%s'" % cmd

            # When more than one potential command is found...
            if len(possibilities) > 1:
                return "Which did you want?  %s" % str(possibilities)[1:-1]

            # The output of the last command is the input to the next one, if
            # there is no next command, this is returned to the user.
            output = commandlist[possibilities[0]](irc, nick, chan, sandbox_args[1], (prefix, command, sandbox_args))

    if output is not None:
        return output[:400]


@event('PRIVMSG')
def command_forwarder(irc, prefix, command, args):
    """
    This acts as the actual PRIVMSG handler, the reason for this is that it
    allows `commands` to return a message instead of using irc.reply, this
    also means that `commands` can be called manually to simulate a command
    being called.
    """
    output = commands(irc, prefix, command, args)
    if output is not None:
        irc.reply(output)


@command
def help(irc, nick, chan, msg, args):
    """
    Get help about a command.
    .help <command>
    .help <command> full
    .help list
    """
    if msg == '':
        msg = 'help'

    # Try and get the help information by looking up the commands docstring
    # from the command dictionary.
    try:
        cmd = msg.split(' ')

        # Print out currently installed commands if 'list' is the command.
        if cmd[0] == 'list':
            output = "Commands: "
            for item in commandlist.keys():
                output += item + ', '

            return output[:-2]

        # Fetch the commands docstring.
        info = commandlist[cmd[0]].__doc__.strip().split('\n')

        # If the user supplied 'full' to their help, we should notice them
        # instead as the help could be long from long help messages.
        if len(cmd) > 1 and cmd[1] == 'full' or cmd[0] == 'help':
            for line in info:
                irc.notice(nick, line.strip())
                time.sleep(0.1)

            return None

    except KeyError:
        return "Command not found."

    except AttributeError:
        return "This command has no help information."

    return info[0].strip()
