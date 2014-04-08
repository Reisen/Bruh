"""
    Generate markov chains from the text stored in data/markov.txt
"""
import os
import string
from random import randrange, choice
from plugins import event, mod

hook = mod.hook
auth = mod.auth

# Markov state. All strings generated from these.
markovc = {}
markov_keys = []

def reload_markov():
    global markovc, markov_keys
    markovc = {}
    markov_keys = []

    try:
        with open('data/markov.txt', 'r+', encoding='utf-8') as f:
            punctuation = string.punctuation.replace('\'', '')
            punctuation = {ord(c): None for c in punctuation}
            word_1 = ""
            word_2 = word_1

            for line in f:
                for word in line.split():
                    word   = word.translate(punctuation).lower()
                    word_1 = word_1.translate(punctuation).lower()
                    word_2 = word_2.translate(punctuation).lower()

                    markovc.setdefault((word_1, word_2), []).append(word)
                    word_1, word_2 = word_2, word

            markov_keys = list(markovc.keys())

    except Exception as e:
        f = open('data/markov.txt', 'w')
        f.close()


@event('BRUH')
def initialize_markov(irc):
    reload_markov()


@hook.command
@auth.authenticated(['Admin', 'Moderator'])
def chain(irc, nick, chan, msg, args, user):
    reload_markov()
    return 'Reloaded markov chain.'


def markov_generate(seed = None):
    # Find the seed to start building the Markov generator from. Can be either
    # user chosen or random.
    if not seed:
        word_1, word_2 = choice(markov_keys)
    else:
        word_1, word_2 = seed

    # Current state.
    output = '{} {} '.format(word_1.capitalize(), word_2)

    # Generate text from the Markov chain. Also do some rudimentary checking on
    # words to check if we're inside a quote or already at the end of a
    # sentence to back out early.
    for text in range(randrange(10, 20)):
        # Find random word.
        try:
            word = choice(markovc[(word_1, word_2)])
            output += word + ' '
            word_1, word_2 = word_2, word
        except:
            word_1, word_2 = choice(markov_keys)

    # Do all fixups that make the sentence seem more legitimate.
    output = output.strip()
    words  = output.split()

    if words[-1] in ['and', 'or', 'either', 'otherwise', 'the', 'a', 'from', 'very', 'to', 'there', 'therefore', 'he', 'she', 'they', 'I']:
        output = " ".join(words[:-1])

    return output + '.'


@hook.command
def markov(irc, nick, chan, msg, args):
    try:
        word_1, word_2, *rest = msg.split(' ', 2)
        return markov_generate((word_1, word_2))

    except Exception as e:
        return markov_generate()
