
import sys
import datetime
from copy import deepcopy
from decimal import Decimal
from fractions import Fraction

if sys.version_info[0] < 3:
    PYTHON_VERSION = 2
else:
    PYTHON_VERSION = 3


__all__ = [
    "BoolField",
    "NumberField",
    "StringField",
    "ListField",
    "DictField",
    "ObjectField",
    "LatLongField",
    "DateTimeField",
    "BytesField",
    "DecimalField",
    "FractionField",
    "ReferenceTo",
    "ReferenceFrom",
    "EmailField",
]

from .constants import *
from .exceptions import *
from .extra_types.lat_long import LatLong


class Field(object):
    object = "base"

    def __init__(self, required=False, immutable=False, default=None, unique=False):
        self.required = required
        self.immutable = immutable
        self.default = default
        self.unique = unique
        self._types = []

        if self.default is not None and self.required is True:
            raise FamError("It doesnt really make sense to use both required and default together. Just use default")

    def is_correct_type(self, value):
        value is None or any(isinstance(value, cls) for cls in self._types)

    def get_default(self):
        return self.default

    def __str__(self):
        attr = []
        if self.required:
            attr.append(FIELD_REQUIRED)
        return " ".join(attr)

    as_string = property(__str__)


class BoolField(Field):

    _types = [bool]


class NumberField(Field):

    if PYTHON_VERSION == 3:
        _types = [int, float]
    else:
        _types = [int, float, long]


class StringField(Field):

    if PYTHON_VERSION == 3:
        _types = [str]
    else:
        _types = [basestring]


class ListField(Field):

    _types = [list]

    def __init__(self, item_cls=None, required=False, immutable=False, default=None):
        self.item_cls = item_cls
        super(ListField, self).__init__(required=required, immutable=immutable, default=default)

    def get_default(self):
        return deepcopy(self.default)



class DictField(Field):

    _types = [dict]

    def get_default(self):
        return deepcopy(self.default)



class ObjectField(Field):

    def get_default(self):
        return self.cls()

    def __init__(self, cls, default=None, required=False):
        self.cls = cls
        self._types = [cls]
        super(ObjectField, self).__init__(default=default, required=required)


    # "LatLongField",
    # "DateTimeField",
    # "ByteField",
    # "DecimalField",
    # "FractionField",

class LatLongField(Field):

    _types = [LatLong]

    def get_default(self):
        return LatLong(self.default.latitude, self.default.longitude)


class DateTimeField(Field):
    _types = [datetime.datetime]

    def get_default(self):
        return self.default


class BytesField(Field):

    if PYTHON_VERSION == 3:
        _types = [bytes, bytearray]
    else:
        _types = [bytes, bytearray, str]

    def get_default(self):
        return self.default.copy()


class DecimalField(Field):

    _types = [Decimal]

    def get_default(self):
        return self.default.copy()


class FractionField(Field):
    _types = [Fraction]

    def get_default(self):
        return self.default.copy()


class EmailField(StringField):

    pattern = r"""^([-!#$%&'*+/=?^_`{}|~0-9a-zA-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9a-zA-Z]+)*|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*")@(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}\.?$"""



class ReferenceTo(Field):

    if PYTHON_VERSION == 3:
        _types = [str]
    else:
        _types = [basestring]

    def __init__(self, refns, refcls, required=False, immutable=False, default=None, unique=False,
                 cascade_delete=False):
        self.refns = refns
        self.refcls = refcls
        self.cascade_delete = cascade_delete
        super(ReferenceTo, self).__init__(required, immutable, default, unique)

    def __str__(self):
        attr = []

        attr.append("ns:%s" % self.refns)
        attr.append("resource:%s" % self.refcls)

        if self.required:
            attr.append(FIELD_REQUIRED)
        return " ".join(attr)

    as_string = property(__str__)


class ReferenceFrom(Field):

    def __init__(self, refns, refcls, fkey, required=False, immutable=False, default=None, cascade_delete=False):
        self.refns = refns
        self.refcls = refcls
        self.fkey = fkey
        self.cascade_delete = cascade_delete
        super(ReferenceFrom, self).__init__(required, immutable, default)

    def __str__(self):
        attr = []
        attr.append("ns:%s" % self.refns)
        attr.append("resource:%s" % self.refcls)
        attr.append("key:%s" % self.fkey)
        if self.required:
            attr.append(FIELD_REQUIRED)
        return " ".join(attr)

    as_string = property(__str__)