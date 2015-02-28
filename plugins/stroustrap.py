import random
from bruh import command


wisdom_lines = []
with open('data/wisdom') as f:
    wisdom_lines = f.readlines()


@command('stroustrup')
@command('wisdom')
@command('s')
def keybutt(irc):
    output = random.choice(wisdom_lines)

    if irc.message:
        try:
            index = int(irc.message)
            return '[{}]: {}'.format(
                index,
                wisdom_lines[index]
            )

        except Exception as e:
            print(e)

    index  = wisdom_lines.index(output)

    return '[{}]: {}'.format(
        index,
        output
    )
