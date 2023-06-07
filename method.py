import json
import logging

class Method(object):
    _log = logging.getLogger("caffa-method")

    def __init__(self, self_object, json_string):
        self._object = self_object
        self._json = json.loads(json_string)

    def keyword(self):
        return self._json["keyword"]

    def execute(self, **parameters):
        json_with_params = self._json

        for key, value in parameters.items():
            for entry in json_with_params["arguments"]:
                if entry["keyword"] == key:
                    entry["value"] = value

        result_string = self._object.execute(json_with_params)
        json_result = json.loads(result_string)
        if "value" in json_result:
            return json_result["value"]
        return None

    def dump(self):
        return json.dumps(self._json)

