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
import json
import logging

class Method:
    _log = logging.getLogger("caffa-method")

    def __init__(self, self_object):
        self._self_object = self_object
        self._arguments = {}

    def execute(self, *args, **kwargs):
        arguments = {}
        if len(kwargs.items()) > 0:
            arguments["labelledArguments"] = kwargs
        elif len(args) > 0:
            arguments["positionalArguments"] = args
        return self._self_object.execute(self, arguments)

    @classmethod
    def static_name(cls):
        return cls.__name__

    def name(self):
        return self.__class__.__name__

def make_read_lambda(property_name):
    return lambda self: self_self_object.get(property_name)

def make_write_lambda(property_name):
    return lambda self, value: self.set(property_name, value)

def create_method_class(name, schema):
    def __init__(self, self_object):
        print ("Creating new method of type", self.__class__.__name__)
        return Method.__init__(self, self_object)
    
    newclass = type(name, (Method,),{"__init__": __init__})
    
    print("Method schema: ", schema)
    if "labelledArguments" in schema:
        for property_name in schema["labelledArguments"]["properties"]:
            print("Assigning property:", property_name, "to method", name)
            setattr(newclass, property_name, None)

    return newclass
