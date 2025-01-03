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

from .method import create_method_class


class Object(object):
    _log = logging.getLogger("caffa-object")

    _methods = []
    __frozen = False

    @classmethod
    def prep_attributes(cls):
        setattr(cls, "_fields", None)
        setattr(cls, "_client", None)
        setattr(cls, "_local", None)
        setattr(cls, "_method_list", None)
        for method in cls._methods:
            setattr(cls, method.static_name(), None)
        cls.__frozen = True

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
            method_instance = method(self_object=self)
            setattr(self, method.static_name(), method_instance)
            self._method_list.append(method_instance)

    @classmethod
    def create(cls, **kwargs):
        return cls(json_object=kwargs, client=None, local=True)

    @property
    def keyword(self):
        return self._fields["keyword"]

    def __setattr__(self, key, value):
        if not hasattr(self, key) and self.__class__.__frozen:
            raise TypeError("%r does not have the property %s", self, key)
        object.__setattr__(self, key, value)

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
        if not self._local and field_keyword != "keyword" and field_keyword != "uuid":
            value = json.loads(
                self._client.get_field_value(self._fields["uuid"], field_keyword)
            )
        elif self._fields and field_keyword in self._fields:
            value = self._fields[field_keyword]

        if isinstance(value, dict):
            keyword = value["keyword"]
            schema_location = ""
            if "$id" in value:
                schema_location = value["$id"]
            else:
                schema_location = self._client.schema_location_from_keyword(keyword)

            schema_properties = self._client.schema_properties(schema_location)
            cls = create_class(keyword, schema_properties)
            value = cls(value, self._client, self._local)
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

    def raise_write_exception(self, property_name):
        raise AttributeError("Property " + property_name + " is read only!")


def make_read_lambda(property_name):
    return lambda self: self.get(property_name)


# Dummy read lambda used to avoid a proper caffa read call when asking
# for a write-only attribute
def make_dummy_read_lambda(property_name):
    return lambda self: None


def make_write_lambda(property_name):
    return lambda self, value: self.set(property_name, value)


def make_error_write_lambda(property_name):
    return lambda self, value: self.raise_write_exception(property_name)


def create_class(name, schema_properties):
    def __init__(self, json_object="", client=None, local=False):
        Object.__init__(self, json_object, client, local)

    newclass = type(name, (Object,), {"__init__": __init__})

    for property_name, prop in schema_properties.items():
        if property_name != "keyword" and property_name != "methods":
            read_only = "readOnly" in prop and prop["readOnly"]
            write_only = "writeOnly" in prop and prop["writeOnly"]

            read_lambda = make_dummy_read_lambda(property_name)
            write_lambda = make_error_write_lambda(property_name)

            if not write_only:
                read_lambda = make_read_lambda(property_name)
            if not read_only:
                write_lambda = make_write_lambda(property_name)

            setattr(
                newclass,
                property_name,
                property(
                    fget=read_lambda,
                    fset=write_lambda,
                ),
            )
        elif property_name == "methods":
            for method_name, method_schema in prop["properties"].items():
                method_schema = method_schema["properties"]
                newclass._methods.append(
                    create_method_class(method_name, method_schema)
                )
    newclass.prep_attributes()
    return newclass
