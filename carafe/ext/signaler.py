
from flask.signals import Namespace


class Signaler(object):
    '''
    Collection of supported signals to use throughout application

    Define new signals as properties and return self.namespace.signal('name')
    '''
    def __init__(self, namespace=None):
        if not namespace:
            namespace = Namespace()

        self.namespace = namespace
        self._signals = {}

    def send(self, signal, *args, **kargs):
        '''Send signal by name'''
        getattr(self, signal).send(*args, **kargs)

    def connect(self, signal, *args, **kargs):
        '''Connect to signl by name'''
        getattr(self, signal).connect(*args, **kargs)

    def make_signal(self, signal):
        if signal not in self._signals:
            self._signals[signal] = self.namespace.signal(signal)

        return self._signals[signal]

    def __getattr__(self, signal):
        '''Return signal object. If it doesn't exist in registry, create it.'''
        return self.make_signal(signal)
