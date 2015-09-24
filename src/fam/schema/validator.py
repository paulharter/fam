import jsonschema
import os
import json
import inspect
from fam.blud import GenericObject

from .writer import createJsonSchema


class ModelValidator(object):

    def __init__(self, classes=[], modules=[], schema_folder=None):

        self.reference_store = {}

        if classes is not None:
            self._add_classes(classes)

        if modules is not None:
            self._add_modules(modules)

        if schema_folder is not None:
            os.path.walk(schema_folder, self.add_file, None)

    def add_file(self, _ctx, dir_name, names):
        for file_name in names:
            file_path = os.path.join(dir_name, file_name)
            if os.path.isfile(file_path):
                if file_path.endswith(".json"):
                    with open(file_path, "r") as f:
                        schema = json.loads(f.read())
                        self.add_schema(schema)

    def _add_classes(self, classes):
        for cls in classes:
            self.add_schema(createJsonSchema(cls))

    def _add_modules(self, modules):
        for module in modules:
            classes = []
            for k, obj in module.__dict__.iteritems():
                if inspect.isclass(obj):
                    if issubclass(obj, GenericObject):
                        if obj != GenericObject:
                            if not k.startswith("_"):
                                classes.append(obj)
            self._add_classes(classes)

    def add_schema(self, schema):
        jsonschema.Draft4Validator.check_schema(schema)
        self.reference_store[schema["id"]] = schema

    def validate(self, doc):

        type_name = doc.get("type")
        namespace = doc.get("namespace")

        if type_name:
            schema_id = "%s::%s" % (namespace, type_name)
            schema = self.reference_store[schema_id]
            resolver = jsonschema.RefResolver(schema_id, schema, store=self.reference_store)
            validator = jsonschema.Draft4Validator(schema, resolver=resolver)
            validator.validate(doc)

    def write_out_schemata(self, dir):

        for schema_id, schema in self.reference_store.iteritems():
            namespace, name = schema_id.split("::")
            dirname = os.path.join(dir, namespace)
            filename = os.path.join(dirname, "%s.%s.json" % (namespace.replace("/", "_"), name))
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            if os.path.exists(filename):
                os.remove(filename)
            with open(filename, "w") as f:
                f.write(json.dumps(schema, indent=4, sort_keys=True))



