
from time import sleep

from .base import TestBase

from carafe.utils import async, classproperty, to_dict


class TestAsync(TestBase):

    tracker = {'count': 0, 'callback': 0}

    @async
    def asyncfn(self, callback=None):
        sleep(0.1)
        self.tracker['count'] += 1

        if callback:
            callback()

    def test_async(self):
        def callback():
            self.tracker['callback'] = self.tracker['count']

        self.assertEqual(self.tracker['count'], 0)

        self.asyncfn(callback=callback)

        self.assertEqual(self.tracker['count'], 0)

        sleep(0.2)

        self.assertEqual(self.tracker['count'], 1)
        self.assertEqual(self.tracker['callback'], 1)


class TestClassProperty(TestBase):
    class HasClassProperty(object):
        @classproperty
        def foo(self):
            return 'foo' + 'bar'

    def test_class_property(self):
        self.assertEqual(self.HasClassProperty.foo, 'foobar')
        self.assertEqual(self.HasClassProperty().foo, 'foobar')


class TestToDict(TestBase):
    data = {'foo': 'bar'}

    class DictClass(object):
        def __init__(self, data):
            self.data = data

        def to_dict(self):
            return self.data

    def test_to_dict_as_function(self):
        x = self.DictClass(self.data)
        y = [x] * 2

        self.assertEqual(to_dict(x), self.data)
        self.assertEqual(to_dict(y), [self.data] * 2)

        self.assertEqual(to_dict(x, namespace='baz'), {'baz': self.data})
        self.assertEqual(to_dict(y, namespace='baz'), {'baz': [self.data] * 2})

    def test_to_dict_as_decorator(self):
        x = self.DictClass(self.data)

        @to_dict()
        def foo():
            return x

        @to_dict(namespace='baz')
        def baz():
            return x

        self.assertEqual(foo(), self.data)
        self.assertEqual(baz(), {'baz': self.data})
