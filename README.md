# README
Bruh is an IRC plugin for [Walnut] written in Python 3. It implements most plugins from
the [old standalone] IRC bot. It was created just to run mostly as a code execution bot
on Rizon's #c++ channel. I use it to play with libraries so It's not the easiest bot to
setup. If you definitely want to run it however check the requirements below and follow
the instructions.

# Requirements
*Note: The old bot can still be found [here.][old standalone]*
To run the bot, the following dependencies are needed, though these instructions should
set them up for you, GHC, libzmq, and pip should be all you need to have installed.

Required:
* [Walnut]
* GHC
* libzmq
* Flask (for the web.py plugin)

# Setup
Clone this repository, followed by the walnut repository which will include the drivers
Bruh needs to run behind Walnut:

    git clone https://github.com/Reisen/Bruh.git
    cd Bruh
    git clone https://github.com/Reisen/Walnut.git walnut

Build Walnut:

    cd walnut
    ./Setup.hs build

Install Python Dependencies:

    cd ../
    pip install -r requirements.txt

Edit `walnut/config` to setup the IRC networks Walnut should connect to, then start it
to connect. Once connected, run `python bruh.py` to run Bruh. You can background both
processes, bruh can be killed safely at any time and Walnut will continue to run, this
makes testing changes pretty smooth.

[Walnut]: https://github.com/Reisen/Walnut
[old standalone]: https://github.com/Reisen/Bruh/tree/old-base
