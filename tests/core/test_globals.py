#!/usr/bin/env python

from circuits import handler, Event, Component


class Foo(Event):
    """Foo Event"""


class Test(Event):
    """Test Event"""


class A(Component):

    channel = "a"

    def test(self):
        return "Hello World!"

    @handler(priority=1.0)
    def _on_event(self, event, *args, **kwargs):
        return "Foo"


class B(Component):

    @handler(priority=10.0, channel="*")
    def _on_channel(self, event, *args, **kwargs):
        return "Bar"


def test():
    app = A() + B()
    while app:
        app.flush()

    x = app.fire(Test(), "a")
    while app:
        app.flush()

    assert x.value[0] == "Bar"
    assert x.value[1] == "Foo"
    assert x.value[2] == "Hello World!"


def test_event():
    app = A() + B()
    while app:
        app.flush()

    e = Test()
    x = app.fire(e)
    while app:
        app.flush()

    assert x.value[0] == "Bar"
    assert x.value[1] == "Foo"
    assert x.value[2] == "Hello World!"


def test_channel():
    app = A() + B()
    while app:
        app.flush()

    e = Foo()
    x = app.fire(e, "b")
    while app:
        app.flush()

    assert x.value == "Bar"