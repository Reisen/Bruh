"""
    Commands
    --------
    Creates two decorators that are used by other plugins to create commands,
    and a single 'help' command for providing help by returning a commands
    docstring.

    The first decorator creates a command based on the function name, commands
    are passed 5 arguments, the irc server that called it, the nick, channel,
    the users input and the parsed IRC message.

    @command
    def example(irc, nick, channel, msg, args):
        pass

    Commands can also be used shorthand if they aren't ambiguous, .exam will
    call the above function just fine.

    Regular Expressions
    -------------------
    The second decorator will allow a regex pattern to be matched, these
    functions receive regular expression match objects.

    @regex('\?(\w+)')
    def f(irc, nick, channel, match, args):
        pass
"""
import re
import time
from functools import wraps
from plugins import event
from traceback import print_exc

# Stored commands. Command names mapped to function objects.
commandlist = {}
patternlist = {}

def command(f):
    """This decorator creates new command entry."""
    # If the argument to the function is a list, then the decorator has
    # been called with a list of alternative command names like so:
    #
    #   @command(['g', 'gog'])
    #
    # This list is a list of commands that must also explicitly match the
    # command. This helps resolve naming conflicts, for example: the github
    # plugin registers .github, and the google plugin registers .google -
    # however 99% of the time someone doing .g will want to google, but because
    # of Bruh's matching, this will conflict and the bot will ask which plugin
    # the user wanted. Providing an explicit short name to the google plugin
    # with `@command(['g'])` solves this.
    if isinstance(f, list):
        def shortname_wrapper(g):
            for shortname in f:
                commandlist[shortname] = g

            commandlist[g.__name__] = g
            return g

        return shortname_wrapper

    # When the argument is a function then the decorator has been called with
    # no short names and we just add directly.
    commandlist[f.__name__] = f
    return f


def regex(pattern):
    """This decorator creates a new pattern matching entry."""
    def wrapper(f):
        patternlist[pattern] = f
        return f

    return wrapper


def commands(irc, prefix, command, args):
    """
    This function expects a parsed IRC message as input. This function assumes
    nothing about the input, and returns a string that it expects to be sent to
    the output. This means this function can be called with fake data, and the
    result doesn't even have to be printed back to IRC.

    The function can be invoked at any time anywhere to emulate functions being
    called by users. The most obvious use is simply piping IRC input into it,
    as done in this module by `command_forwarder`.

    This function also automatically evaluates piped commands, a single call to
    this function may potentially invoke several modules.
    """
    # Ignore empty messages, and messages consisting of only the command dot.
    if len(args[1]) < 2:
        return None

    # Find the users nick, passed to @command functions.
    nick = prefix.split('!')[0]

    # Find the channel the message was received from, also passed to @commands
    chan = args[0] if args[0].startswith('#') else prefix.split('!')[0]

    # The function doesn't assume the input is in any particular format, if the
    # input isn't a command, then we attempt here to find any regex patterns
    # that match and pass control to them.
    command_prefix = irc.config.get('prefix', '.')
    if args[1][0] != command_prefix:
        for pattern, callback in patternlist.items():
            # Replace matching configuration options.
            for item in irc.server:
                pattern = pattern.replace('$' + item, str(irc.server[item]))

            # Try and match the newly substituted pattern. For example, the
            # pattern '$nick!' after previous replacement may now be 'bruh!'
            # which is used against the message.
            match = re.search(pattern, args[1])
            if match is not None:
                return callback(irc, nick, chan, match, args)

        return None

    # Split arguments into pipeable pieces, using '|' characters found directly
    # before another command as the splitting point. This is a pretty hairy
    # regular expression, maybe could be done cleaner at some point.
    pieces = re.findall(r'\{0}(.*?)(?:\|\s*(?=\{0})|$)'.format(command_prefix), args[1])

    output = ""
    for item in pieces:
        cmd, *input = item.strip().split(' ', 1)

        # Check the input to see if it contains any substitutions, and run them
        # before the command itself is run.
        if input:
            substitutions = re.findall(r'(\$\{([^\}]+)\})', input[0])

            # For each substitution, we sandbox and run the substituted command.
            for substitution in substitutions:
                replace_text, cmd_string = substitution
                sub_cmd, *sub_input = cmd_string.strip().split(' ', 1)

                # Setup the sandboxed environment.
                sandbox_args = args[:]
                sandbox_args[1] = sub_input[0] if sub_input else ''

                # Find command used in substitution.
                possibilities = []
                for candidate in commandlist:
                    if candidate.startswith(sub_cmd): possibilities.append(candidate)

                if len(possibilities) == 0:
                    return "Substitution command '{}' didn't match anything".format(sub_cmd)

                if len(possibilities) > 1:
                    return "Substitution command '{}' matched all of the following: {}".format(str(possibilities)[1:-1])

                replacement = commandlist[possibilities[0]](irc, nick, chan, sandbox_args[1], (prefix, command, sandbox_args))
                input[0] = input[0].replace(replace_text, replacement)

        # Create a fake args environment for the command based on current args,
        # this stops plugins from trashing the default args. If we're piping to
        # new commands, we might also want to modify the environment being
        # passed to a plugin to appear as though just that one command has been
        # called.
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
            # Search for partial matches.
            possibilities = []
            for candidate in commandlist:
                if candidate.startswith(cmd): possibilities.append(candidate)

            # When no commands are found...
            if len(possibilities) == 0:
                return None

            # When more than one potential command is found...
            if len(possibilities) > 1:
                irc.notice(nick, 'Be more specific, the following matched: {}'.format(', '.join(possibilities)))
                return None

            # The output of the last command is the input to the next one, if
            # there is no next command, this is returned to the user.
            output = commandlist[possibilities[0]](irc, nick, chan, sandbox_args[1], (prefix, command, sandbox_args))

    if output is not None:
        return output[:400]


@event('PRIVMSG')
def command_forwarder(irc, prefix, command, args):
    """
    This acts as the actual PRIVMSG handler, the reason for this is that it
    allows `commands` to return a message instead of using irc.reply, this also
    means that `commands` can be called manually to simulate a command being
    called.
    """
    try:
        output = commands(irc, prefix, command, args)
        if output is not None:
            irc.reply(output)

    except:
        print_exc()
        return None


@command
def help(irc, nick, chan, msg, args):
    """
    Get help about a command. See http://morphism.org/walnut/ for a command list and more info.
    .help <command>         - Get help about a command.
    .help <command> detail  - Get the longer, more detailed help text.
    .help list              - List all registered commands.
    """
    # If no plugin is given, default to this plugin, and print help about the
    # help command itself.
    if msg == '':
        msg = 'help'

    # Try and get the help information by looking up the commands docstring
    # from the command dictionary.
    try:
        cmd = msg.split(' ')

        # Print out currently installed commands if 'list' is the command. Any
        # command starting with an underscore are hidden.
        if cmd[0] == 'list':
            output = "Commands: "
            commands = [command for command in commandlist.keys() if not command.startswith('_')]
            commands = sorted(commands)
            commands = ', '.join(commands)

            return output + commands

        # Fetch the commands docstring.
        info = commandlist[cmd[0]].__doc__.strip().split('\n')

        # If the user supplied 'full' to their help, we should notice them
        # instead as the help could be long from long help messages.
        if len(cmd) > 1 and cmd[1] == 'full':
            for line in info:
                irc.notice(nick, line.strip())
                time.sleep(0.1)

            return None

    except KeyError:
        return "Command not found."

    except AttributeError:
        return "This command has no help information."

    return info[0].strip()
