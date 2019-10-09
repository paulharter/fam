import unittest
import sys
from decimal import Decimal
from fractions import Fraction
from fam.extra_types.lat_long import LatLong
from google.cloud.firestore_v1 import GeoPoint
from fam.tests.test_couchdb.config import *

import os
import datetime
import pytz

from fam.database.couchdb_adapter import CouchDBDataAdapter



import fam
from fam.exceptions import *
from fam.tests.models.test04 import Fish

from fam.database import CouchDBWrapper
from fam.mapper import ClassMapper

SECRETS_DIR = os.path.join(os.path.dirname(fam.__file__), "tests", "secrets")
DATA_DIR = os.path.join(os.path.dirname(fam.__file__), "tests", "data")


class TestSerialisation(unittest.TestCase):

    """
    str
    list
    dict
    bool
    float
    int
    Decimal
    Fraction
    LatLong
    datetime
    bytes
    unicode/str utf8
    """


    def setUp(self):
        self.adapter = CouchDBDataAdapter()


    def test_serialise_basic_types(self):

        doc = { "name": "Paul",
                "age": 53,
                "height": 5.9,
                "is_stoopid": True,
                "children": ["Sol", "Jake"],
                "favorites": {"drink": "coffee", "food": "egg and chips"}
        }

        serialised = self.adapter.serialise(doc)

        # these should all pass through unchanged
        self.assertEqual(doc, serialised)


    def test_serialise_numerics(self):

        doc = {"name": "Paul",
               "age": 53,
               "height": Decimal("5.9"),
               "fraction": Fraction(1, 2),
               "is_stoopid": True,
               "children": ["Sol", "Jake"],
               "favorites": {"drink": "coffee", "food": Decimal("4.2")}
               }

        serialised = self.adapter.serialise(doc)


        self.assertEqual(serialised["height"], "::decimal::5.9")
        self.assertEqual(serialised["fraction"], "::fraction::1/2")
        self.assertEqual(serialised["favorites"]["food"], "::decimal::4.2")


    def test_serialise_latlong_datetime(self):

        birthday = datetime.datetime(1964, 12, 5)

        doc = { "name": "Paul",
                "age": 53,
                "height": 5.9,
                "is_stoopid": True,
                "location": LatLong(51.5102213, -0.1178892),
                "birthday": birthday,
                "children": ["Sol", "Jake"],
                "favorites": {"drink": "coffee", "food": "egg and chips"}
        }

        serialised = self.adapter.serialise(doc)
        self.assertTrue(isinstance(serialised["location"], str))
        self.assertTrue(isinstance(serialised["birthday"], str))
        self.assertEqual(serialised["birthday"], "::datetime::1964-12-05T00:00:00Z")
        self.assertEqual(serialised["location"], "::latlong::51.5102213,-0.1178892")

    def test_serialise_bytes(self):

        doc = { "name": "Paul",
                "age": 53,
                "height": 5.9,
                "is_stoopid": True,
                "birthday": b"aq3restdyrgvdhrjb",
                "children": ["Sol", "Jake"],
                "favorites": {"drink": "coffee", "food": "egg and chips"}
        }

        serialised = self.adapter.serialise(doc)
        self.assertTrue(isinstance(serialised["birthday"], str))


class TestDeSerialisation(unittest.TestCase):


    def setUp(self):
        self.adapter = CouchDBDataAdapter()


    def test_deserialise_datetime(self):

        birthday = datetime.datetime(1964, 12, 5, 12, tzinfo=pytz.UTC)

        doc = { "name": "Paul",
                "age": 53,
                "height": 5.9,
                "new_datetime": birthday,
                "old_datetime": "1964-12-05T12:00:00Z"

        }

        serialised = self.adapter.serialise(doc)

        # these should all pass through unchanged
        self.assertEqual(serialised["new_datetime"], "::datetime::1964-12-05T12:00:00Z")
        self.assertEqual(serialised["old_datetime"], "1964-12-05T12:00:00Z")

        deserialised = self.adapter.deserialise(serialised)

        self.assertEqual(deserialised["new_datetime"], birthday)
        self.assertEqual(deserialised["old_datetime"], birthday)






class TestDatabase(unittest.TestCase):


    def setUp(self):
        mapper = ClassMapper([Fish])
        self.db = CouchDBWrapper(mapper, COUCHDB_URL, COUCHDB_NAME, reset=True)
        self.db.update_designs()





    def test_fish(self):

        loc = LatLong(51.2345, -1.4533)
        birthday = datetime.datetime(1964, 12, 5, tzinfo=pytz.utc)

        image_path = os.path.join(DATA_DIR, "goldfish.jpg")
        with open(image_path, "rb") as f:
            image_data = f.read()

        if sys.version_info < (3, 0):
            image_data = bytearray(image_data)

        fish = Fish.create(self.db, name="Nemo",
                           location=loc,
                           born=birthday,
                           length=Decimal("45.7"),
                           edible_fraction=Fraction(1, 3),
                           image=image_data
        )

        fish2 = Fish.get(self.db, fish.key)

        self.assertTrue(type(fish2.location) == LatLong)
        self.assertEqual(fish2.location.latitude, 51.2345)

        self.assertTrue(isinstance(fish2.born, datetime.datetime))
        self.assertEqual(fish2.born, birthday)

        self.assertTrue(isinstance(fish2.length, Decimal))
        self.assertEqual(fish2.length, Decimal("45.7"))

        self.assertTrue(isinstance(fish2.edible_fraction, Fraction))
        self.assertEqual(fish2.edible_fraction, Fraction(1, 3))

        self.assertTrue(isinstance(fish2.image, bytes))
        self.assertEqual(fish2.image, image_data)

        ## test for view query
        fishes = list(Fish.all(self.db))
        fish3 = fishes[0]

        self.assertTrue(type(fish3.location) == LatLong)
        self.assertEqual(fish3.location.latitude, 51.2345)

        self.assertTrue(isinstance(fish3.born, datetime.datetime))
        self.assertEqual(fish3.born, birthday)

        self.assertTrue(isinstance(fish3.length, Decimal))
        self.assertEqual(fish3.length, Decimal("45.7"))

        self.assertTrue(isinstance(fish3.edible_fraction, Fraction))
        self.assertEqual(fish3.edible_fraction, Fraction(1, 3))

        self.assertTrue(isinstance(fish3.image, bytes))
        self.assertEqual(fish3.image, image_data)






