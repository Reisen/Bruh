import os
import sys
import subprocess
from bruh import command
from plugins.userlist import auth

@command('pull')
@auth
def pull(irc):
    try:
        output = subprocess.check_output(['git', 'pull']).decode('UTF-8')
        output = output.split('\n')[0]
        output = output.strip()
        return output

    except subprocess.CalledProcessError as e:
        return 'git pull failed: ' + e.output


@command('restart')
@auth
def restart(irc):
    args = sys.argv[:]
    args.insert(0, sys.executable)
    os.execv(sys.executable, args)
    return 'Failed.'
