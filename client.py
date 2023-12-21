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
import requests
import time
import threading

from enum import IntEnum
from . import object
from types import SimpleNamespace

# Update the (x, y, z) tuple to match minimum required version (0, 6, 4) means minimum 0.6.4
# By default we try to match the caffa-version
# However the application using caffa should set its own version which can be checked
# against by providing the script-version parameter
MIN_APP_VERSION = (1, 2, 0)
MAX_APP_VERSION = (1, 2, 99)

class SessionType(IntEnum):
    INVALID   = 0
    REGULAR   = 1
    OBSERVING = 2


class Client:
    def __init__(self, hostname, port=50000, username="", password="", min_app_version=MIN_APP_VERSION, max_app_version=MAX_APP_VERSION, session_type=SessionType.REGULAR):
        self.hostname = hostname
        self.port = port
        self.basic_auth = requests.auth.HTTPBasicAuth(username, password)

        self.log = logging.getLogger("rpc-logger")
        self.mutex = threading.Lock()

        self.check_version(min_app_version, max_app_version)

        self.session_uuid = self.create_session(session_type)

        if not self.session_uuid:
            raise RuntimeError("Failed to create session")
        self.log.debug("Session uuid: %s", self.session_uuid)
        self.keep_alive = True
        self.keepalive_thread = threading.Thread(target=self.send_keepalives)
        self.keepalive_thread.start()

    def _build_url(self, path, params = ""):
        url = "http://" + self.hostname + ":" + str(self.port) + path
        if hasattr(self, "session_uuid"):
            url += "?session_uuid=" + self.session_uuid
            if len(params) > 0:
                url += "&" + params
        else:
            if len(params) > 0:
                url += "?" + params
        return url

    def _perform_get_request(self, path, params = ""):
        url = self._build_url(path, params)
        try:
            response = requests.get(url, auth=self.basic_auth)
            response.raise_for_status()
            return response.text
        except requests.exceptions.HTTPError as e:
            self.log.error("Failed GET request with error " + e.response.text)
            raise e
        except requests.exceptions.RequestException as e:
            self.log.error("Failed GET request with error ", e)
            raise e
    
    def _perform_delete_request(self, path, params):
        url = self._build_url(path, params)
        try:
            response = requests.delete(url, auth=self.basic_auth)
            response.raise_for_status()
            return response.text
        except requests.exceptions.HTTPError as e:
            self.log.error("Failed DELETE request with error " + e.response.text)
            raise e
        except requests.exceptions.RequestException as e:
            self.log.error("Failed DELETE request with error ", e)
            raise e

    def _perform_put_request(self, path, params="", body=""):
        url = self._build_url(path, params)
        try:
            response = requests.put(url, json=body, auth=self.basic_auth)
            response.raise_for_status()
            return response.text
        except requests.exceptions.HTTPError as e:
            self.log.error("Failed PUT request with error " + e.response.text)
            raise e
        except requests.exceptions.RequestException as e:
            self.log.error("Failed PUT request with error ", e)
            raise e

    def _json_text_to_object(self, text):
        return json.loads(text, object_hook=lambda d: SimpleNamespace(**d))

    def schema_list(self):
        all_schemas = json.loads(self._perform_get_request("/schemas"))
        return all_schemas

    def schema(self, keyword):
        schema = json.loads(self._perform_get_request("/schemas/" + keyword))
        return schema

    def execute(self, object_uuid, method_name, arguments):
        value = json.loads(self._perform_put_request(path="/uuid/" + object_uuid + "/" + method_name, body=arguments))
        if isinstance(value, dict):
            if "keyword" in value:
                keyword = value["keyword"]
                schema = self.schema(keyword)
                cls = object.create_class(keyword, schema)
                return cls(value, self, True)
        return value

    def app_info(self):
        return self._json_text_to_object(self._perform_get_request("/app/info"))

    def create_session(self, session_type):
        response = self._json_text_to_object(self._perform_put_request(path="/session/create?type="+str(int(session_type))))
        return response.session_uuid

    def cleanup(self):
        try:
            self.mutex.acquire()
            self.keep_alive = False
            if self.session_uuid:
                self._perform_delete_request("/session/destroy?session_uuid=" + self.session_uuid, "")
        finally:
            self.mutex.release()

    def send_keepalive(self):
        self._perform_put_request(path="/session/keepalive")

    def send_keepalives(self):
        while True:
            time.sleep(0.5)
            try:
                self.mutex.acquire()
                if not self.keep_alive:
                    break;
                else:
                    self.send_keepalive()
            finally:
                self.mutex.release()

    def document(self, document_id):
        assert len(document_id) > 0
        json_text = self._perform_get_request("/" + document_id, "skeleton=true")
        json_object = json.loads(json_text)
        keyword = json_object["keyword"]
        schema = self.schema(keyword)
        cls = object.create_class(keyword, schema)

        return cls(json_text, self, False)
    
    def get_field_value(self, object_uuid, field_name):
        return self._perform_get_request("/uuid/" + object_uuid + "/" + field_name)

    def set_field_value(self, object_uuid, field_name, json_value):
        return self._perform_put_request(path="/uuid/" + object_uuid + "/" + field_name, body=json_value)

    def check_version(self, min_app_version, max_app_version):
        app_info = self.app_info()
        self.log.info(
            "Found Caffa '"
            + app_info.name
            + "' with version: "
            + str(app_info.major_version)
            + "."
            + str(app_info.minor_version)
            + "."
            + str(app_info.patch_version)
        )

        if (
            app_info.major_version,
            app_info.minor_version,
            app_info.patch_version,
        ) < min_app_version:
            raise RuntimeError(
                "App Version {}.{}.{} is too old. The minimum required is {}.{}.{}".format(
                app_info.major_version,
                app_info.minor_version,
                app_info.patch_version,
                min_app_version[0],
                min_app_version[1],
                min_app_version[2])
            )
        if (
            app_info.major_version,
            app_info.minor_version,
            app_info.patch_version,
        ) > max_app_version:
            raise RuntimeError(
                "App Version {}.{}.{} is too new. The maximum required is {}.{}.{}".format(
                app_info.major_version,
                app_info.minor_version,
                app_info.patch_version,
                max_app_version[0],
                max_app_version[1],
                max_app_version[2])
            )

        return True
