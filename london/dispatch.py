# Using dispatcher from PyDispatcher
from pydispatch import dispatcher

class Signal(object):
    """
    Uses PyDispatcher to dispatch messages to listeners.

    The arguments required and optional must be lists or tuples.
    """
    def __init__(self, required=None, optional=None):
        self.required = required
        self.optional = optional

    def connect(self, function, **kwargs):
        """
        Connects a function to this signal
        """
        dispatcher.connect(function, signal=self, **kwargs)

    def send(self, **kwargs):
        """
        Calls the connected functions to this signal.
        """
        return [ret for func, ret in dispatcher.send(signal=self, **kwargs)]

