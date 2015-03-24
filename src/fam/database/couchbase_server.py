
from couchbase.exceptions import NotFoundError
from couchbase import Couchbase
from couchbase.views.params import Query
from couchbase.views.iterator import View
import fam.namespaces as namespaces
from fam import couchbase_utils

import time

class CouchbaseWrapper(object):

    def __init__(self, host, port, db_name, user_name, password, reset=False, ns=True):

        print "*****  CouchbaseWrapper  ********"

        db_url = "http://%s:%s" % (host, port)
        if reset:
            try:
                couchbase_utils.flush_a_bucket(db_url, user_name, password, db_name)
            except Exception:
                couchbase_utils.make_a_bucket(db_url, user_name, password, db_name, force=True, flush=True)
                time.sleep(2)
        if ns:
            namespaces.update_designs_couchbase(db_name, host)

        self.db = Couchbase.connect(bucket=db_name, host=host)


    def get(self, key):
        try:
            return self.db.get(key)
        except NotFoundError:
            return None


    def set(self, key, value, cas=0):
        return self.db.set(key, value, cas)

    def delete(self, key, cas):
        return self.db.delete(key, cas)

    def view(self, name, key):
        design, view = name.split("/")

        q = Query(
            stale=False,
            inclusive_end=True,
            mapkey_range=[key]
        )

        view = View(self.db, design, view, query=q)
        return [(row.docid, None, row.value) for row in view]


    def query(self, *attr, **kwargs):
        return self.db.query(*attr, **kwargs)

    def __getattr__(self, name):
        return getattr(self.db, name)

    def sync_up(self):
        return
