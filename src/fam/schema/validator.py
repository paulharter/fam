import jsonschema
import os
import json
import inspect
import copy
from fam.blud import GenericObject
from fam.constants import *



from .writer import createJsonSchema


class ModelValidator(object):

    def __init__(self, mapper, schema_dir=None, classes=None, modules=None):
        self.reference_store = {}
        self.ref_schemas = {}
        self.schema_dir = schema_dir
        if mapper is not None:
            self._add_classes(mapper)
        if classes is not None:
            self._add_classes(classes)

    def iter_schemas(self):

        for k, schema in self.ref_schemas.items():
            namespace = k[0]
            typename = k[1]
            yield namespace, typename, schema


    def _add_classes(self, classes):
        for cls in classes:
            type_name = cls.__name__.lower()
            namespace = cls.namespace.lower()
            self.add_schema(namespace, type_name, cls)


    def add_schema(self, namespace, type_name, cls):

        schema = createJsonSchema(cls)

        if self.schema_dir is not None:
            schema["id"] = self._check_for_changes(namespace, type_name, schema)
        else:
            schema["id"] = "%s/%s" % (namespace, type_name)

        jsonschema.Draft4Validator.check_schema(schema)
        self.reference_store[schema["id"]] = schema
        self.ref_schemas[(namespace, type_name)] = schema


    def schema_id_for(self, namespace, type_name):
        schema = self.ref_schemas.get((namespace, type_name))
        if schema:
            # print schema["id"]
            return schema["id"]
        return None


    def validate(self, doc):

        schema_id = doc.get("schema")
        if schema_id is None:
            namespace = doc.get("namespace")
            type_name = doc.get("type")

            if namespace and type_name:
                schema_id = self.schema_id_for(namespace, type_name)

        if schema_id:
            schema = self._look_schema_with_lazy_load(schema_id)
            resolver = jsonschema.RefResolver(schema_id, schema, store=self.reference_store)
            validator = jsonschema.Draft4Validator(schema, resolver=resolver)
            validator.validate(doc)


    def _look_schema_with_lazy_load(self, schema_id):
        schema = self.reference_store.get(schema_id)
        if schema is None:
            schema = self._schema_from_id(schema_id)
            self.reference_store[schema_id] = schema

        return schema

        return ''.join(diff)

    def _schemata_are_equal(self, schema_a, schema_b):


        if schema_b is None:
            return False

        # expects dicts
        # don't mess with the input
        dupe_a = copy.deepcopy(schema_a)
        dupe_b = copy.deepcopy(schema_b)

        # remove ids before comparison
        if "id" in dupe_a:
            del dupe_a["id"]

        if "id" in dupe_b:
            del dupe_b["id"]

        return dupe_a == dupe_b


    def _type_dir(self, namespace, type_name):
        ns = namespace.replace("/", "_")
        dir_path = os.path.join(self.schema_dir, "schemata", ns, type_name)
        return dir_path

    def _schema_path(self, namespace, type_name, timestamp):
        type_dir = self._type_dir(namespace, type_name)
        dir_path = os.path.join(type_dir, timestamp)
        return dir_path


    def _timestamp_from_schema_id(self, schema_id):
        namespace, typename, timestamp = self._namespace_typename_timestamp_from_schema_id(schema_id)
        return timestamp


    def _schema_path_from_id(self, schema_id):
        namespace, type_name, timestamp = self._namespace_typename_timestamp_from_schema_id(schema_id)
        return self._schema_path(namespace, type_name, timestamp)


    def _schema_from_id(self, schema_id):
        schema_path = self._schema_path_from_id(schema_id)
        return self.schema_at_schema_path(schema_path)


    def _namespace_typename_timestamp_from_schema_id(self, schema_id):

        parts = schema_id.split("/")
        namespace = "/".join(parts[:-3])
        type_name = parts[-3]
        timestamp = parts[-2]

        return namespace, type_name, timestamp

    def schema_at_schema_path(self, schema_path):
        schema_path = os.path.join(schema_path, "schema.json")
        with open(schema_path, "r") as f:
            return json.loads(f.read())


    def _previous_schema(self, namespace, type_name):

        dir_path = self._type_dir(namespace, type_name)

        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        filenames = os.listdir(dir_path)
        if not filenames:
            return None

        most_recent_filename = sorted(filenames)[-1]
        return self.schema_at_schema_path(os.path.join(dir_path, most_recent_filename))


    def _check_for_changes(self, namespace, type_name, schema):

        existing_schema = self._previous_schema(namespace, type_name)

        if existing_schema is None:
            raise NotImplementedError("The schema for %s %s is missing" % (namespace, type_name))
        else:
            # compare the latest schema with the most recent
            if self._schemata_are_equal(schema, existing_schema):
                return existing_schema["id"]
            else:
                raise NotImplementedError("The schema for %s %s is not up to date" % (namespace, type_name))



