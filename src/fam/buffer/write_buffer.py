import traceback


class FamWriteBuffer(object):

    def __init__(self, db):
        self.store = {}
        self.to_be_saved = set()
        self.db = db
        self.views = db.mapper.buffer_views


    def _get(self, *args, **kwargs):
        traceback.print_stack()
        raise Exception()


    def view(self, name, **kwargs):
        traceback.print_stack()
        raise NotImplementedError("view doesn't work with the DataBaseCache yet")


    def put(self, thing):

        thing._db = self
        self.views.index_obj(thing)

        key = thing.key
        if key in self.store:
            if id(not self.store[key]) == id(thing):
                raise Exception("putting thing with same key but different python id into cache - it's confused")
        else:
            self.store[thing.key] = thing
        self.to_be_saved.add(key)

    def get_refs_from(self, namespace, type_name, name, key, field):
        view_namespace = namespace.replace("/", "_")
        view_name = "%s/%s_%s" % (view_namespace, type_name, name)
        return self.query_view(view_name, key=key)

    def query_view(self, view_name, **kwargs):
        db_objs = self.db.query_view(view_name, **kwargs)
        [self._refresh_cache(o.key, o) for o in db_objs]
        # these will inclde the refreshed ones
        buffer_objs = self.views.query_view(view_name, **kwargs)
        return buffer_objs


    def _refresh_cache(self, key, got):
        if got is not None:
            got._db = self
        current_in_cache = self.store.get(key)
        # If there are changes from the database then update the current one in place
        if current_in_cache is not None and got is not None:
            if current_in_cache.rev != got.rev:
                current_in_cache.rev = got.rev
                current_in_cache._properties = got._properties
                self.views.index_obj(current_in_cache)
            return current_in_cache
        elif current_in_cache is not None:
            return current_in_cache
        elif got is not None:
            self.store[got.key] = got
            self.views.index_obj(got)
            return got
        else:
            return None


    def delete(self, thing):
        if thing.key in self.store:
            del self.store[thing.key]
            self.views.remove_from_indexes(thing.key)
        return self.db.delete(thing)


    def get(self, key, class_name=None):
        got = self.db.get(key)
        result = self._refresh_cache(key, got)
        return result


    def delete_key(self, key):
        if key in self.store:
            del self.store[key]
            self.views.remove_from_indexes(key)
        return self.db.delete_key(key)


    def flush(self):
        # only save the things that have been "put"
        for key in list(self.to_be_saved):
            thing = self.store[key]
            thing._db = self.db
            self.db.put(thing)

        self.views.clear_indexes()
