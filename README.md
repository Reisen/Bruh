# README
Bruh is an IRC bot written in Python 3. Originally standalone; Bruh is now a collection
of plugins for the [Walnut] IRC router. This repository comes with two plugins: the bot
itself and an optional web server that presents the bots database showing several items
like statistics, channel quotes, and general help information.

# How Plugins Work
Although Bruh is itself a plugin, plugins can be written for Bruh which are capable of
implementing commands or matching regular expressions. Writing plugins for bruh itself
allows command-like plugins to all be grouped under this one plugin. For a plugin that
does something a little more specialist, write a plugin for [Walnut] directly instead.
The main instance of Walnut, running on Rizon, uses a seperate plugin for dealing with
code compilation for example. It is possible to write plugins that run entirely within
containers or other VM's that simply plug into the ZMQ ports provided by [Walnut]. All
information on this can be found on the project wiki.

[Walnut]: https://github.com/Reisen/Walnut
