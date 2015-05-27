# README
Bruh is an IRC plugin for [Walnut] written in Python 3. It implements most plugins from
the [old standalone] IRC bot. It was created just to run mostly as a code execution bot
on Rizon's #c++ channel. I use it to play with libraries so It's not the easiest bot to
setup. If you definitely want to run it however check the requirements below and follow
the instructions.

# Requirements
*Note: The old bot can still be found [here.][old standalone]*
To run the bot, the following are required. Walnut should automatically be cloned along
with this repository so as long as you have GHC, it should build with the setup script.

Required:
* [Walnut]
* Redis
* pyzmq

Optional:
* Hyphentator (for the buttify plugin)
* Flask (for the web.py plugin)

# Setup
Clone this repository, followed by the walnut repository for the drivers required. These are part of the Walnut project and doesn't include the drivers, this will change:

    git clone https://github.com/Reisen/Bruh.git
    cd Bruh
    git clone https://github.com/Reisen/Walnut.git

Build Walnut:

    cd walnut
    ./Setup.hs build

Install Python Dependencies:

    cd ../
    pip install -r requirements.txt

Make sure Redis is running. Then simply run `python bruh.py` to start bruh, then next
run Walnut to start the connections to IRC. Modifications can be made to bruh and the
python can be killed and restarted without issue, Walnut will maintain the connection
to IRC at all times.

[Walnut]: https://github.com/Reisen/Walnut
[old standalone]: https://github.com/Reisen/Bruh/tree/old-base
