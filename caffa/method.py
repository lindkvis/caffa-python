###################################################################################################
#
#   Caffa
#   Copyright (C) Kontur AS
#
#   GNU Lesser General Public License Usage
#   This library is free software; you can redistribute it and/or modify
#   it under the terms of the GNU Lesser General Public License as published by
#   the Free Software Foundation; either version 2.1 of the License, or
#   (at your option) any later version.
#
#   This library is distributed in the hope that it will be useful, but WITHOUT ANY
#   WARRANTY; without even the implied warranty of MERCHANTABILITY or
#   FITNESS FOR A PARTICULAR PURPOSE.
#
#   See the GNU Lesser General Public License at <<http:#www.gnu.org/licenses/lgpl-2.1.html>>
#   for more details.
#
import logging


class Method:
    _log = logging.getLogger("caffa-method")
    _labelled_arguments = {}
    _positional_arguments = {}

    def __init__(self, self_object):
        self._self_object = self_object

    def __call__(self, *args, **kwargs):
        from .object import Object

        arguments = {}
        if len(kwargs.items()) > 0:
            arguments["labelledArguments"] = self.__class__._labelled_arguments[
                self.__class__.__name__
            ]
            for key, value in kwargs.items():
                if isinstance(value, Object):
                    value = value.to_dict()
                arguments["labelledArguments"][key] = value
        elif len(args) > 0:
            arguments["positionalArguments"] = self.__class__._positional_arguments[
                self.__class__.__name__
            ]
            for i, value in enumerate(args):
                if isinstance(value, Object):
                    value = value.to_dict()
                arguments["positionalArguments"][i] = value

        return self._self_object.execute(self, arguments)

    @classmethod
    def static_name(cls):
        return cls.__name__

    def name(self):
        return self.__class__.__name__


def make_read_lambda(property_name):
    return lambda self: self._self_object.get(property_name)


def make_write_lambda(property_name):
    return lambda self, value: self.set(property_name, value)


def create_method_class(name, schema):
    def __init__(self, self_object):
        return Method.__init__(self, self_object)

    newclass = type(name, (Method,), {"__init__": __init__})
    newclass._labelled_arguments[name] = {}
    newclass._positional_arguments[name] = []
    if "labelledArguments" in schema:
        for argument_name in schema["labelledArguments"]["properties"]:
            newclass._labelled_arguments[name][argument_name] = None
    if "positionalArguments" in schema:
        for i, entry in enumerate(schema["positionalArguments"]["items"]):
            newclass._positional_arguments[name].append(None)

    return newclass
