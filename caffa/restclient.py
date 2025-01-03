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
import threading
import time
from enum import IntEnum
from types import SimpleNamespace

from . import object

# Update the (x, y, z) tuple to match minimum required version (0, 6, 4) means minimum 0.6.4
# By default we try to match the caffa-version
# However the application using caffa should set its own version which can be checked
# against by providing the script-version parameter
MIN_APP_VERSION = (1, 5, 0)
MAX_APP_VERSION = (1, 6, 99)


class SessionType(IntEnum):
    INVALID = 0
    REGULAR = 1
    OBSERVING = 2


class RestClient:
    number_of_attempts = 1
    delay_between_attempts = 0.5

    def __init__(
        self,
        hostname,
        port=50000,
        username="",
        password="",
        min_app_version=MIN_APP_VERSION,
        max_app_version=MAX_APP_VERSION,
        session_type=SessionType.REGULAR,
    ):
        self.hostname = hostname
        self.port = port
        self.basic_auth = requests.auth.HTTPBasicAuth(username, password)

        self.log = logging.getLogger("rpc-logger")
        self.mutex = threading.Lock()

        version_status = True
        errmsg = ""

        for i in range(0, RestClient.number_of_attempts):
            try:
                version_status, errmsg = self.check_version(
                    min_app_version, max_app_version
                )
                break
            except Exception as e:
                if i == RestClient.number_of_attempts - 1:
                    raise e from None
                else:
                    self.log.warning(
                        "Connection attempt %d/%d failed. Trying again in %f s",
                        i,
                        RestClient.number_of_attempts,
                        RestClient.delay_between_attempts,
                    )
                    time.sleep(RestClient.delay_between_attempts)
        if not version_status:
            raise RuntimeError(errmsg)

        self.session_uuid = self.create_session(session_type)

        if not self.session_uuid:
            raise RuntimeError("Failed to create session")
        self.log.debug("Session uuid: %s", self.session_uuid)
        self.keep_alive = True
        self.keepalive_thread = threading.Thread(target=self.send_keepalives)
        self.keepalive_thread.start()

    def quit(self):
        try:
            self.mutex.acquire()
            self.keep_alive = False
            if self.session_uuid:
                self._perform_delete_request("/sessions/" + self.session_uuid, "")
        finally:
            self.mutex.release()
        self.keepalive_thread.join()

    def _build_url(self, path, params=""):
        url = "http://" + self.hostname + ":" + str(self.port) + path
        if hasattr(self, "session_uuid"):
            url += "?session_uuid=" + self.session_uuid
            if len(params) > 0:
                url += "&" + params
        else:
            if len(params) > 0:
                url += "?" + params
        return url

    def _perform_get_request(self, path, params=""):
        url = self._build_url(path, params)
        try:
            response = requests.get(url, auth=self.basic_auth)
            response.raise_for_status()
            return response.text
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(
                "Failed GET request with error %s" % e.response.text
            ) from None
        except requests.exceptions.RequestException as e:
            raise RuntimeError("Failed GET request with error %s" % e) from None

    def _perform_options_request(self, path, params=""):
        url = self._build_url(path, params)
        try:
            response = requests.options(url, auth=self.basic_auth)
            response.raise_for_status()
            return response.text
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(
                "Failed OPTIONS request with error %s" % e.response.text
            ) from None
        except requests.exceptions.RequestException as e:
            raise RuntimeError("Failed OPTIONS request with error %s" % e) from None

    def _perform_delete_request(self, path, params):
        url = self._build_url(path, params)
        try:
            response = requests.delete(url, auth=self.basic_auth)
            response.raise_for_status()
            return response.text
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(
                "Failed DELETE request with error %s" % e.response.text
            ) from None
        except Exception as e:
            raise RuntimeError("Failed DELETE request with error %s" % e) from None

    def _perform_put_request(self, path, params="", body=""):
        url = self._build_url(path, params)
        try:
            response = requests.put(url, json=body, auth=self.basic_auth)
            response.raise_for_status()
            return response.text
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(
                "Failed PUT request with error %s" % e.response.text
            ) from None
        except Exception as e:
            raise RuntimeError("Failed PUT request with error %s" % e) from None

    def _perform_post_request(self, path, params="", body=""):
        url = self._build_url(path, params)
        try:
            response = requests.post(url, json=body, auth=self.basic_auth)
            response.raise_for_status()
            return response.text
        except requests.exceptions.HTTPError as e:
            self.log.error("Failed POST request with error " + e.response.text)
            raise e
        except requests.exceptions.RequestException as e:
            self.log.error("Failed POST request with error ", e)
            raise e

    def _json_text_to_object(self, text):
        return json.loads(text, object_hook=lambda d: SimpleNamespace(**d))

    def schema_root(self):
        return "/openapi.json"

    def schema_list(self):
        return self.schema(self.schema_root() + "/components/object_schemas")

    def schema(self, location):
        if location.startswith("#"):
            location = self.schema_root() + location[1:]
        schema = json.loads(self._perform_get_request(location))
        return schema

    def schema_location_from_keyword(self, keyword):
        return self.schema_root() + "/components/object_schemas/" + keyword

    def schema_properties(self, full_schema_location):
        properties = {}
        full_schema = self.schema(full_schema_location)
        if "allOf" in full_schema:
            for sub_schema in full_schema["allOf"]:
                if "properties" in sub_schema:
                    properties = properties | sub_schema["properties"]
                elif "$ref" in sub_schema:
                    properties = properties | self.schema_properties(sub_schema["$ref"])
        return properties

    def execute(self, object_uuid, method_name, arguments):
        value = json.loads(
            self._perform_post_request(
                path="/objects/" + object_uuid + "/methods/" + method_name,
                body=arguments,
            )
        )

        if isinstance(value, dict) and value:
            if "keyword" in value:
                schema_location = ""
                keyword = value["keyword"]
                if "$id" in value:
                    schema_location = value["$id"]
                else:
                    schema_location = self.schema_location_from_keyword(keyword)
                schema_properties = self.schema_properties(schema_location)
                cls = object.create_class(keyword, schema_properties)
                return cls(value, self, True)

        return value

    def app_info(self):
        return self._json_text_to_object(self._perform_get_request("/app/info"))

    def create_session(self, session_type):
        response = self._json_text_to_object(
            self._perform_post_request(path="/sessions/?type=" + session_type.name)
        )
        return response.uuid

    def session_metadata(self):
        response = self._json_text_to_object(
            self._perform_options_request(path="/sessions/" + self.session_uuid)
        )
        return response

    def send_keepalive(self):
        self._perform_put_request(path="/sessions/" + self.session_uuid)

    def send_keepalives(self):
        while True:
            time.sleep(0.5)
            try:
                self.mutex.acquire()
                if not self.keep_alive:
                    break
                else:
                    self.send_keepalive()
            finally:
                self.mutex.release()

    def document(self, document_id):
        assert len(document_id) > 0
        json_text = self._perform_get_request(
            "/documents/" + document_id, "skeleton=true"
        )
        json_object = json.loads(json_text)
        keyword = json_object["keyword"]

        schema_location = ""
        if "$id" in json_object:
            schema_location = json_object["$id"]
        else:
            schema_location = self.schema_location_from_keyword(keyword)

        schema_properties = self.schema_properties(schema_location)
        cls = object.create_class(keyword, schema_properties)

        return cls(json_text, self, False)

    def get_field_value(self, object_uuid, field_name):
        return self._perform_get_request(
            "/objects/" + object_uuid + "/fields/" + field_name
        )

    def set_field_value(self, object_uuid, field_name, json_value):
        return self._perform_put_request(
            path="/objects/" + object_uuid + "/fields/" + field_name, body=json_value
        )

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
        self.log.debug(
            "Requiring minimum %d.%d.%d",
            min_app_version[0],
            min_app_version[1],
            min_app_version[2],
        )
        self.log.debug(
            "Requiring maximum %d.%d.%d",
            max_app_version[0],
            max_app_version[1],
            max_app_version[2],
        )
        if (
            app_info.major_version,
            app_info.minor_version,
            app_info.patch_version,
        ) < min_app_version:
            return (
                False,
                "App Version v{}.{}.{} is too old. This client only supports version v{}.{}.{} and newer".format(
                    app_info.major_version,
                    app_info.minor_version,
                    app_info.patch_version,
                    min_app_version[0],
                    min_app_version[1],
                    min_app_version[2],
                ),
            )
        if (
            app_info.major_version,
            app_info.minor_version,
            app_info.patch_version,
        ) > max_app_version:
            return (
                False,
                "App Version v{}.{}.{} is too new. This client only supports up to and including v{}.{}.{}".format(
                    app_info.major_version,
                    app_info.minor_version,
                    app_info.patch_version,
                    max_app_version[0],
                    max_app_version[1],
                    max_app_version[2],
                ),
            )

        return True, ""
