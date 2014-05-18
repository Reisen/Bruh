"""
    Provides Redis access to Bruh. Used mostly for Pub/Sub messages for instant
    notifications to IRC, such as Github push requests or maybe live channel
    notifications for pastebin pastes.
"""
try:
    from redis import StrictRedis
    from functools import wraps
    from threading import Thread
    from plugins import event, mod
    from collections import defaultdict

    hook = mod.hook

    pubsub_hooks = defaultdict(list)


    def handle_pubsub(pubsub, hooks, servers):
        for message in pubsub.listen():
            # Only handle messages, ignore subscribe/unsubscribe messages.
            if message['type'] != 'pmessage':
                continue

            # Handle a shutdown message, means we're done handling messages and
            # we should just abandon thread.
            if message['channel'] == 'bruh:core' and message['data'] == b'REDIS_QUIT':
                break

            # Route the resulting message to the callback.
            # Network specific channel routing.
            network = None
            channel = message['channel']
            message = message['data']
            for irc in servers:
                if channel.startswith(irc.server['address']):
                    print('Nice')
                    network, channel = irc, channel.split(':', 1)[1]

            if channel in hooks:
                for f in hooks[channel]:
                    f(network, message)

        pubsub.close()


    @event('BRUH')
    def initialize_redis(irc):
        # Connect to the default Redis database.
        # TODO: Make Redis configurable.
        redis = StrictRedis()

        # Expose the StrictRedis object to plugins through the IRC object.
        irc.redis = redis

        # Expose a Pub/Sub object, just one, as it handles all listening and
        # routes messages out based on pattern.
        irc.pubsub = redis.pubsub()

        # Start listening on a core channel for general messages, including the
        # shutdown signal. Also setup the hook dictionary for routing messages
        # to the right hooks.
        irc.plugins['redis'].setdefault('pub_hooks', pubsub_hooks)
        irc.pubsub.psubscribe('*')

        # Create a thread to listen for incoming pubsub events and route them
        # out to the correct functions.
        irc.plugins['redis'].setdefault('pub_thread', Thread(
            target = handle_pubsub,
            args = (irc.pubsub, pubsub_hooks, irc.conns)
        ))
        irc.plugins['redis']['pub_thread'].start()


    @event('GETOUT')
    def shutdown_redis(irc):
        if irc.plugins['redis']['pub_thread']:
            irc.redis.publish('bruh:core', 'REDIS_QUIT')
            irc.plugins['redis']['pub_thread'].join()


    def sub(channel):
        def sub_wrapper(f):
            pubsub_hooks[channel].append(f)
            return f

        return sub_wrapper


except ImportError:
    print('Loading Module: redis (failed: No redis-py module installed)')
