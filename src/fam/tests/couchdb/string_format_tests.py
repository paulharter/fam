import unittest
import datetime
import pytz

from fam.tests.models.test01 import Event
from fam.database import CouchDBWrapper
from fam.mapper import ClassMapper

COUCHDB_URL = "http://localhost:5984"
COUCHDB_NAME = "test"

class MapperTests(unittest.TestCase):


    def setUp(self):
        mapper = ClassMapper([Event])
        self.db = CouchDBWrapper(mapper, COUCHDB_URL, COUCHDB_NAME, reset=True)
        self.db.update_designs()

    def tearDown(self):
        pass


    def test_date_time(self):

        utc = pytz.utc
        birthday = datetime.datetime(year=2015, month=12, day=5, hour=10, minute=10, second=13, microsecond=876532, tzinfo=utc)
        event = Event(created=birthday)
        self.db.put(event)
        timestamp = event._properties["created"]
        self.assertEqual(timestamp, "2015-12-05T10:10:13.876532Z")
        self.assertEqual(event.created, birthday)

    def test_date_time_without_tz(self):

        utc = pytz.utc
        birthday = datetime.datetime(year=2015, month=12, day=5, hour=10, minute=10, second=13, microsecond=876532)
        event = Event(created=birthday)
        self.db.put(event)
        timestamp = event._properties["created"]
        self.assertEqual(timestamp, "2015-12-05T10:10:13.876532Z")
        self.assertEqual(event.created, birthday.replace(tzinfo=utc))

