from .blud import StringField
import pytz

import datetime

class EmailField(StringField):
    pattern = """^([-!#$%&'*+/=?^_`{}|~0-9a-zA-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9a-zA-Z]+)*|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*")@(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}\.?$"""


class DateTimeField(StringField):
    pattern = """^([0-9]{4})-(0[1-9]|1[0-2])-([0-2][0-9]|3[0-1])T([0-1][0-9]|2[0-3]):([0-5][0-9]):[0-5][0-9](.[0-9]{1,8})?Z$"""

    @staticmethod
    def to_json(dt):
        # force to utc and then to RFC 3339
        utc = pytz.utc
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=utc)
        else:
            dt = dt.astimezone(utc)
        as_iso = dt.isoformat("T") + "Z"
        #remove unnecessary offset if there is one
        return as_iso.replace("+00:00", "")

    @staticmethod
    def from_json(as_json):
        dt = datetime.datetime.strptime(as_json, '%Y-%m-%dT%H:%M:%S.%fZ')
        dt = dt.replace(tzinfo=pytz.utc)
        return dt

