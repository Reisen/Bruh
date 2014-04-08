import inspect
from collections import defaultdict

# Store references to imported plugins. This dictionary acts as a proxy for
# inter-plugin communication. This is so plugins can be reloaded independently
# of each other.
#
# Each module entry contains its own hooks key, which is a list of functions
# that respond to each IRC event. The reason it is stored in the dictonary
# along with the relevant module is so that module reloading can remove all old
# hooks easily.
modules = defaultdict(dict)

# Proxy object generator. This creates an object that when accessed
# automatically are passed through to the right object.
class mod_proxy:
    def __init__(self, modules):
        self.modules = modules

    def load_module(self, name):
        if name not in self.modules:
            print('Loading Module: {}'.format(name))
            self.modules[name] = {
                'module': None,
                'hooks': defaultdict(list)
            }

            self.modules[name]['module'] = __import__('plugins.' + name, globals(), locals(), -1)

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
                return getattr(mod_closure[self.key]['module'], key)

        return proxy_mod(key)

mod = mod_proxy(modules)

def event(event_name):
    """Plugins decorate functions using this to hook events."""
    global modules

    # Find the calling module name for hook storage.
    stack = inspect.stack()[1]
    stack = inspect.getmodule(stack[0])
    stack = stack.__name__.rsplit('.', 1)[1]

    def hook(f):
        # Store the event hooked in the function, for access by other plugins.
        f.event = event_name
        modules[stack]['hooks'][event_name].append(f)

        return f

    return hook
