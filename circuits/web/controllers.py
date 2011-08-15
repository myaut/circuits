# Module:   controllers
# Date:     6th November 2008
# Author:   James Mills, prologic at shortcircuit dot net dot au

"""Controllers

This module implements ...
"""

import json
from inspect import getargspec
from collections import Callable
from functools import update_wrapper

from circuits.core import handler, BaseComponent
from circuits import Event

from . import tools
from .events import GenerateResponse, RequestSuccess, RequestFailure
from .wrappers import Response
from .errors import Forbidden, HTTPError, NotFound, Redirect


def expose(*channels, **config):
    def decorate(f):
        @handler(*channels, **config)
        def wrapper(self, event, *args, **kwargs):
            try:
                if not hasattr(self, "request"):
                    (self.request, self.response), args = args[:2], args[2:]
                    self.request.args = args
                    self.request.kwargs = kwargs
                    self.cookie = self.request.cookie
                    if hasattr(self.request, "session"):
                        self.session = self.request.session
                if not getattr(f, "event", False):
                    result = f(self, *args, **kwargs)
                else:
                    result = f(self, event, *args, **kwargs)
                self.fire(RequestSuccess(event), self.channel)
                return result
            finally:
                if hasattr(self, "request"):
                    del self.request
                    del self.response
                    del self.cookie
                if hasattr(self, "session"):
                    del self.session
                self.fire(RequestFailure(event), self.channel)

        wrapper.args, wrapper.varargs, wrapper.varkw, wrapper.defaults = \
                getargspec(f)
        if wrapper.args and wrapper.args[0] == "self":
            del wrapper.args[0]
        wrapper.event = True

        return update_wrapper(wrapper, f)

    return decorate


class ExposeMetaClass(type):

    def __init__(cls, name, bases, dct):
        super(ExposeMetaClass, cls).__init__(name, bases, dct)

        for k, v in dct.items():
            if isinstance(v, Callable) \
                    and not (k[0] == "_" or hasattr(v, "handler")):
                setattr(cls, k, expose(k)(v))


class BaseController(BaseComponent):

    channel = "/"

    def url(self, *args, **kwargs):
        """Return the current URL or create a new URL

        If no arguments or keywords arguments are passed, returns the
        current URL for the current request.

        .. seealso:: :py:func:`circuits.web.utils.url`
        """

        return self.request.url(*args, **kwargs)

    def forbidden(self, description=None):
        """Return a 403 (Forbidden) response

        :param description: Message to display
        :type description: str
        """

        return Forbidden(self.request, self.response, description=description)

    def notfound(self, description=None):
        """Return a 404 (Not Found) response

        :param description: Message to display
        :type description: str
        """

        return NotFound(self.request, self.response, description=description)

    def redirect(self, urls, code=None):
        """Return a 30x (Redirect) response

        Redirect to another location specified by urls with an optional
        custom response code.

        :param urls: A single URL or list of URLs
        :type urls: str or list

        :param code: HTTP Redirect code
        :type code: int
        """
        return Redirect(self.request, self.response, urls, code=code)

    def serve_file(self, path, type=None, disposition=None, name=None):
        return tools.serve_file(self.request, self.response, path,
                type, disposition, name)

    def serve_download(self, path, name=None):
        return tools.serve_download(self.request, self.response, path,
                name)

    def expires(self, secs=0, force=False):
        tools.expires(self.request, self.response, secs, force)

    @handler('request_success')
    def _on_request_success(self, e):
        self.fire(GenerateResponse(e), "*")

Controller = ExposeMetaClass("Controller", (BaseController,), {})


def exposeJSON(*channels, **config):
    def decorate(f):
        @handler(*channels, **config)
        def wrapper(self, event, *args, **kwargs):
            try:
                if not hasattr(self, "request"):
                    self.request, self.response = args[:2]
                    args = args[2:]
                    self.cookie = self.request.cookie
                    if hasattr(self.request, "session"):
                        self.session = self.request.session
                if not getattr(f, "event", False):
                    result = f(self, *args, **kwargs)
                else:
                    result = f(self, event, *args, **kwargs)
                self.fire(RequestSuccess(event), self.channel)
                if (isinstance(result, HTTPError)
                        or isinstance(result, Response)):
                    return result
                else:
                    self.response.headers["Content-Type"] = (
                            "application/json"
                    )
                    return json.dumps(result)
            finally:
                if hasattr(self, "request"):
                    del self.request
                    del self.response
                    del self.cookie
                if hasattr(self, "session"):
                    del self.session
                self.fire(RequestFailure(event), self.channel)

        wrapper.args, wrapper.varargs, wrapper.varkw, wrapper.defaults = \
                getargspec(f)
        if wrapper.args and wrapper.args[0] == "self":
            del wrapper.args[0]

        return update_wrapper(wrapper, f)

    return decorate


class ExposeJSONMetaClass(type):

    def __init__(cls, name, bases, dct):
        super(ExposeJSONMetaClass, cls).__init__(name, bases, dct)

        for k, v in dct.items():
            if isinstance(v, Callable) \
                    and not (k[0] == "_" or hasattr(v, "handler")):
                setattr(cls, k, exposeJSON(k)(v))


JSONController = ExposeJSONMetaClass("JSONController", (BaseController,), {})
