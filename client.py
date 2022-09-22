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
import logging
import time
import threading

import App_pb2
import App_pb2_grpc

import ObjectService_pb2
import ObjectService_pb2_grpc

from . import object

# Update the (x, y, z) tuple to match minimum required version (0, 6, 4) means minimum 0.6.4
# By default we try to match the caffa-version
# However the application using caffa should set its own version which can be checked
# against by providing the script-version parameter
REQUIRED_CAFFA_VERSION = (0, 14, 0)


class Client:
    def __init__(self, hostname, port=50000, script_version=REQUIRED_CAFFA_VERSION, session_type=App_pb2.SessionType.REGULAR):
        self.channel = grpc.insecure_channel(hostname + ":" + str(port))
        self.app_info_stub = App_pb2_grpc.AppStub(self.channel)
        self.object_stub = ObjectService_pb2_grpc.ObjectAccessStub(
            self.channel)
        self.hostname = hostname
        self.port_number = port
        self.log = logging.getLogger("grpc-logger")
        self.mutex = threading.Lock()

        if not self.check_version(script_version):
            raise RuntimeError("Server version is too old")

        msg = App_pb2.SessionParameters(type=session_type)
        self.session_uuid = self.app_info_stub.CreateSession(msg).uuid
        if not self.session_uuid:
            raise RuntimeError("Failed to create session")
        self.log.debug("Session uuid: %s", self.session_uuid)
        self.keep_alive = True
        self.keepalive_thread = threading.Thread(target=self.send_keepalives)
        self.keepalive_thread.start()

    def app_info(self):
        msg = App_pb2.NullMessage()
        return self.app_info_stub.GetAppInfo(msg)

    def cleanup(self):
        try:
            self.mutex.acquire()
            self.keep_alive = False
            msg = App_pb2.SessionMessage(uuid=self.session_uuid)
            self.app_info_stub.DestroySession(msg)
            self.app_info_stub = None
        finally:
            self.mutex.release()

    def send_keepalive(self):
        msg = App_pb2.SessionMessage(uuid=self.session_uuid)
        self.app_info_stub.KeepSessionAlive(msg)

    def send_keepalives(self):
        while True:
            time.sleep(0.5)
            try:
                self.mutex.acquire()
                if not self.keep_alive:
                    break;
                elif self.app_info_stub is not None:
                    self.send_keepalive()
                else:
                    break
            finally:
                self.mutex.release()

    def document(self, document_id=""):
        session = App_pb2.SessionMessage(uuid=self.session_uuid)

        doc_request = ObjectService_pb2.DocumentRequest(
            document_id=document_id, session=session
        )
        rpc_document = self.object_stub.GetDocument(doc_request)
        if rpc_document is not None:
            return object.Object(rpc_document.json, self.session_uuid, self.channel)
        return None

    def check_version(self, script_version):
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
        ) < script_version:
            self.log.error(
                "Caffa Version %d.%d.%d is too old. Script requires minimum %d.%d.%d",
                app_info.major_version,
                app_info.minor_version,
                app_info.patch_version,
                script_version[0],
                script_version[1],
                script_version[2],
            )
            return False
        if (
            app_info.major_version,
            app_info.minor_version,
            app_info.patch_version,
        ) > script_version:
            self.log.warning(
                "Caffa Version %d.%d.%d is newer than the script version %d.%d.%d . This may or may not work!",
                app_info.major_version,
                app_info.minor_version,
                app_info.patch_version,
                script_version[0],
                script_version[1],
                script_version[2],
            )
        return True
