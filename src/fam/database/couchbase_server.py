
from couchbase.exceptions import NotFoundError, HTTPError
from couchbase import Couchbase
from couchbase.views.params import Query
from couchbase.views.iterator import View
import fam.namespaces as namespaces
from fam.utils import couchbase_utils
from fam.database.base import BaseDatabase

import time

class CouchbaseWrapper(BaseDatabase):

    def __init__(self, mapper, host, port, db_name, user_name, password, reset=False, ns=True):

        self.mapper = mapper

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


    def set(self, key, value, cas=0, ttl=0):
        return self.db.set(key, value, cas, ttl)

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

    def update_designs(self):

        if self.mapper is None:
            return

        design_doc = {
            "views": {
                "all": {
                    "map": "function(doc) {emit(doc.type, doc);}"
                }
            }
        }

        try:
            old_design = self.db.design_get("raw")
            design_doc["cas"] = old_design["cas"]
        except HTTPError:
            pass

        self.db.design_create("raw", design_doc, use_devmode=False)

        for namespace_name, namespace in self.mapper.namespaces.iteritems():
            new_design = self._get_design(namespace)
            design_name = namespace_name.replace("/", "_")

            try:
                old_design = self.db.design_get(design_name)
                new_design["cas"] = old_design["cas"]
            except HTTPError:
                pass

            self.db.design_create(design_name, new_design, use_devmode=False)