"""
    Provide a means of editing profile properties for users. Things like
    Avatars, etc. This can be used to generate, well, profiles for users.
"""
from plugins import mod

auth = mod.auth
hook = mod.hook

@hook.command
@auth.logged_in
def profile(irc, nick, chan, msg, args, user):
    """
    Change properties that effect your user profile.
    .profile <property> <value>
    """
    if not msg:
        return "Syntax: .profile <property> <value>"

    # Properties that the user is actually allowed to edit, otherwise they
    # could change their rank or something.
    allowed_properties = [
        'avatar',
        'quote',
    ]

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
