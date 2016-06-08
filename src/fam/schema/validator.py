import jsonschema
import os
import json
import inspect
import datetime
import pytz
import copy
import difflib
from fam.blud import GenericObject
from fam.constants import *



from .writer import createJsonSchema


class ModelValidator(object):

    def __init__(self, classes=None, modules=None, schema_dir=None):

        self.reference_store = {}
        self.lookup_store = {}
        self.schema_dir = schema_dir
        self.timestamp = self._now_timestamp()
        self.changes = []

        if classes is not None:
            self._add_classes(classes)

        if modules is not None:
            self._add_modules(modules)


    def _add_classes(self, classes):
        for cls in classes:
            type_name = cls.__name__.lower()
            namespace = cls.namespace.lower()
            self.add_schema(namespace, type_name, createJsonSchema(cls))


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


    def add_schema(self, namespace, type_name, schema):
        self._get_timestamped_id(self.schema_dir, namespace, type_name, schema)

        jsonschema.Draft4Validator.check_schema(schema)
        self.reference_store[schema["id"]] = schema
        self.lookup_store[(namespace, type_name)] = schema


    def schema_id_for(self, namespace, type_name):
        schema = self.lookup_store.get((namespace, type_name))
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
            schema = self.reference_store[schema_id]
            resolver = jsonschema.RefResolver(schema_id, schema, store=self.reference_store)
            validator = jsonschema.Draft4Validator(schema, resolver=resolver)
            validator.validate(doc)


    def _now_timestamp(self):
        utc = pytz.utc
        dt = datetime.datetime.now(utc)
        # force to utc and then to RFC 3339
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=utc)
        else:
            dt = dt.astimezone(utc)
        ts = dt.strftime("%Y%m%d-%H%M%S-%f")
        return ts

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


    def _most_recent_schema(self, dir):
        filenames = os.listdir(dir)
        if not filenames:
            return None
        most_recent_filename = sorted(filenames)[-1]
        file_path = os.path.join(dir, most_recent_filename)
        with open(file_path, "r") as f:
            return json.loads(f.read())


    def _unidiff_output(self, expected, actual):
        """
        Helper function. Returns a string containing the unified diff of two multiline strings.
        """
        expected=expected.splitlines(1)
        actual=actual.splitlines(1)
        diff=difflib.unified_diff(expected, actual)

        return ''.join(diff)


    def _get_timestamped_id(self, schema_dir, namespace, type_name, schema):

            if schema_dir is None:
                most_recent_schema = None
                dir_path = None
            else:
                dir_path = os.path.join(schema_dir, "schemata", namespace, type_name)
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path)
                most_recent_schema = self._most_recent_schema(dir_path)


             # compare the latest schema with the most recent
            if self._schemata_are_equal(schema, most_recent_schema):
                diff = None
                schema["id"] = most_recent_schema["id"]
            else:
                # write the new schema
                if schema_dir is not None:
                    schema["id"] = "{}/{}/{}.json#".format(namespace, type_name, self.timestamp)
                    schema_path = os.path.join(dir_path, "{}.json".format(self.timestamp))
                    current_schema_string = json.dumps(schema, indent=4, sort_keys=True)
                    with open(schema_path, "w") as f:
                        f.write(current_schema_string)
                else:
                    schema["id"] = "{}/{}".format(namespace, type_name)

                if most_recent_schema is None:
                    diff = None
                else:
                    existing_schema_string = json.dumps(most_recent_schema, indent=4, sort_keys=True)
                    diff = self._unidiff_output(existing_schema_string, current_schema_string)

            if diff:
                self.changes.append((namespace, type_name, diff))

            return schema["id"]




    def write_out_schemata(self):

        if self.changes:
            print "writing changes"
            mutation_dir = os.path.join(self.schema_dir, "mutations")
            if not os.path.exists(mutation_dir):
                os.makedirs(mutation_dir)
            mutation_path = os.path.join(mutation_dir, "{}.py".format(self.timestamp))
            with open(mutation_path, "w") as f:
                for namespace, type_name, diff in self.changes:
                    mutation = "**** {} {} schema changed ****\n\n{}".format(namespace, type_name, diff)
                    f.write('"""\n{}"""\n\n\n'.format(mutation))
#                     do = """@mutate_do("{}", "{}")
# def do_{}(doc):
#     \"\"\" Write mutation code here \"\"\"
#
#
# """
#                     f.write(do.format(namespace, type_name, type_name))
#                     undo = """@mutate_undo("{}", "{}")
# def undo_{}(doc):
#     \"\"\" Write code to undo mutation here \"\"\"
#
#
# """
#                     f.write(undo.format(namespace, type_name, type_name))

