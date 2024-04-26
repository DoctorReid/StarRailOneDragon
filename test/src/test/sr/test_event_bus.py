import test
from sr.event_bus import EventBus


class TestEventBus(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_listen(self):
        bus = EventBus()
        obj1 = set()
        obj2 = set()

        bus.listen('test', obj1.add)
        bus.listen('test', obj1.add)
        bus.listen('test', obj2.add)

        self.assertEqual(2, len(bus.callbacks['test']))

        bus.unlisten_all(obj1)
        self.assertEqual(1, len(bus.callbacks['test']))

        bus.unlisten('test', obj2.add)
        self.assertEqual(0, len(bus.callbacks['test']))

    def test_dispatch(self):
        bus = EventBus()
        obj1 = set()

        bus.listen('test', obj1.add)
        bus.dispatch_event('test', 1)

        self.assertEqual(1, len(obj1))
        self.assertEqual(1, obj1.pop())
