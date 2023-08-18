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

from .method import Method, create_method_class

class Object(object):
    _log = logging.getLogger("caffa-object")

    _methods = []

    def __init__(self, json_object="", client=None, local=False):
        if isinstance(json_object, dict):
            self._fields = json_object
        else:
            self._fields = json.loads(json_object)

        self._client = client
        self._local = local

        if not self._local:
            assert self._client is not None

        self._method_list = []
        for method in self.__class__._methods:
            method_instance = method(self_object = self)
            setattr(self, method.static_name(), method_instance)
            self._method_list.append(method_instance)
    

    @classmethod
    def create_local(cls, **kwargs):
        return cls(json_object=kwargs, client=None, local=True)

    @property
    def keyword(self):
        return self._fields["keyword"]

    def client(self):
        return self._client

    def to_dict(self):
        content = {}
        for key in self._fields:
            value = self.get(key)
            if isinstance(value, Object):
                value = value.to_dict()
            content[key] = value
        return content

    def to_json(self):
        return json.dumps(self.to_dict())

    def field_keywords(self):
        keywords = []
        for keyword in self._fields:
            keywords.append(keyword)
        return keywords

    def get(self, field_keyword):
        value = None
        if not self._local:
            value = json.loads(self._client.get_field_value(self._fields["uuid"], field_keyword))
        elif self._fields and field_keyword in self._fields:
            value = self._fields[field_keyword]

        if value is None:
            raise Exception("Field " + field_keyword + " did not exist in object")

        if isinstance(value, dict):
            keyword = value["keyword"]
            schema = self._client.schema(keyword)
            cls = create_class(keyword, schema)
            value = cls(value, self._client)
        return value

    def set(self, field_keyword, value):
        if isinstance(value, Object):
            value = object.to_json()
        if not self._local:
            self._client.set_field_value(self.uuid, field_keyword, value)
        else:
            self._fields[field_keyword]["value"] = value

    def create_field(self, keyword, type, value):
        self._fields[keyword] = {"type": type, "value": value}

    def set_fields(self, **kwargs):
        for key, value in kwargs.items():
            self.set(key, value)

    def execute(self, object_method, arguments):
        return self.client().execute(self.uuid, object_method.name(), arguments)

    def methods(self):
        return self._method_list

    def dump(self):
        return json.dumps(self.to_json())

def make_read_lambda(property_name):
    return lambda self: self.get(property_name)

def make_write_lambda(property_name):
    return lambda self, value: self.set(property_name, value)


def create_class(name, schema):
    def __init__(self, json_object="", client=None, local=False):        
        Object.__init__(self, json_object, client, local)
  
    newclass = type(name, (Object,),{"__init__": __init__})
    
    if "properties" in schema:
        for property_name in schema["properties"]:
            if property_name != "keyword" and property_name != "methods":
                setattr(newclass, property_name, property(fget=make_read_lambda(property_name), fset=make_write_lambda(property_name)))
            elif property_name == "methods":
                for method_name, method_schema in schema["properties"]["methods"]["properties"].items():
                    method_schema = method_schema["properties"]
                    newclass._methods.append(create_method_class(method_name, method_schema))

    return newclass
