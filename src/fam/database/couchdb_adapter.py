import sys
import datetime
import pytz
from fam.extra_types.lat_long import LatLong
from fractions import Fraction
from decimal import Decimal
from google.cloud.firestore_v1beta1 import GeoPoint
import base64

from .base_adapter import BaseDataAdapter


if sys.version_info[0] < 3:
    PYTHON_VERSION = 2
else:
    PYTHON_VERSION = 3


class CouchDBDataAdapter(BaseDataAdapter):
    pass


