#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=3 sts=3 ts=3

"""Main

circutis.web Web Server and Testing Tool.
"""

import optparse
from wsgiref.validate import validator
from wsgiref.simple_server import make_server

try:
    import hotshot
    import hotshot.stats
except ImportError:
    hostshot = None

try:
    import psyco
except ImportError:
    psyco = None

from circuits.tools import inspect, graph
from circuits import Component, Manager, Debugger
from circuits import __version__ as systemVersion
from circuits.net.pollers import Select, Poll, EPoll
from circuits.web import BaseServer, Server, Application, Controller


USAGE = "%prog [options]"
VERSION = "%prog v" + systemVersion

###
### Functions
###

def parse_options():
    """parse_options() -> opts, args

    Parse the command-line options given returning both
    the parsed options and arguments.
    """

    parser = optparse.OptionParser(usage=USAGE, version=VERSION)

    parser.add_option("-b", "--bind",
            action="store", type="string", default="0.0.0.0:8000", dest="bind",
            help="Bind to address:[port]")

    parser.add_option("-j", "--jit",
            action="store_true", default=False, dest="jit",
            help="Use python HIT (psyco)")

    parser.add_option("-t", "--type",
            action="store", type="string", default="select", dest="type",
            help="Specify type of poller to use")

    parser.add_option("-s", "--server",
            action="store", type="string", default="server", dest="server",
            help="Specify server to use")

    parser.add_option("-p", "--profile",
            action="store_true", default=False, dest="profile",
            help="Enable execution profiling support")

    parser.add_option("-d", "--debug",
            action="store_true", default=False, dest="debug",
            help="Enable debug mode")

    parser.add_option("-v", "--validate",
            action="store_true", default=False, dest="validate",
            help="Enable WSGI validation mode")

    opts, args = parser.parse_args()

    return opts, args

###
### Components
###

class HelloWorld(Component):

    channel = "web"

    def request(self, request, response):
        return "Hello World!"

class Root(Controller):

    def index(self):
        return "Hello World!"

###
### Main
###

def main():
    opts, args = parse_options()

    if opts.jit and psyco:
        psyco.full()

    if ":" in opts.bind:
        address, port = opts.bind.split(":")
        port = int(port)
    else:
        address, port = opts.bind, 8000

    bind = (address, port)

    if opts.validate:
        application = (Application() + Root())
        app = validator(application)

        httpd = make_server(bind, app)
        httpd.serve_forever()
        
        raise SystemExit, 0

    manager = Manager()

    if opts.debug:
        manager += Debugger()

    poller = opts.type.lower()
    if poller == "poll":
        Poller = Poll
    elif poller == "epoll":
        Poller = EPoll
    else:
        Poller = Select

    if opts.server.lower() == "base":
        manager += (BaseServer(bind, poller=Poller) + HelloWorld())
    else:
        manager += (Server(bind, poller=Poller) + Root())

    if opts.profile:
        if hotshot:
            profiler = hotshot.Profile(".profile")
            profiler.start()

    if opts.debug:
        print graph(manager)
        print
        print inspect(manager)

    manager.run()

    if opts.profile and hotshot:
        profiler.stop()
        profiler.close()

        stats = hotshot.stats.load(".profile")
        stats.strip_dirs()
        stats.sort_stats("time", "calls")
        stats.print_stats(20)

###
### Entry Point
###

if __name__ == "__main__":
    main()
