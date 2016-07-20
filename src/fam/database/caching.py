from contextlib import contextmanager

@contextmanager
def cache(db):
    dbc = DataBaseCache(db)
    yield dbc
    dbc.flush()

class DataBaseCache(object):

    def __init__(self, db):

        self.store = {}
        self.to_be_saved = set()
        self.db = db

    def put(self, thing):
        key = thing.key
        if key in self.store:
            if id(not self.store[key]) == id(thing):
                raise Exception("putting thing with same key but different python id into cache - it's confused")
        else:
            self.store[thing.key] = thing
        self.to_be_saved.add(key)


    def query_view(self, view_name, **kwargs):
        objs = self.db.query_view(view_name, **kwargs)
        return [self._refresh_cache(o.key, o) for o in objs]


    def _refresh_cache(self, key, got):

        current_in_cache = self.store.get(key)
        if current_in_cache is not None and got is not None:
            if current_in_cache.rev != got.rev:
                current_in_cache.rev = got.rev
                current_in_cache._properties = got._properties
            return current_in_cache
        elif current_in_cache is not None:
            return current_in_cache
        elif got is not None:
            self.store[got.key] = got
            return got
        else:
            return None


    def delete(self, thing):
        if thing.key in self.store:
            del self.store[thing.key]
        return self.db.delete(thing)


    def get(self, key):
        got = self.db.get(key)
        return self._refresh_cache(key, got)


    def delete_key(self, key):
        if key in self.store:
            del self.store[key]
        return self.db.delete_key(key)


    def flush(self):
        # only save the things that have been "put"
        for key in list(self.to_be_saved):
            thing = self.store[key]
            self.db.put(thing)
