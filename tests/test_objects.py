import logging
import sys
import pytest
import caffa

log = logging.getLogger("test_objects")


class TestObjects(object):
    def setup_method(self, method):
        self.testApp = caffa.Client("localhost", 50000)

    def teardown_method(self, method):
        self.testApp.cleanup()

    def test_document(self):
        doc = self.testApp.document()
        assert doc is not None
        log.debug(doc.dump())
        log.debug("Found document: " + doc.keyword())
        log.debug("Found filename: " + doc.fileName)
        assert doc.fileName == "dummyFileName"
        try:
            doc.fileName = "TestValue"
        except Exception as e:
            pytest.fail("Failed with exception {0}", e)
        assert doc.fileName == "TestValue"
        doc.fileName = "dummyFileName"

    def test_fields(self):
        doc = self.testApp.document()
        assert doc is not None
        keywords = doc.field_keywords()
        assert len(keywords) > 0
        for keyword in keywords:
            log.debug("Found field: " + keyword)

    def test_children(self):
        doc = self.testApp.document()
        assert doc is not None
        keywords = doc.field_keywords()
        assert "demoObject" in keywords
        demo_object = doc.get("demoObject")
        assert demo_object is not None
        log.debug("Found demo object: %s", demo_object.dump())

    def test_methods(self):
        doc = self.testApp.document()
        assert doc is not None
        doc_methods = doc.methods()
        assert len(doc_methods) == 0
        demo_object = doc.get("demoObject")
        assert demo_object is not None
        obj_methods = demo_object.methods()
        assert len(obj_methods) > 0

        method = obj_methods[0]
        log.debug("Found method: %s", method.dump())

        method.doubleArgument = 99.0
        method.intArgument = 41
        method.stringArgument = "AnotherValue"
        method.intArrayArgument = [1, 2, 97]

        result = demo_object.execute(method)
        assert result is not None
        assert result.get("status")

        assert demo_object.get("doubleField") == 99.0
        assert demo_object.get("intField") == 41
        assert demo_object.get("stringField") == "AnotherValue"
        assert demo_object.get("proxyIntVector") == [1, 2, 97]

    def test_non_existing_field(self):
        doc = self.testApp.document()
        assert doc is not None
        try:
            value = doc.does_not_exist
            pytest.fail("Should have had exception, but got none!")
        except Exception as e:
            log.info(
                "Got expected exception when trying to read a field which doesn't exist: '{0}'".format(e))

    def test_int_vector(self):
        doc = self.testApp.document()
        assert doc is not None

        demo_object = doc.get("demoObject")
        for field in demo_object.field_keywords():
            log.debug("Found field: " + field)
        demo_object.set("proxyIntVector", [1, 4, 42])
        assert demo_object.get("proxyIntVector") == [1, 4, 42]

    def test_float_vector(self):
        doc = self.testApp.document()
        assert doc is not None

        demo_object = doc.get("demoObject")
        demo_object.floatVector = [1.0, 3.0, -42.0]
        assert demo_object.floatVector == [1.0, 3.0, -42.0]

    def test_app_enum(self):
        doc = self.testApp.document()
        assert doc is not None
        demo_object = doc.get("demoObject")
        demo_object.set("enumField", "T3")
        assert demo_object.get("enumField") == "T3"

        try:
            demo_object.set("enumField", "InvalidValue")
            pytest.fail("Should have failed to set invalid value")

        except Exception as e:
            log.info(
                "Got expected exception when trying to assign an invalid enum value: '0'".format(e))
