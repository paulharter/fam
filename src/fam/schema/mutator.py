import os
import json
import datetime
import pytz
import difflib
import jsonschema
from importlib.machinery import SourceFileLoader

from fam.blud import FamObject
from fam.database.couchdb import ResultWrapper
from fam.schema.writer import createJsonSchema
from fam.schema.validator import ModelValidator


class FamMutator(ModelValidator):

    def __init__(self, mapper, schema_dir):

        self.logable = None

        # structures for indexing mutations
        self.all_mutations = {}
        self.mutation_histories = {}
        self.live_schemas = {}

        super(FamMutator, self).__init__(mapper, schema_dir=schema_dir)


    def log(self, msg, level="debug"):
        if self.logable is None:
            print(msg)
        else:
            self.logable.log(msg, level=level)

    def add_schema(self, namespace, type_name, cls):
        schema = createJsonSchema(cls)
        jsonschema.Draft4Validator.check_schema(schema)
        self.live_schemas[(namespace, type_name)] = schema


    def preflight(self):
        self.update_ref_schemata()
        self.check_not_implemented_mutations()


    def update_ref_schemata(self):

        self.changes = []
        timestamp = self._now_timestamp()

        for k, schema in self.live_schemas.items():
            namespace = k[0]
            type_name = k[1]

            previous_schema = self._previous_schema(namespace, type_name)

            # compare the latest schema with the most recent
            if self._schemata_are_equal(schema, previous_schema):
                self.ref_schemas[(namespace, type_name)] = previous_schema
                self.reference_store[previous_schema["id"]] = previous_schema
            else:
                jsonschema.Draft4Validator.check_schema(schema)
                self.changes.append((namespace, type_name, timestamp))
                self._add_new_schema(namespace, type_name, schema, previous_schema, timestamp)
                self.ref_schemas[(namespace, type_name)] = schema
                self.reference_store[schema["id"]] = schema



    def check_not_implemented_mutations(self):

        self._index_all_mutations()

        not_implemented = []

        for k, history in self.mutation_histories.items():
            namespace = k[0]
            typename = k[1]

            for timestamp in history:
                mutate = self._lazy_get_mutation_func(namespace, typename, timestamp, "mutate")

                try:
                    mutate(self.db, None)
                except NotImplementedError as e:
                    print(e)
                    not_implemented.append(e)
                except Exception as e:
                    pass

        if not_implemented:
            raise NotImplementedError("There were NotImplementedErrors")


    def do_mutation(self, namespace, typename, history, events):

        mutated = False

        if len(history) > 0:
            for obj in self._iter_of_of_date_obj(namespace, typename, history[-1]):
                timestamp = self._timestamp_from_schema_id(obj.schema)
                mutations = self._mutations_to_apply(namespace, typename, timestamp, history)
                for mutation in mutations:
                    mutation(self.db, obj)
                events.append(obj.key)
                mutated = True

        return mutated


    def mutate_type(self, namespace, typename):

        history = self.mutation_histories.get((namespace, typename))
        events = []
        mutated = self.do_mutation(namespace, typename, history, events)
        count = len(events)
        if count > 0:
            self.log("Mutated %s %ss" % (count, typename), "info")


    def record_mutation(self, timestamp, typename, count):
        self.log("Mutated %s %ss up to %s" % (count, typename, timestamp), "info")


    def mutate(self):

        mutation_events = {}
        mutated = False

        for k, history in self.mutation_histories.items():
            namespace = k[0]
            typename = k[1]
            events = []
            if history:
                mutation_events[k] = (events, history[-1])
                mutated = self.do_mutation(namespace, typename, history, events)

        for k, info in mutation_events.items():
            count = len(info[0])
            if count > 0:
                self.record_mutation(info[1], typename, count)

        return mutated


    # def _ensure_schema_view(self):
    #
    #     """
    #     Adds a view to the database to index documents by schema
    #
    #     """
    #
    #     design_id = "_design/mutator"
    #     db_type = self.db.database_type
    #
    #     if db_type == "couchdb":
    #         map_func = "function(doc) {if(doc.schema !== undefined){emit(doc.schema, doc);}}"
    #     elif db_type == "sync_gateway":
    #         map_func = "function(doc, meta) {doc._rev = meta.rev; if(doc.schema !== undefined){emit(doc.schema, doc);}}"
    #     else:
    #         raise Exception("unsupported db type: ", self.db.database_type)
    #
    #     design_doc = {"views": {
    #         "schema": {"map": map_func},
    #     }}

        # self.db.ensure_design_doc(design_id, design_doc)



    def _index_all_mutations(self):

        """
        fills in self.mutation_histories with ordered lists of timestamps starting with oldest
        """

        for k, schema in self.ref_schemas.items():
            namespace = k[0]
            type_name = k[1]

            type_dir = self._type_dir(namespace, type_name)
            timestamps = os.listdir(type_dir)
            sorted_timestamps = sorted(timestamps)
            history = [ts for ts in sorted_timestamps if os.path.exists(os.path.join(type_dir, ts, "mutation.py"))]
            self.mutation_histories[(namespace, type_name)] = history


    def _get_function(self, namespace, type_name, timestamp, func_name):

        ns = namespace.replace("/", "_")
        name = "fam_mutator_schemata.%s.%s.%s.mutation" % (ns, type_name, timestamp)
        schema_dir = self._schema_path(namespace, type_name, timestamp)
        filepath = os.path.join(schema_dir, "mutation.py")
        module = SourceFileLoader(name, filepath).load_module()
        return getattr(module, func_name)


    def _iter_of_of_date_obj(self, namespace, type_name, timestamp):

        fs = self.db.db
        obj_ref = fs.collection(type_name)
        schema_id = self._id_from(namespace, type_name, timestamp)
        q = obj_ref.where("schema", "<", schema_id)
        rows = self.query_wrappers(self.db, q, batch_size=1000)

        # as_json = self.value_from_snapshot(snapshot)

        for row in rows:
            obj = FamObject.from_row(self.db, row)
            yield obj


    def query_wrappers(self, db, firebase_query, batch_size=100):
        return self.query_wrappers_iterator(db, firebase_query, batch_size=batch_size)


    def query_wrappers_iterator(self, db, firebase_query, batch_size):

        skip = 0
        query = firebase_query.order_by("schema").order_by(u"_id").limit(batch_size)

        while True:
            docs = query.stream()
            docs_list = list(docs)
            if len(docs_list) == 0:
                break
            for doc_snapshot in docs_list:
                as_json = db.value_from_snapshot(doc_snapshot)
                yield ResultWrapper.from_couchdb_json(as_json)
            last_doc = docs_list[-1]
            last_id = last_doc.to_dict()["_id"]
            last_schema = last_doc.to_dict()["schema"]
            query = firebase_query.order_by("schema").order_by(u"_id").start_after({
                "_id": last_id,
                "schema": last_schema
            }).limit(batch_size)


    def _mutations_to_apply(self, namespace, typename, timestamp, history):

        mutations = []

        for mutation_timestamp in history:
            if mutation_timestamp > timestamp:
                mutations.append(self._lazy_get_mutation_func(namespace, typename, mutation_timestamp, "mutate"))

        return mutations




    def _lazy_get_mutation_func(self, namespace, type_name, timestamp, func_name):

        key = (namespace, type_name, timestamp, func_name)

        func = self.all_mutations.get(key)

        if func is None:
            func = self._get_function(namespace, type_name, timestamp, func_name)
            self.all_mutations[key] = func

        return func



    def _unidiff_output(self, expected, actual):
        """
        Helper function. Returns a string containing the unified diff of two multiline strings.
        """

        expected=expected.splitlines(1)
        actual=actual.splitlines(1)
        diff=difflib.unified_diff(expected, actual)

        return ''.join(diff)


    def _timestamp_from_datetime(self, dt):
        return dt.strftime("%Y%m%d-%H%M%S-%f")


    def _datetime_from_timestamp(self, ts):
        return datetime.datetime.strptime(ts, "%Y%m%d-%H%M%S-%f")



    def _now_timestamp(self):
        utc = pytz.utc
        dt = datetime.datetime.now(utc)
        # force to utc and then to RFC 3339
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=utc)
        else:
            dt = dt.astimezone(utc)
        return self._timestamp_from_datetime(dt)


    def _id_from(self, namespace, type_name, timestamp):
        return "{}/{}/{}/schema#".format(namespace, type_name, timestamp)


    def _add_new_schema(self, namespace, type_name, schema, previous_schema, timestamp):

        schema_id = self._id_from(namespace, type_name, timestamp)
        schema["id"] = schema_id
        this_schema_dir = self._schema_path(namespace, type_name, timestamp)

        if not os.path.exists(this_schema_dir):
            os.makedirs(this_schema_dir)

        schema_file_path = os.path.join(this_schema_dir, "schema.json")

        current_schema_string = json.dumps(schema, indent=4, sort_keys=True)
        with open(schema_file_path, "w") as f:
            f.write(current_schema_string)

        if previous_schema is not None:
            existing_schema_string = json.dumps(previous_schema, indent=4, sort_keys=True)
            diff = self._unidiff_output(existing_schema_string, current_schema_string)

            self._write_out_mutation(this_schema_dir, namespace, type_name, diff, timestamp)

        return schema_id



    def _write_out_mutation(self, schema_path, namespace, type_name, diff, timestamp):

        mutation_path = os.path.join(schema_path, "mutation.py")

        with open(mutation_path, "w") as f:

            mutation = "**** {} {} schema changed ****\n\n{}".format(namespace, type_name, diff)
            f.write('"""\n{}"""\n\n\n'.format(mutation))

            f.write("CURRENT_SCHEMA_ID = \"{}\"\n\n".format(self._id_from(namespace, type_name, timestamp)))

            mutate = """def mutate(db, {}):
    \"\"\" Write mutation code here \"\"\"
    raise NotImplementedError("The do function in mutation {} {} {} has not been implemented")


"""
            f.write(mutate.format(type_name, namespace, type_name, timestamp))

