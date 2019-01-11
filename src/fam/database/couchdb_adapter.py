import sys


from .base_adapter import BaseDataAdapter


if sys.version_info[0] < 3:
    PYTHON_VERSION = 2
else:
    PYTHON_VERSION = 3


class CouchDBDataAdapter(BaseDataAdapter):
    pass


