from fam.database.base import BaseDatabase
from fam.buffer.write_buffer import FamWriteBuffer
from .null import NullDatabase


class MockDatabase(BaseDatabase):
    database_type = "mock"

    def __init__(self, mapper):
        self.mapper = mapper
        null_db = NullDatabase(mapper)
        self.buffer = FamWriteBuffer(null_db)


    def set_object(self, obj, rev=None):
        return self.buffer.put(obj)

    def get(self, key, class_name=None):
        return self.buffer.get(key)

    def _delete(self, key, rev, classname):
        return self.buffer.delete_key(key)

    def delete_key(self, key):
        return self.buffer.delete_key(key)

    def query_view(self, view_name, **kwargs):
        return self.buffer.query_view(view_name, **kwargs)
