import logging
import sys
import pytest
import caffa

log = logging.getLogger("test_client")


def test_connection():
    try:
        client = caffa.Client("localhost", username="test", password="password")
        assert client is not None
        log.info("Client connection worked")
    except Exception as e:
        pytest.fail("Failed with exception {0}".format(e))
    client.cleanup()


def test_app_info():
    client = caffa.Client("localhost", username="test", password="password")
    assert client is not None
    log.info("Client connection worked")
    app_info = client.app_info()
    assert app_info is not None
    assert app_info.name != ""
    app_string = (
        app_info.name
        + " v"
        + str(app_info.major_version)
        + "."
        + str(app_info.minor_version)
        + "."
        + str(app_info.patch_version)
    )
    log.info("App info: %s", app_string)

    client.cleanup()


def test_schemas():
    try:
        client = caffa.Client("localhost", username="test", password="password")
        assert client is not None
        schemas = client.schema_list()
        print("ALL SCHEMAS: ", schemas)
    except Exception as e:
        pytest.fail("Failed with exception {0}".format(e))
    client.cleanup()
