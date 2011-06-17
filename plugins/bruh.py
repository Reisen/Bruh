"""
    This is the only plugin that is required by the bot itself to run successfully.
    It provides a single decorator that assigns functions to IRC events. The reason
    it is needed by the bot is because the bot is responsible for plugin loading, and
    uses this module's 'hooks' object to access them.

    Other plugins can use this plugin also to hook events.
"""

# Collect Hooks Locally
hooks = {'BRUH':[]}

def event(name):
    """Hooks an event"""
    global hooks

    def hook(f):
        if name not in hooks:
            hooks[name] = []

        # Append to global hooks
        hooks[name].append(f)
        f.event = name
        return f

    return hook
