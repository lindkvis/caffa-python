from __future__ import annotations
from collections import UserDict
import schemas_DemoObject
from collections import UserList
import schemas_InheritedDemoObj

class Object(UserDict):
    """This represents a JSON object.
    """
    
    # This object makes use of an external schema specified at #/schemas/DemoObject
    class FileNameProperty(object):
        """ This class is a schema-validating wrapper around a string.
        """

        def __init__(self, value):
            self.Set(value)

        @staticmethod
        def _Validate(value):
            """Ensures that the provided string value meets all the schema constraints.
            """
            if not isinstance(value, str):
                raise ValueError("Passed value '{}' was not a string".format(value))          

        def Set(self, new_value) -> Object.FileNameProperty:
            if isinstance(new_value, type(self)):
                self._value = new_value._value
            elif isinstance(new_value, str):
                self._Validate(new_value)
                self._value = new_value
            else:
                raise TypeError("The provided type was not a Object.FileNameProperty or a str")
            return self

        def Get(self) -> str:
            return self._value

        def Serializable(self) -> str:
            return self.Get()

    class IdProperty(object):
        """ This class is a schema-validating wrapper around a string.
        """

        def __init__(self, value):
            self.Set(value)

        @staticmethod
        def _Validate(value):
            """Ensures that the provided string value meets all the schema constraints.
            """
            if not isinstance(value, str):
                raise ValueError("Passed value '{}' was not a string".format(value))          

        def Set(self, new_value) -> Object.IdProperty:
            if isinstance(new_value, type(self)):
                self._value = new_value._value
            elif isinstance(new_value, str):
                self._Validate(new_value)
                self._value = new_value
            else:
                raise TypeError("The provided type was not a Object.IdProperty or a str")
            return self

        def Get(self) -> str:
            return self._value

        def Serializable(self) -> str:
            return self.Get()

    class InheritedDemoObjectsProperty (UserList):
        """ This represents a JSON array.
        """
        
        def __init__(self, the_list=None):
            """Initializer for array.
            """
            if not hasattr(the_list, '__iter__'):
                raise TypeError("The provided list was not iterable")

            self.the_list = the_list

            if isinstance(the_list, type(self)):
                super().__init__(the_list.data)
            else:
                super().__init__([schemas_InheritedDemoObj.InheritedDemoObj(x) for x in the_list])

        def Append(self, new_value) -> InheritedDemoObjectsProperty:
            self.data.append(schemas_InheritedDemoObj.InheritedDemoObj(new_value))
            return self

        def Serializable(self) -> list:
            return self.data

    class KeywordProperty(object):
        """ This class is a schema-validating wrapper around a string.
        """

        def __init__(self, value):
            self.Set(value)

        @staticmethod
        def _Validate(value):
            """Ensures that the provided string value meets all the schema constraints.
            """
            if not isinstance(value, str):
                raise ValueError("Passed value '{}' was not a string".format(value))          

        def Set(self, new_value) -> Object.KeywordProperty:
            if isinstance(new_value, type(self)):
                self._value = new_value._value
            elif isinstance(new_value, str):
                self._Validate(new_value)
                self._value = new_value
            else:
                raise TypeError("The provided type was not a Object.KeywordProperty or a str")
            return self

        def Get(self) -> str:
            return self._value

        def Serializable(self) -> str:
            return self.Get()

    class UuidProperty(object):
        """ This class is a schema-validating wrapper around a string.
        """

        def __init__(self, value):
            self.Set(value)

        @staticmethod
        def _Validate(value):
            """Ensures that the provided string value meets all the schema constraints.
            """
            if not isinstance(value, str):
                raise ValueError("Passed value '{}' was not a string".format(value))          

        def Set(self, new_value) -> Object.UuidProperty:
            if isinstance(new_value, type(self)):
                self._value = new_value._value
            elif isinstance(new_value, str):
                self._Validate(new_value)
                self._value = new_value
            else:
                raise TypeError("The provided type was not a Object.UuidProperty or a str")
            return self

        def Get(self) -> str:
            return self._value

        def Serializable(self) -> str:
            return self.Get()


    def __init__(self, data=None, **kwargs):
        """Initialization for the Object object.
        It can be initialized with an object, or by passing each
        object property as a keyword argument.
        """
        new_data = {}
        try:
            prop = data["demoObject"] if ("demoObject" in data) else kwargs["demoObject"]
            if not isinstance(prop, schemas_DemoObject.DemoObject):
                new_data["demoObject"] = schemas_DemoObject.DemoObject(prop)
        except KeyError:
            pass
        try:
            prop = data["fileName"] if ("fileName" in data) else kwargs["fileName"]
            if not isinstance(prop, self.FileNameProperty):
                new_data["fileName"] = self.FileNameProperty(prop)
        except KeyError:
            pass
        try:
            prop = data["id"] if ("id" in data) else kwargs["id"]
            if not isinstance(prop, self.IdProperty):
                new_data["id"] = self.IdProperty(prop)
        except KeyError:
            pass
        try:
            prop = data["inheritedDemoObjects"] if ("inheritedDemoObjects" in data) else kwargs["inheritedDemoObjects"]
            if not isinstance(prop, self.InheritedDemoObjectsProperty):
                new_data["inheritedDemoObjects"] = self.InheritedDemoObjectsProperty(prop)
        except KeyError:
            pass
        try:
            prop = data["keyword"] if ("keyword" in data) else kwargs["keyword"]
            if not isinstance(prop, self.KeywordProperty):
                new_data["keyword"] = self.KeywordProperty(prop)
        except KeyError:
            raise ValueError("Missing property 'keyword'")
        try:
            prop = data["uuid"] if ("uuid" in data) else kwargs["uuid"]
            if not isinstance(prop, self.UuidProperty):
                new_data["uuid"] = self.UuidProperty(prop)
        except KeyError:
            pass
        super().__init__(new_data)

    def GetDemoObject(self):
        return self.data["demoObject"]
    
    def SetDemoObject(self, new_value) -> Object:
        if not isinstance(new_value, schemas_DemoObject.DemoObject):
            self.data["demoObject"] = schemas_DemoObject.DemoObject(new_value)
        else:
            self.data["demoObject"] = new_value
        return self

    def GetFileName(self):
        return self.data["fileName"]
    
    def SetFileName(self, new_value) -> Object:
        if not isinstance(new_value, self.FileNameProperty):
            self.data["fileName"] = self.FileNameProperty(new_value)
        else:
            self.data["fileName"] = new_value
        return self

    def GetId(self):
        return self.data["id"]
    
    def SetId(self, new_value) -> Object:
        if not isinstance(new_value, self.IdProperty):
            self.data["id"] = self.IdProperty(new_value)
        else:
            self.data["id"] = new_value
        return self

    def GetInheritedDemoObjects(self):
        return self.data["inheritedDemoObjects"]
    
    def SetInheritedDemoObjects(self, new_value) -> Object:
        if not isinstance(new_value, self.InheritedDemoObjectsProperty):
            self.data["inheritedDemoObjects"] = self.InheritedDemoObjectsProperty(new_value)
        else:
            self.data["inheritedDemoObjects"] = new_value
        return self

    def GetKeyword(self):
        return self.data["keyword"]
    
    def SetKeyword(self, new_value) -> Object:
        if not isinstance(new_value, self.KeywordProperty):
            self.data["keyword"] = self.KeywordProperty(new_value)
        else:
            self.data["keyword"] = new_value
        return self

    def GetUuid(self):
        return self.data["uuid"]
    
    def SetUuid(self, new_value) -> Object:
        if not isinstance(new_value, self.UuidProperty):
            self.data["uuid"] = self.UuidProperty(new_value)
        else:
            self.data["uuid"] = new_value
        return self

    def Serializable(self) -> dict:
        return self.data
