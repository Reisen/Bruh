"""
    Provide a means of editing profile properties for users. Things like
    Avatars, etc. This can be used to generate, well, profiles for users.
"""
from plugins import mod
from uuid import uuid4

auth = mod.auth
hook = mod.hook

@hook.command
@auth.logged_in
def profile(irc, nick, chan, msg, args, user):
    """
    Change properties that effect your user profile.
    .profile <property> <value>
    """
    # Properties that the user is actually allowed to edit, otherwise they
    # could change their rank or something.
    allowed_properties = [
        'avatar',
        'quote',
        'api'
    ]

    if not msg:
        # Get all the users current properties and list them.
        for p in allowed_properties:
            p = p.capitalize()
            irc.notice(nick, '{}: {}'.format(p, user.get(p, None)))

        irc.notice(nick, "Syntax: .profile <property> <value>")
        return

    command, *args = msg.split(' ', 1)

    # Normalize the property name.
    key = command.lower().capitalize()

    # Check if the command is actuall modifiable, or if it exists.
    if command.lower() in allowed_properties:
        if not args:
            return "Current {} is {}".format(key, user.get(key, 'None'))

        user[key] = args[0]
        return "Updated {} to {}".format(key, user[key])

    return "You cannot modify or access the {} property.".format(key)


@hook.command
@auth.logged_in
def avatar(irc, nick, chan, msg, args, user):
    """
    Change your profile avatar. Use .profile for more customization.
    .avatar <image url>
    """
    if not msg:
        return "Syntax: .avatar <image url>"

    user['Avatar'] = msg
    return "Avatar changed to {}".format(msg)


@hook.command
@auth.logged_in
def api(irc, nick, chan, msg, args, user):
    # Generate a new API key if one didn't already exist.
    if 'Api' not in user or msg == 'new':
        user['Api'] = uuid4().hex
        return "Generated new API Key: {}".format(msg)

    return "Your API Key: {}  --  Use '.api new' to generate a new key.".format(user['Api'])
