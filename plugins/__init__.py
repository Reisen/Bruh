from collections import defaultdict

# Collect Hooks Locally within the Plugins module. Other plugins and the IRC
# core use this directly.
hooks = defaultdict(lambda: [])

def event(event_name):
    """Plugins decorate functions using this to hook events."""
    global hooks

    def hook(f):
        # Store the event hooked in the function, for access by other plugins.
        f.event = event_name
        hooks[event_name].append(f)

        return f

    return hook
