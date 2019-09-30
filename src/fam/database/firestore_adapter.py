import sys
import datetime
from fam.extra_types.lat_long import LatLong
from fractions import Fraction
from decimal import Decimal
from google.cloud.firestore_v1 import GeoPoint

from .base_adapter import BaseDataAdapter


if sys.version_info[0] < 3:
    PYTHON_VERSION = 2
else:
    PYTHON_VERSION = 3


class FirestoreDataAdapter(BaseDataAdapter):


    def serialise_lat_long(self, lat_long):
        return GeoPoint(latitude=lat_long.latitude, longitude=lat_long.longitude)


    def serialise_date_time(self, date_time):
        return date_time


    def serialise_bytes(self, btes):
        return btes


    def _deserialise_walk(self, node):

        if isinstance(node, dict):
            for k, v in node.items():
                node[k] = self._deserialise_walk(v)
            return node
        if isinstance(node, list):
            return [self._deserialise_walk(v) for v in node]
        if isinstance(node, GeoPoint):
            return LatLong(latitude=node.latitude, longitude=node.longitude)
        if self.is_a_string(node):
            if node.startswith("::fraction::"):
                stripped = node[len("::fraction::"):]
                num, denom = stripped.split("/")
                return Fraction(int(num), int(denom))
            if node.startswith("::decimal::"):
                stripped = node[len("::decimal::"):]
                return Decimal(stripped)
            return node
        if isinstance(node, datetime.datetime):
            return node
        if isinstance(node, bytes):
            return node
        if isinstance(node, bool):
            return node
        if self.is_a_number(node):
            return node
        if node is None:
            return node

        raise Exception("FirestoreDataAdapter can't deserialise this value: %s" % node)