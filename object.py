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
import grpc
import json
import logging

import App_pb2
import FieldService_pb2
import FieldService_pb2_grpc
import ObjectService_pb2
import ObjectService_pb2_grpc

from .method import Method

class Object(object):
    _log = logging.getLogger("caffa-object")

    def __init__(self, json_object="", session_uuid="", grpc_channel=None, local=False):
        if isinstance(json_object, dict):
            self._json_object = json_object
        else:
            self._json_object = json.loads(json_object) if json_object else { "keyword": self.__class__.__name__}

        self._session_uuid = session_uuid
        self._object_cache = {}
        self._grpc_channel = grpc_channel
        self._local = local

        if self._grpc_channel is not None:
            self._field_stub = FieldService_pb2_grpc.FieldAccessStub(
                self._grpc_channel)
            self._object_stub = ObjectService_pb2_grpc.ObjectAccessStub(
                self._grpc_channel)

        if not self._local:
            assert self._grpc_channel is not None

    def keyword(self):
        return self._json_object["keyword"]

    def uuid(self):
        return self._json_object["uuid"]

    def session_uuid(self):
        return self._session_uuid

    def grpc_channel(self):
        return self._grpc_channel

    def type(self, field_keyword):
        if self._json_object and field_keyword in self._json_object:
            return self._json_object[field_keyword]["type"]
        else:
            return None

    def make_json(self):
        if self._object_cache:
            for key, object in self._object_cache.items():
                self._json_object[key] = object.make_json()

        for var in vars(self):
            if not var.startswith("_"):
                value = getattr(self, var)
                if isinstance(value, Object):
                    value = value.make_json()    
                self._json_object[var] = value
        return self._json_object

    def rpc_object(self):
        return ObjectService_pb2.RpcObject(json=self.dump())

    def field_keywords(self):
        keywords = []
        for keyword in self._json_object:
            keywords.append(keyword)
        return keywords

    def get_object(self, field_keyword):
        if not self._local:
            session = App_pb2.SessionMessage(uuid=self._session_uuid)
            field_request = FieldService_pb2.FieldRequest(
                class_keyword=self.keyword(),
                uuid=self.uuid(),
                keyword=field_keyword,
                session=session,
            )
            result = self._field_stub.GetValue(field_request).value
            return (
                Object(result, self._session_uuid, self._grpc_channel)
                if result is not None
                else None
            )
        else:
            if field_keyword in self._object_cache:
                return self._object_cache[field_keyword]

            json_string = json.dumps(self._json_object[field_keyword]["value"])
            if json_string:
                self._object_cache[field_keyword] = Object(json_string)
                return self._object_cache[field_keyword]
            return None

    def get_objects(self, field_keyword):
        if not self._local:
            session = App_pb2.SessionMessage(uuid=self._session_uuid)
            field_request = FieldService_pb2.FieldRequest(
                class_keyword=self.keyword(),
                uuid=self.uuid(),
                keyword=field_keyword,
                session=session,
            )
            result = self._field_stub.GetValue(field_request).value
            caffa_objects = []
            json_array = json.loads(result)

            for json_object in json_array:
                caffa_objects.append(Object(json.dumps(json_object), self._session_uuid, self._grpc_channel))
            return caffa_objects
        elif field_keyword in self._json_object:
            if field_keyword in self._object_cache:
                cached_data = self._object_cache[field_keyword]
                if not isinstance(cached_data, list):
                    return [cached_data]
                return cached_data
            cached_data = []
            for entry in self._json_object[field_keyword]["value"]:
                json_string = json.dumps(entry)
                if json_string:
                    cached_data.append(Object(json_string))
            self._object_cache[field_keyword] = cached_data
            return cached_data
        return []

    def get_primitives(self, field_keyword):
        result = None
        if not self._local:
            session = App_pb2.SessionMessage(uuid=self._session_uuid)
            field_request = FieldService_pb2.FieldRequest(
                class_keyword=self.keyword(),
                uuid=self.uuid(),
                keyword=field_keyword,
                session=session,
            )
            result = self._field_stub.GetValue(field_request).value
            return json.loads(result) if result is not None else None
        elif self._json_object and field_keyword in self._json_object:
            if "value" in self._json_object[field_keyword]:
                result = self._json_object[field_keyword]["value"]
            else:
                result = self._json_object[field_keyword]
            return result
        return None

    def get(self, field_keyword):
        data_type = self.type(field_keyword)
        Object._log.debug(
            "Getting data for keyword=%s and data type=%s", field_keyword, data_type
        )
        if data_type is not None:
            if data_type == "object":
                return self.get_object(field_keyword)
            elif data_type == "object[]":
                return self.get_objects(field_keyword)
            else:
                return self.get_primitives(field_keyword)
        print (field_keyword, data_type)
        raise Exception("Field " + field_keyword + " did not exist in object")
        return None

    def set(self, field_keyword, value, address_offset=0):
        data_type = self.type(field_keyword)
        Object._log.debug(
            "Setting value=%s for keyword=%s and data type=%s",
            str(value),
            field_keyword,
            data_type,
        )
        if not self._local:
            session = App_pb2.SessionMessage(uuid=self._session_uuid)

            field_request = FieldService_pb2.FieldRequest(
                class_keyword=self.keyword(),
                uuid=self.uuid(),
                keyword=field_keyword,
                index=address_offset,
                session=session,
            )
            setter_request = FieldService_pb2.SetterRequest(
                field=field_request, value=json.dumps(value)
            )
            self._field_stub.SetValue(setter_request)
        else:
            self._json_object[field_keyword]["value"] = value

    def create_field(self, keyword, type, value):
        self._json_object[keyword] = {"type": type, "value": value}

    def set_fields(self, **kwargs):
        for key, value in kwargs.items():
            self.set(key, value)

    def methods(self):
        session = App_pb2.SessionMessage(uuid=self._session_uuid)
        request = ObjectService_pb2.ListMethodsRequest(
            self_object=self.rpc_object(), session=session
        )

        rpc_object_list = self._object_stub.ListMethods(request).objects
        caffa_method_list = []
        for rpc_object in rpc_object_list:
            caffa_method_list.append(Method(self, rpc_object.json))
        return caffa_method_list

    def method(self, keyword):
        all_methods = self.methods()
        for single_method in all_methods:
            if single_method.keyword() == keyword:
                return single_method
        return None

    def execute(self, object_method):
        session = App_pb2.SessionMessage(uuid=self._session_uuid)

        method_request = ObjectService_pb2.MethodRequest(
            self_object=self.rpc_object(),
            method=object_method.rpc_object(),
            session=session
        )
        try:
            result = self._object_stub.ExecuteMethod(method_request)
        except grpc.RpcError as e:
            raise RuntimeError(e.details())

        return_json = json.loads(result.json)
        if "value" in return_json:
            return return_json["value"]
        else:
            return None

    def dump(self):
        return json.dumps(self.make_json())


    def upgrade(self, cls):
        return cls(self._json_object, self._session_uuid, self._grpc_channel, self._local)

class Document(Object):
    """The Document class is a top level object acting as a "Project" or container"""

    def __init__(self, json_object="", session_uuid="", grpc_channel=None, local=False):
        super().__init__(json_object, session_uuid, grpc_channel, local)

    @property
    def id(self):
        """A unique document ID"""

        return self.get("id")

    @id.setter
    def id(self, value):
        return self.set("id", value)

    @property
    def fileName(self):
        """The filename of the document if saved to disk"""

        return self.get("fileName")

    @fileName.setter
    def fileName(self, value):
        return self.set("fileName", value)
