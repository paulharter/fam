
## little dance to use patch version if necessary

def is_gevent_monkey_patched():
    try:
        from gevent import monkey
    except ImportError:
        return False
    else:
        return monkey.is_module_patched('__builtin__')

if is_gevent_monkey_patched():
    from gcouchbase import Bucket
else:
    from couchbase.bucket import Bucket

from couchbase.bucket import View
from couchbase.n1ql import N1QLQuery
from couchbase.exceptions import NotFoundError, KeyExistsError


from fam.blud import FamObject
from fam.database.base import BaseDatabase
from fam.database.couchdb import ResultWrapper
from fam.exceptions import *


class CouchbaseWrapper(BaseDatabase):

    def __init__(self, mapper, host, bucket_name, read_only=True):
        connection_str = "couchbase://%s/%s" % (host, bucket_name)
        self.bucket = Bucket(connection_str)
        self.read_only = read_only
        self.mapper = mapper



    def view(self, name, *args, **kwargs):

        design_doc_id, view_name = name.split("/")

        design_name = "_design/%s" % design_doc_id

        # print design_doc_id, view_name

        view = View(self.bucket,
                    design_doc_id,
                           view_name,
                           *args,
                           **kwargs
                           )

        rows_list = list(view)
        # print rows_list
        #
        #
        #
        # keys = rows_list[0].keys()
        # keys.remove("id")
        # keys.remove("cas")
        return [ResultWrapper(row.docid, row.doc.cas, row.value) for row in rows_list]

    def n1ql(self, query, with_revs=False, *args, **kwargs):
        return FamObject.n1ql(self, query, with_revs=with_revs, *args, **kwargs)

    def _get(self, key):
        try:
            result = self.bucket.get(key)
        except NotFoundError as e:
            return None
        return ResultWrapper(key, result.cas, result.value)

    def _set(self, key, value, rev=None):
        if self.read_only:
            raise FamWriteError("You can't write to this database")
        try:
            print "rev", rev
            if rev is not None:
                result = self.bucket.upsert(key, value, cas=rev)
            else:
                result = self.bucket.upsert(key, value)
            print "result", result
            return ResultWrapper(key, result.cas, value)
        except KeyExistsError as e:
            raise FamResourceConflict("key alreday exists in couchbase: %s - %s" % (key, e))


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
        # print "rows_list: ", rows_list
        keys = rows_list[0].keys()
        keys.remove("id")
        keys.remove("cas")
        return [ResultWrapper(row["id"], row["cas"], row[keys[0]]) for row in rows_list]