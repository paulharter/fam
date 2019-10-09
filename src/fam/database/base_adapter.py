import sys
import pytz
import base64
import re

from copy import deepcopy
import datetime
from fam.extra_types.lat_long import LatLong
from fractions import Fraction
from decimal import Decimal
from google.cloud.firestore_v1 import GeoPoint


if sys.version_info[0] < 3:
    PYTHON_VERSION = 2
else:
    PYTHON_VERSION = 3


class BaseDataAdapter(object):

    # a fam doc to serialise into firestore
    def serialise(self, doc):
        dup = deepcopy(doc)
        return self._serialise_walk(dup)

    def deserialise(self, doc):
        dup = deepcopy(doc)
        result = self._deserialise_walk(dup)
        return result


    def is_a_string(self, node):

        if PYTHON_VERSION == 3:
            return isinstance(node, str)
        else:
            return isinstance(node, basestring)


    def is_a_number(self, node):

        if PYTHON_VERSION == 3:
            return isinstance(node, int) or isinstance(node, float)
        else:
            return isinstance(node, int) or isinstance(node, float) or isinstance(node, long)


    def _serialise_walk(self, node):

        if isinstance(node, dict):
            for k, v in node.items():
                node[k] = self._serialise_walk(v)
            return node
        if isinstance(node, list):
            return [self._serialise_walk(v) for v in node]
        if isinstance(node, LatLong):
            return self.serialise_lat_long(node)
        if isinstance(node, Fraction):
            return self.serialise_fraction(node)
        if isinstance(node, Decimal):
            return self.serialise_decimal(node)
        if isinstance(node, datetime.datetime):
            return self.serialise_date_time(node)
        if self.is_a_string(node):
            return self.serialise_string(node)
        if isinstance(node, bytes) or isinstance(node, bytearray):
            return self.serialise_bytes(node)
        if isinstance(node, bool):
            return self.serialise_bool(node)
        if self.is_a_number(node):
            return self.serialise_number(node)
        if hasattr(node, "to_json"):
            return self.serialise_object(node)
        if node is None:
            return None

        raise Exception("BaseAdapter can't serialise this value: %s" % str(node))


    def serialise_lat_long(self, lat_long):
        return "::latlong::%s,%s" % (lat_long.latitude, lat_long.longitude)

    def serialise_fraction(self, fraction):
        return "::fraction::%s/%s" % (fraction.numerator, fraction.denominator)

    def serialise_decimal(self, decimal):
        return "::decimal::%s" % str(decimal)

    def serialise_date_time(self, date_time):
        utc = pytz.utc
        if date_time.tzinfo is None:
            dt = date_time.replace(tzinfo=utc)
        else:
            dt = date_time.astimezone(utc)
        as_iso = dt.isoformat("T") + "Z"
        fixed = as_iso.replace("+00:00", "")
        return "::datetime::%s" % str(fixed)


    def serialise_bytes(self, btes):
        encoded = base64.b64encode(btes)
        result = "::bytes::%s" % encoded.decode("utf-8")
        return result

    def serialise_string(self, string):
        return string

    def serialise_bool(self, boolean):
        return boolean

    def serialise_number(self, number):
        return number

    def serialise_object(self, obj):
        return obj.to_json()

    def is_legacy_datetime(self, node):

        if not self.is_a_string(node):
            return False

        datepattern = r"""^\d{4}-(0[1-9]|1[0-2])-([0-2]\d|3[0-1])T([0-1][0-9]|2[0-3]):[0-5]\d:[0-5]\d([.]\d{1,8})?Z$"""
        pattern = re.compile(datepattern)
        return pattern.match(node)


    def _deserialise_walk(self, node):


        if isinstance(node, dict):
            for k, v in node.items():
                node[k] = self._deserialise_walk(v)
            return node
        if isinstance(node, list):
            return [self._deserialise_walk(v) for v in node]
        if self.is_a_string(node):
            if node.startswith("::fraction::"):
                stripped = node[len("::fraction::"):]
                num, denom = stripped.split("/")
                return Fraction(int(num), int(denom))
            if node.startswith("::decimal::"):
                stripped = node[len("::decimal::"):]
                return Decimal(stripped)
            if node.startswith("::latlong::"):
                stripped = node[len("::latlong::"):]
                lat, long = stripped.split(",")
                return LatLong(float(lat), float(long))
            if node.startswith("::bytes::"):
                stripped = node[len("::bytes::"):]
                return base64.b64decode(stripped)
            if node.startswith("::datetime::"):
                stripped = node[len("::datetime::"):]
                if "." in stripped:
                    dt = datetime.datetime.strptime(stripped, '%Y-%m-%dT%H:%M:%S.%fZ')
                else:
                    dt = datetime.datetime.strptime(stripped, '%Y-%m-%dT%H:%M:%SZ')
                dt = dt.replace(tzinfo=pytz.utc)
                return dt
            if self.is_legacy_datetime(node):
                stripped = node
                if "." in stripped:
                    dt = datetime.datetime.strptime(stripped, '%Y-%m-%dT%H:%M:%S.%fZ')
                else:
                    dt = datetime.datetime.strptime(stripped, '%Y-%m-%dT%H:%M:%SZ')
                dt = dt.replace(tzinfo=pytz.utc)
                return dt
            return node
        if isinstance(node, bool):
            return node
        if node is None:
            return node
        if self.is_a_number(node):
            return node

        raise Exception("FirestoreDataAdapter can't deserialise this value: %s", node)