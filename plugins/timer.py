"""
    This plugin allows queuing of timed callbacks, callbacks can be recurring
    and can be used to schedule timed plugins events.
"""
from plugins.commands import command
from plugins.bruh import event
from functools import wraps
import threading, time, datetime

class DeltaQueue(threading.Thread):
    """
    Implements a delta queue. Each element in the queue is delayed by every
    element before it.
    """
    def __init__(self):
        threading.Thread.__init__(self)

        self.running = True
        self.queue = []
        self.lock = threading.Lock()

    def stop(self):
        self.running = False

    def run(self):
        while self.running:
            time.sleep(1)

            # Lock, we don't want any modifications to be made to the queue
            # while we are already working on it.
            self.lock.acquire(True)
            
            # See if we actually have any events to process.
            if len(self.queue) > 0:
                # First we subtract one from the head of the queue.
                self.queue[0]._delta -= 1

                # If the head is less than or equal to 0, we run that event as
                # well as all events after that are also 0.
                for callback in self.queue[:]:
                    if callback._delta > 0:
                        break

                    callback()
                    self.queue = self.queue[1:]

                    # If the callback is repeatable, we stick it back in.
                    if callback._repeat:
                        self._insert(callback, callback._delay, callback._repeat)

            self.lock.release()

    def insert(self, f, delay, repeat = False):
        self.lock.acquire(True)

        self._insert(f, delay, repeat)

        self.lock.release()

    def _insert(self, f, delay, repeat = False):
        """Function to insert a new callback."""
        # Store delay states in the callback.
        f._delay = delay
        f._delta = delay
        f._repeat = repeat

        # If the list is empty, just stick that shit right in.
        if len(self.queue) == 0:
            self.queue.append(f)

        else:
            # We search the list until we find a place to insert our new queue
            # such that all previous elements sum to a larger delay than our
            # current callback.
            for position, callback in enumerate(self.queue):
                if callback._delta <= f._delta:
                    f._delta -= callback._delta

                else:
                    callback._delta -= f._delta
                    self.queue.insert(position, f)
                    break

            else:
                self.queue.insert(position + 1, f)


dq = DeltaQueue()
dq.start()

@event('GETOUT')
def stop_timers():
    dq.stop()
