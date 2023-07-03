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

import ObjectService_pb2

class Method(object):
    _log = logging.getLogger("caffa-method")

    def __init__(self, self_object, json_object):
        self._self_object = self_object
        self._json_object = json.loads(json_object)

    def keyword(self):
        return self._json_object["keyword"]

    def return_type(self, field_keyword):
        return self._json_object["returns"]
        
    def rpc_object(self):
        return ObjectService_pb2.RpcObject(json=self.dump())

    def arguments(self):
        keywords = []
        for argument in self._json_object["arguments"]:
            keywords.append(argument["keyword"])
        return keywords

    def set_argument(self, keyword, value):
        from .object import Object
        for argument in self._json_object["arguments"]:
            if argument["keyword"] == keyword:
                if isinstance(value, Object):
                    argument["value"] = value.make_json()
                else:
                    argument["value"] = value

    def execute(self, **kwargs):
        for key, value in kwargs.items():
            self.set_argument(key, value)
        self._self_object.execute(self)

    def dump(self):
        return json.dumps(self._json_object)
