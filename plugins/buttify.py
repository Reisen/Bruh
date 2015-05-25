try:
    from hyphen import Hyphenator, dictools
    from bruh import command, sink
    from walnut.drivers import Walnut
    from collections import defaultdict
    from random import random, choice, randrange

    for lang in ['de_GB']:
        if not dictools.is_installed(lang):
            dictools.install(lang)

    split = Hyphenator('en_US')
    memes = defaultdict(lambda: 'butt')
    prob  = 0.0005

    def buttify_word(word, meme):
        try:
            # Find a buttable word and piece to work with.
            pieces = split.syllables(word)
            if not pieces:
                return word

            syllable = randrange(0, len(pieces))
            butt_target = pieces[syllable]

            # Punctuation should be ignored. Otherwise sentence structure is lost.
            # So 'however.' becomes 'howbutt.' and not 'howbutt'
            if butt_target[-1] in '.,!?;\'':
                butt_target = butt_target[:-1]

            # Fix up any contextual information around the butt, any 's' at the end
            # of the word should keep the s, so that completes becomes 'combutts'
            # and not 'combutt'.
            if butt_target[-1] == 's' and meme[-1] != 's':
                butt_target = butt_target[:-1]

            # Words with the same letter at the start of the next symbol as the
            # word we're replacing with should not be replaced, so that battle
            # becomes 'buttle', and not 'butttle'.
            if syllable + 1 < len(pieces) and pieces[syllable + 1][0] == meme[-1]:
                meme = meme[:-1]

            if syllable > 0 and pieces[syllable - 1][0] == meme[0]:
                meme = meme[1:]

            if pieces[syllable].upper() == pieces[syllable]:
                meme = meme.upper()

            # Sometimes, the hyphenator will return weird words. Such as the line
            # 'McDonalds.com' which returns as ['McDon', 'ald', 's.', 'com'], if
            # 's.' is chosen, the rules above will generate the empty word '' and
            # has weird behaviour with replace. I could detect this, on the other
            # hand this is really funny so I won't. The note is here to warn that
            # butt_target can potentially be '' however.
            return word.replace(butt_target, meme)

        except:
            return word


    stopwords = []
    with open('data/stopwords') as f:
        for word in f.read().split('\n'):
            stopwords.append(word.strip())


    def buttify_line(message, meme):
        # Split and order words in the message by length, buttifying longer words
        # has greater comedic effect according to my book on comedy (2006).
        words = map(str.lower, message.split(' '))
        words = list(filter(lambda x: x not in stopwords, words))
        words.sort(key = len, reverse = True)

        # Find longest word, used for calculating weightings.
        maximum = len(words[0])

        # For each word in the sentence, we have a 25% probability of being
        # buttified modified by the weighting, on top of this, frequency is taken
        # into account so as not to buttify 30 words in a row.
        output   = ""
        distance = randrange(0, 4)
        for word in message.split(' '):
            distance += 1

            # Skip stop words and similar words.
            if word.lower() not in words:
                output += word + " "
                continue

            # Calculate a weighting, and try and buttify the word.
            weighting = len(word) / maximum
            if random() * weighting > 0.08 and distance % 3 == 0:
                buttified = buttify_word(word, meme)
                output += buttified + " "
                continue

            output += word + " "

        return output


    @sink
    def butt_sink(irc):
        if random() > prob:
            return None

        for attempt in range(5):
            buttified = buttify_line(irc.message, memes[irc.channel])
            if 'butt' in buttified:
                return buttified


    @command('chance')
    def chancebutt(irc):
        global prob
        prob = float(irc.message)
        return 'Chance for critical buttification now {}%.'.format(prob * 100)


    @command('key')
    def keybutt(irc):
        if not irc.message:
            return "The current key is: {}.".format(memes[irc.channel])

        memes[irc.channel] = irc.message.split(' ')[0]
        return 'Buttification key set to: {}.'.format(memes[irc.channel])


    @command('buttify')
    @command('butt')
    @command('bu')
    @command('b')
    def buttify(irc):
        if not irc.message:
            return None

        for attempt in range(3):
            buttified = buttify_line(irc.message, memes[irc.channel])
            if memes[irc.channel] in buttified:
                return buttified

        return 'Unable to buttify.'

except ImportError:
    print('No Hyphenator library found. Ignoring buttify plugin.')

except OSError:
    print('Hyphenator dictionary missing. en_US expected.')
