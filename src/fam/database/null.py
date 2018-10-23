from fam.database.base import BaseDatabase
from fam.buffer.write_buffer import FamWriteBuffer


class NullDatabase(BaseDatabase):
    database_type = "null"

    def __init__(self, mapper):
        self.mapper = mapper

    def put(self, thing):
        pass

    def delete(self, thing):
        pass

    def get(self, key, class_name=None):
        return None

    def delete_key(self, key):
        pass

    def query_view(self, view_name, **kwargs):
        return []

