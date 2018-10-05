
from fam.exceptions import *

from fam.database.firestore_adapter import FirestoreDataAdapter


class FirestoreSyncer(object):

    def __init__(self, couchdb_wrapper, firestore_wrapper, batch_size=100):

        self.couchdb_wrapper = couchdb_wrapper
        self.firestore_wrapper = firestore_wrapper
        self.queries = []
        self.since = 0
        self.batch_size = batch_size

        self.data_adapter = FirestoreDataAdapter()


    def add_query(self, query):

        self.queries.append(query)


    def sync_down(self):

        for query in self.queries:

            for snapshot in self.firestore_wrapper.query_snapshots(query, batch_size=self.batch_size):
                item = self.firestore_wrapper.data_adapter.deserialise(snapshot.to_dict())
                update_time = snapshot.update_time
                item["update_seconds"] = update_time.seconds
                item["update_nanos"] = update_time.nanos
                try:
                    self.couchdb_wrapper._set(item["_id"], item)
                except FamResourceConflict as e:
                    existing = self.couchdb_wrapper._get(item["_id"])
                    if update_time.seconds > existing.value["update_seconds"] or \
                            (update_time.seconds == existing.value["update_seconds"] and
                                     update_time.nanos > existing.value["update_nanos"]):
                        item["_rev"] = existing.rev
                        self.couchdb_wrapper._set(item["_id"], item)
                    else:
                        pass

        self.since = self.couchdb_wrapper.info()["update_seq"]


    def sync_up(self):
        fs = self.firestore_wrapper.db

        while True:
            last_seq, changes = self.couchdb_wrapper._changes(since=self.since, limit=self.batch_size)

            if changes:
                self.since = last_seq
                batch = fs.batch()
                for item in changes:
                    value = item.value
                    if "update_nanos" in value:
                        del value["update_nanos"]
                    if "update_seconds" in value:
                        del value["update_seconds"]
                    value["_id"] = item.key
                    serialised_value = self.data_adapter.serialise(value)
                    batch.set(fs.collection(item.value["type"]).document(item.key), serialised_value)
                batch.commit()
            else:
                break



