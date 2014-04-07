from collections import defaultdict

# Collect Hooks Locally within the Plugins module. Other plugins and the IRC
# core use this directly.
hooks = defaultdict(lambda: [])

# Store references to imported plugins. This dictionary acts as a proxy for
# inter-plugin communication. This is so plugins can be reloaded independently
# of each other.
modules = {}

# Proxy object generator. This creates an object that when accessed
# automatically are passed through to the right object.
class mod_proxy:
    def __init__(self, modules):
        self.modules = modules

    def load_module(self, name):
        print('Loading {}'.format(name))
        if name not in self.modules:
            self.modules[name] = __import__('plugins.' + name, globals(), locals(), -1)

    def __getattr__(self, key):
        # If a module is being accessed that hasn't yet been loaded (such as on
        # first run of the bot), the module should be loaded immediately.
        self.load_module(key)

        # Store the module dictionary in the local scope so that it is captured
        # in the closure that the returned object has access to.
        mod_closure = self.modules

        # Object that proxies all values to the closure reference to the
        # module.
        class proxy_mod:
            def __init__(self, key):
                self.key = key

            def __getattr__(self, key):
                return getattr(mod_closure[self.key], key)

        return proxy_mod(key)

mod = mod_proxy(modules)

def event(event_name):
    """Plugins decorate functions using this to hook events."""
    global hooks

    def hook(f):
        # Store the event hooked in the function, for access by other plugins.
        f.event = event_name
        hooks[event_name].append(f)

        return f

    return hook
