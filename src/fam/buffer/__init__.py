from contextlib import contextmanager
from .write_buffer import FamWriteBuffer

@contextmanager
def buffered_db(db):
    dbb = FamWriteBuffer(db)
    yield dbb
    dbb.flush()