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

import AppInfo_pb2
import AppInfo_pb2_grpc

import ObjectService_pb2
import ObjectService_pb2_grpc

from . import object

# Update the (x, y, z) tuple to match minimum required version (0, 6, 4) means minimum 0.6.4
REQUIRED_CAFFA_VERSION = (0, 13, 0)


class Client:
    def __init__(self, hostname, port=50000):
        self.channel = grpc.insecure_channel(hostname + ":" + str(port))
        self.app_info_stub = AppInfo_pb2_grpc.AppStub(self.channel)
        self.object_stub = ObjectService_pb2_grpc.ObjectAccessStub(
            self.channel)
        self.hostname = hostname
        self.port_number = port
        self.log = logging.getLogger("grpc-logger")

        if not self.check_version():
            raise RuntimeError("Server version is too old")

        msg = AppInfo_pb2.NullMessage()
        self.session_uuid = self.app_info_stub.CreateSession(msg).uuid
        if not self.session_uuid:
            raise RuntimeError("Failed to create session")
        self.log.debug("Session uuid: %s", self.session_uuid)

    def app_info(self):
        msg = AppInfo_pb2.NullMessage()
        return self.app_info_stub.GetAppInfo(msg)

    def cleanup(self):
        msg = AppInfo_pb2.SessionMessage(uuid=self.session_uuid)
        self.app_info_stub.DestroySession(msg)

    def send_keepalive(self):
        msg = AppInfo_pb2.SessionMessage(uuid=self.session_uuid)
        self.app_info_stub.KeepSessionAlive(msg)

    def document(self, document_id=""):
        session = AppInfo_pb2.SessionMessage(uuid=self.session_uuid)

        doc_request = ObjectService_pb2.DocumentRequest(
            document_id=document_id, session=session
        )
        rpc_document = self.object_stub.GetDocument(doc_request)
        if rpc_document is not None:
            return object.Object(rpc_document.json, self.session_uuid, self.channel)
        return None

    def check_version(self):
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
        ) < REQUIRED_CAFFA_VERSION:
            self.log.error(
                "Caffa Version %d.%d.%d is too old. Script requires minimum %d.%d.%d",
                app_info.major_version,
                app_info.minor_version,
                app_info.patch_version,
                REQUIRED_CAFFA_VERSION[0],
                REQUIRED_CAFFA_VERSION[1],
                REQUIRED_CAFFA_VERSION[2],
            )
            return False
        if (
            app_info.major_version,
            app_info.minor_version,
            app_info.patch_version,
        ) > REQUIRED_CAFFA_VERSION:
            self.log.warning(
                "Caffa Version %d.%d.%d is newer than the script version %d.%d.%d . This may or may not work!",
                app_info.major_version,
                app_info.minor_version,
                app_info.patch_version,
                REQUIRED_CAFFA_VERSION[0],
                REQUIRED_CAFFA_VERSION[1],
                REQUIRED_CAFFA_VERSION[2],
            )
        return True
