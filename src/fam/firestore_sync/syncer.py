
from fam.exceptions import *

from fam.database.firestore_adapter import FirestoreDataAdapter


class FirestoreSyncer(object):

    def __init__(self, couchdb_wrapper, firestore_wrapper, batch_size=100, since_in_db=False):

        self.couchdb_wrapper = couchdb_wrapper
        self.firestore_wrapper = firestore_wrapper
        self.queries = []
        self.doc_refs = []
        self.batch_size = batch_size
        self.data_adapter = FirestoreDataAdapter()
        self.types_to_sync_up = None
        self._since = 0
        self.since_rev = None
        self.since_in_db = since_in_db


    def add_query(self, query):
        self.queries.append(query)


    def add_doc_ref(self, doc_ref):
        self.doc_refs.append(doc_ref)

    def add_snapshot(self, snapshot):
        item = self.firestore_wrapper.value_from_snapshot(snapshot)
        update_time = snapshot.update_time
        item["update_seconds"] = update_time.seconds
        item["update_nanos"] = update_time.nanos
        try:
            self.couchdb_wrapper._set(item["_id"], item)
            return item
        except FamResourceConflict as e:
            existing = self.couchdb_wrapper._get(item["_id"])
            if update_time.seconds > existing.value["update_seconds"] or \
                    (update_time.seconds == existing.value["update_seconds"] and
                     update_time.nanos > existing.value["update_nanos"]):
                item["_rev"] = existing.rev
                self.couchdb_wrapper._set(item["_id"], item)
                return item

        return None

    def sync_down(self):

        items = []

        for query in self.queries:
            for snapshot in self.firestore_wrapper.query_snapshots(query, batch_size=self.batch_size):
                item = self.add_snapshot(snapshot)
                if item is not None:
                    items.append(item)

        for doc_ref in self.doc_refs:
            snapshot = doc_ref.get()
            item = self.add_snapshot(snapshot)
            if item is not None:
                items.append(item)

        #self.since = self.couchdb_wrapper.info()["update_seq"]
        return items


    def sync_up(self):
        fs = self.firestore_wrapper.db

        while True:
            last_seq, changes = self.couchdb_wrapper._changes(since=self.since, limit=self.batch_size)

            if changes:
                count = 0
                batch = fs.batch()
                for item in changes:
                    type_name = item.value["type"]
                    if self.types_to_sync_up is None or type_name in self.types_to_sync_up:
                        value = item.value
                        if "update_nanos" in value:
                            del value["update_nanos"]
                        if "update_seconds" in value:
                            del value["update_seconds"]
                        value["_id"] = item.key
                        serialised_value = self.data_adapter.serialise(value)
                        # del serialised_value["_id"]
                        del serialised_value["type"]
                        del serialised_value["namespace"]
                        batch.set(fs.collection(type_name).document(item.key), serialised_value)
                        count += 1

                batch.commit()
                self.since = last_seq
                print("synced up %s items" % count)
            else:
                print("nothing to sync")
                break


    def get_since(self):

        if self.since_in_db:
            since_result = self.couchdb_wrapper._get("sync_since")
            if since_result is not None:
                self.since_rev = since_result.rev
                return since_result.value["since"]
            else:
                return 0
        else:
            return self._since


    def set_since(self, since):

        if self.since_in_db:
            since_result = self.couchdb_wrapper._get("sync_since")
            if since_result is not None:
                self.since_rev = since_result.rev
            value = {"since": since}
            if self.since_rev is not None:
                value["_rev"] = self.since_rev
            self.couchdb_wrapper._set("sync_since", value)
        else:
            self._since = since


    since = property(get_since, set_since)
