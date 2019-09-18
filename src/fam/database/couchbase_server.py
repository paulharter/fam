import copy
## little dance to use patch version if necessary

def is_gevent_monkey_patched():
    try:
        from gevent import monkey
    except ImportError:
        return False
    else:
        return monkey.is_module_patched('__builtin__')


from couchbase.cluster import Cluster
from couchbase.cluster import PasswordAuthenticator
from couchbase.bucket import View
from couchbase.n1ql import N1QLQuery
from couchbase.exceptions import NotFoundError, KeyExistsError


from fam.blud import FamObject
from fam.database.base import BaseDatabase
from fam.database.couchdb import ResultWrapper
from fam.exceptions import *


class CouchbaseWrapper(BaseDatabase):

    def __init__(self, mapper, host, bucket_name, read_only=True):
        # connection_str = "couchbase://%s/%s" % (host, bucket_name)
        # self.bucket = Bucket(connection_str)
        self.read_only = read_only
        self.mapper = mapper
        # self.bucket_name = bucket_name


        cluster = Cluster('couchbase://%s' % host)
        authenticator = PasswordAuthenticator('test', 'bollocks')
        cluster.authenticate(authenticator)
        self.bucket = cluster.open_bucket(bucket_name)

        self.mapper = mapper

    def update_designs(self):

        ## simple type index
        doc = self._raw_design_doc()
        key = "_design/raw"

        doc["_id"] = key

        self.ensure_design_doc(key, doc)


        ## relational indexes
        for namespace_name, namespace in self.mapper.namespaces.items():

            view_namespace = namespace_name.replace("/", "_")
            key = "_design/%s" % view_namespace

            doc = self.mapper.get_design(namespace, namespace_name, self.FOREIGN_KEY_MAP_STRING)
            doc["_id"] = key
            self.ensure_design_doc(key, doc)

        ## extra indexes
        for doc in self.mapper.extra_design_docs():
            key = doc["_id"]
            self.ensure_design_doc(key, doc)


    def _raw_design_doc(self):

        design_doc = {
            "views": {
                "all": {
                    "map": "function(doc) {emit(doc.type, null);}"
                }
            }
        }

        return design_doc



    def ensure_design_doc(self, key, doc):
        if self.read_only:
            raise Exception("This db is read only")

        # first put it into dev
        dev_key = key.replace("_design/", "_design/dev_")
        dev_doc = copy.deepcopy(doc)
        dev_doc["_id"] = dev_key

        previous_dev = self._get(dev_key)

        # print "self.db_url: ", self.db_url, self.db_name

        self._set(dev_key, dev_doc, rev=None if previous_dev is None else previous_dev.rev)

        # then get it back again to compare
        existing = self._get(key)
        existing_dev = self._get(dev_key)

        if existing == existing_dev:
            pass
            print("************  designs up to date ************")
        else:
            print("************  updating designs ************")
            print("new_design: ", doc)
            self._set(key, doc, rev=None if existing is None else existing.rev)
    #
    # def view(self, name, *args, **kwargs):
    #
    #     design_doc_id, view_name = name.split("/")
    #
    #     design_name = "_design/%s" % design_doc_id
    #
    #     # print design_doc_id, view_name
    #
    #     view = View(self.bucket,
    #                 design_doc_id,
    #                        view_name,
    #                        *args,
    #                        **kwargs
    #                        )
    #
    #     rows_list = list(view)
    #     # print rows_list
    #     #
    #     #
    #     #
    #     # keys = rows_list[0].keys()
    #     # keys.remove("id")
    #     # keys.remove("cas")
    #     return [ResultWrapper(row.docid, row.doc.cas, row.value) for row in rows_list]

    #
    # def get_refs_from(self, namespace, type_name, name, key, field):
    #
    #     query_string = (
    #         "SELECT * FROM `travel-sample`"
    #         "WHERE country=$country "
    #         "AND geo.alt > $altitude "
    #         "AND (geo.lat BETWEEN $min_lat AND $max_lat) "
    #         "AND (geo.lon BETWEEN $min_lon AND $max_lon "
    #     )



    def n1ql(self, query, with_revs=False, *args, **kwargs):
        return FamObject.n1ql(self, query, with_revs=with_revs, *args, **kwargs)

    def _get(self, key, class_name=None):
        try:
            result = self.bucket.get(key)
        except NotFoundError as e:
            return None
        return ResultWrapper(key, result.cas, result.value)

    def _set(self, key, value, rev=None):
        if self.read_only:
            raise FamWriteError("You can't write to this database")
        try:
            if rev is not None:
                result = self.bucket.upsert(key, value, cas=rev)
            else:
                result = self.bucket.upsert(key, value)
            return ResultWrapper(key, result.cas, value)
        except KeyExistsError as e:
            raise FamResourceConflict("key alreday exists in couchbase: %s - %s" % (key, e))



    def set_object(self, obj, rev=None):

        return self._set(obj.key, obj._properties, rev=rev)

    def _n1ql_with_rev(self, query, *args, **kwargs):
        query = N1QLQuery(query, *args, **kwargs)
        rows = self.bucket.n1ql_query(query)
        results = []
        bucket_name = None

        for row in rows:
            if bucket_name is None:
                keys = row.keys()
                keys.remove("id")
                keys.remove("cas")
                bucket_name = keys[0]

            rev = row["_sync"]["rev"]
            results.append(ResultWrapper(row["id"], rev, row[bucket_name]))

        return results


    def _n1ql(self, query, *args, **kwargs):
        query = N1QLQuery(query, *args, **kwargs)
        rows = self.bucket.n1ql_query(query)
        rows_list = list(rows)

        return [ResultWrapper(row["$1"]["id"], row["$1"]["cas"], row["test"]) for row in rows_list]