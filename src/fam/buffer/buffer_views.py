import js2py
import json

class FamWriteBufferViews(object):

    FOREIGN_KEY_MAP_STRING = '''function(doc) {
        var resources = %s;
        if (resources.indexOf(doc.type) != -1 && doc.namespace == \"%s\"){
            emit(doc.%s, doc);
        }
    }'''

    def __init__(self, mapper):

        self.mapper = mapper
        self.views = {}
        self.indexes = {}
        self.reverse_indexes = {}
        self.js_context = None
        self._update_designs()
        self.view_name = None
        self.doc = None


    def clear_indexes(self):
        self.indexes = {}
        self.reverse_indexes = {}


    def query_view(self, view_name, key, **kwargs):

        k = tuple(key) if type(key) == list else key

        name = self._clean_name(view_name)
        view_index = self.indexes.get(name)
        # print "****************** - ", self.indexes.get("join_views_reel_item_memberships")
        if view_index is None:
            return []
        values = view_index.get(k)
        if values is None:
            return []
        return [item[1] for item in values.items()]


    def index_obj(self, obj):

        self.obj = obj
        doc = obj.as_dict()
        for view_name, view in self.views.items():
            self.view_name = view_name
            view(doc)


    def _clean_name(self, name):
        return name.replace("/", "_").replace(".", "_").replace("-", "_").replace(":", "_")


    def remove_from_indexes(self, obj_id):

        for view_name in self.indexes.keys():
            index = self.indexes.get(view_name)
            reverse_index = self.reverse_indexes.get(view_name)

            existing_key = reverse_index.get(obj_id)

            ## remove the previous entry
            if existing_key is not None:
                old_indexed_values = index[existing_key]
                del old_indexed_values[obj_id]
                del reverse_index[obj_id]



    def _add_to_index(self, k):

        # print "********* adding: ", k

        kstr = repr(k).replace("'", "\"").replace("u\"", "\"")
        key = None if kstr == '"undefined"' else json.loads(kstr)

        if type(key) == list:
            key = tuple(key)
            # print "************ adding key: ", key

        index = self.indexes.get(self.view_name)
        reverse_index = self.reverse_indexes.get(self.view_name)
        if index is None:
            index = {}
            self.indexes[self.view_name] = index

        if reverse_index is None:
            reverse_index = {}
            self.reverse_indexes[self.view_name] = reverse_index

        obj_id = self.obj.key
        existing_key = reverse_index.get(obj_id)

        if existing_key == key:
            return

        ## remove the previous entry
        if existing_key is not None:
            old_indexed_values = index[existing_key]
            del old_indexed_values[obj_id]
            del reverse_index[obj_id]

        ## add the new one
        if key is not None:
            reverse_index[obj_id] = key
            new_indexed_values = index.get(key)
            if new_indexed_values is None:
                new_indexed_values = {}
                index[key] = new_indexed_values
            new_indexed_values[obj_id] = self.obj


    def _raw_design_doc(self):
        design_doc = {
            "views": {
                "all": {
                    "map": "function(doc) {emit(doc.type, doc);}"
                }
            }
        }
        return design_doc


    def _update_designs(self):

        def add(k):
            self._add_to_index(k)

        self.js_context = js2py.EvalJs({"add": add})

        code = """
        function emit(k, v){
            add(k);
        }
        """

        self.js_context.execute(code)

        ## simple type index
        doc = self._raw_design_doc()
        key = "_design/raw"
        doc["_id"] = key

        self._add_design(self.js_context, key, doc)

        # ## relational indexes
        for namespace_name, namespace in self.mapper.namespaces.items():
            view_namespace = self._clean_name(namespace_name)
            key = "_design/%s" % view_namespace
            doc = self.mapper.get_design(namespace, namespace_name, self.FOREIGN_KEY_MAP_STRING)
            doc["_id"] = key
            self._add_design(self.js_context, key, doc)

        # ## extra indexes
        for doc in self.mapper.extra_design_docs():
            key = doc["_id"]
            self._add_design(self.js_context, key, doc)


    def _add_design(self, js_context, key, doc):

        if(not key.startswith("_design/")):
            raise Exception("DataBaseCacheViews design doc key should start with _design")

        design_name = key[len("_design/"):]

        for view_name, view in doc["views"].items():
            name = "%s_%s" % (design_name, view_name)
            name = self._clean_name(name)
            code = "var %s = %s" % (name, view["map"])
            js_context.execute(code)
            self.views[name] = getattr(js_context, name)
