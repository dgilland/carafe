
from carafe.ext.signaler import Signaler

from .base import TestBase
from .core import signaler


class TestSignaler(TestBase):
    '''Test signaler'''

    def test_send_connect(self):
        '''Test send/connect methods'''
        data = {}

        @self.app.route('/')
        def index():
            signaler.send('foosignal', data, one=1, two=2, x=3, y=4)
            return ''

        def handler(sender, one, two, y, x):
            sender.update({'one': one, 'two': two, 'x': x, 'y': y})


        signaler.connect('foosignal', handler)

        self.client.get('/')

        self.assertEqual(data, {'one': 1, 'two': 2, 'x': 3, 'y': 4})

    def test_send_connect_using_attr(self):
        '''Test send/connect via named attributes'''
        data = {}

        @self.app.route('/')
        def index():
            signaler.foosignal.send(data, one=1, two=2, x=3, y=4)
            return ''

        def handler(sender, one, two, y, x):
            sender.update({'one': one, 'two': two, 'x': x, 'y': y})


        signaler.foosignal.connect(handler)

        self.client.get('/')

        self.assertEqual(data, {'one': 1, 'two': 2, 'x': 3, 'y': 4})

    def test_signal_registry(self):
        # create new Signaler since imported one alread has used signals
        test_signaler = Signaler()

        self.assertEqual(test_signaler._signals, {})

        test_signaler.signal1.send({})
        test_signaler.signal2.send({})

        self.assertTrue('signal1' in test_signaler._signals)
        self.assertTrue('signal2' in test_signaler._signals)

