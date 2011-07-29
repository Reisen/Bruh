"""
    This is the only plugin that the main bot relies on. The plugin dispatching
    relies on the hooks dictionary in this module, as other plugins use this
    module to populate the dictionary with functions to handle events.
"""

# Collect Hooks Locally
hooks = {'BRUH':[]}

def event(event_name):
    """Plugins decorate functions using this to hook events."""
    global hooks

    def hook(f):
        # Events are not pre-populated in the dictionary. Events that have no
        # hooks simply do not have keys. This keeps the dictionary small and
        # allows the dispatcher to quikly decide whether or not to deal with an
        # event.
        if event_name not in hooks:
            hooks[event_name] = []

        # Store the event hooked in the function, for access by other plugins.
        f.event = event_name

        # Append this function to this list of handlers for this event.
        hooks[event_name].append(f)
        return f

    return hook
