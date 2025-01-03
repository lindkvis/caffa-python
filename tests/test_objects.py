import caffa
import json
import logging
import pytest

log = logging.getLogger("test_objects")
hostname = "127.0.0.1"


class TestObjects(object):
    def setup_method(self, method):
        self.testApp = caffa.RestClient(
            hostname, 50000, username="test", password="password"
        )

    def teardown_method(self, method):
        self.testApp.quit()

    def test_document(self):
        doc = self.testApp.document("testDocument")
        assert doc is not None
        print(str(doc))
        print("Found document: " + doc.keyword)
        schema_location = self.testApp.schema_location_from_keyword(doc.keyword)
        print("With schema: " + json.dumps(self.testApp.schema(schema_location)))

    def test_fields(self):
        doc = self.testApp.document("testDocument")
        print(doc)
        assert doc is not None
        keywords = dir(doc)
        assert len(keywords) > 0

        print("Found id: " + doc.id)
        assert doc.id == "testDocument"
        try:
            doc.id = "AnotherName"
            pytest.fail("Should have failed to write to document id, but succeeded!")
        except Exception:
            print("Got expected error")

        assert doc.id == "testDocument"

        try:
            doc.nonExistantField = "Test"
            pytest.fail("Should get an exception!")
        except Exception:
            print("Got the expected exception for field not found")

    def test_children(self):
        return

        doc = self.testApp.document("testDocument")
        assert doc is not None
        keywords = vars(doc)
        assert "demoObject" in keywords
        demo_object = doc.demoObject
        assert demo_object is not None
        log.debug("Found demo object: %s", str(demo_object))

    def test_methods(self):
        doc = self.testApp.document("testDocument")
        assert doc is not None

        demo_object = doc.demoObject
        assert demo_object is not None
        obj_methods = demo_object.methods()
        assert len(obj_methods) > 0

        for method in obj_methods:
            print("Found method: ", method.name(), dir(method))

        demo_object.copyValues(
            intValue=41, doubleValue=99.0, stringValue="AnotherValue"
        )

        assert demo_object.doubleField == 99.0
        assert demo_object.intField == 41
        assert demo_object.stringField == "AnotherValue"

        demo_object.copyValues(42, 97.0, "AnotherValue2")

        assert demo_object.doubleField == 97.0
        assert demo_object.intField == 42
        assert demo_object.stringField == "AnotherValue2"

        demo_object.setIntVector(intVector=[1, 2, 97])

        assert demo_object.get("proxyIntVector") == [1, 2, 97]

        values = demo_object.getIntVector()

        assert values == [1, 2, 97]

    def test_non_existing_field(self):
        doc = self.testApp.document("testDocument")
        assert doc is not None
        try:
            doc.does_not_exist
            pytest.fail("Should have had exception, but got none!")
        except Exception as e:
            log.info(
                "Got expected exception when trying to read a field which doesn't exist: '{0}'".format(
                    e
                )
            )

    def test_int_vector(self):
        doc = self.testApp.document("testDocument")
        assert doc is not None

        demo_object = doc.get("demoObject")
        demo_object.set("proxyIntVector", [1, 4, 42])
        assert demo_object.get("proxyIntVector") == [1, 4, 42]

    def test_float_vector(self):
        doc = self.testApp.document("testDocument")
        assert doc is not None

        demo_object = doc.get("demoObject")
        demo_object.floatVector = [1.0, 3.0, -42.0]
        assert demo_object.floatVector == [1.0, 3.0, -42.0]

    def test_app_enum(self):
        doc = self.testApp.document("testDocument")
        assert doc is not None
        demo_object = doc.get("demoObject")
        demo_object.set("enumField", "T3")
        assert demo_object.get("enumField") == "T3"

        try:
            demo_object.set("enumField", "InvalidValue")
            pytest.fail("Should have failed to set invalid value")

        except Exception as e:
            log.info(
                "Got expected exception when trying to assign an invalid enum value: '{0}'".format(
                    e
                )
            )
