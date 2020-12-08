import unittest
import os
import datetime
import pytz
import firebase_admin

os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
os.environ["GCLOUD_PROJECT"] = "localtest"

from decimal import Decimal
from fractions import Fraction
from fam.extra_types.lat_long import LatLong
from google.cloud.firestore_v1 import GeoPoint


from fam.database.firestore_adapter import FirestoreDataAdapter

import fam
from fam.exceptions import *
from fam.tests.models.test04 import Fish
from fam.tests.models.test04 import NAMESPACE as fish_namespace
from fam.tests.models.test01 import Dog
from fam.tests.models.test01 import  NAMESPACE as dog_namespace

from fam.database import FirestoreWrapper
from fam.mapper import ClassMapper

from fam.tests.test_firestore.fixtures import clear_db

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
        self.adapter = FirestoreDataAdapter()


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

        self.assertEqual(serialised["birthday"], birthday)
        self.assertTrue(isinstance(serialised["location"], GeoPoint))
        self.assertEqual(serialised["location"].longitude, -0.1178892)
        self.assertEqual(serialised["location"].latitude, 51.5102213)


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

        self.assertTrue(isinstance(serialised["birthday"], bytes))



class TestOptimiseSerialisationDatabase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        mapper = ClassMapper([Dog])
        cls.db = FirestoreWrapper(mapper, None, namespace=dog_namespace)
        if cls.db.db.project != "localtest":
            raise Exception("wrong db: %s" % cls.db.db.project)

    @classmethod
    def tearDownClass(cls):
        if cls.db.app is not None:
            firebase_admin.delete_app(cls.db.app)

    def setUp(self) -> None:
        clear_db()

    def test_data_base_id(self):

        dog = Dog.create(self.db, name="woofer")

        dog_id = dog.key

        self.assertTrue(dog.key is not None)

        doc_ref = self.db.db.collection("dog").document(dog_id)

        doc = doc_ref.get()
        as_dict = doc.to_dict()

        # self.assertTrue("_id" not in as_dict)
        self.assertTrue("type" not in as_dict)
        self.assertTrue("namespace" not in as_dict)

        got_dog = Dog.get(self.db, dog_id)

        self.assertTrue(got_dog.key == dog_id)
        self.assertTrue(got_dog.namespace == dog.namespace)
        self.assertTrue(got_dog.type == "dog")




class TestDatabase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        mapper = ClassMapper([Fish])
        cls.db = FirestoreWrapper(mapper, None, namespace=fish_namespace)
        if cls.db.db.project != "localtest":
            raise Exception("wrong db: %s" % cls.db.db.project)


    @classmethod
    def clear_db(cls):
        cls.db.delete_all("fish")

    def setUp(self) -> None:
        clear_db()

    def test_fish(self):

        loc = LatLong(51.2345, -1.4533)
        birthday = datetime.datetime(1964, 12, 5, tzinfo=pytz.utc)

        image_path = os.path.join(DATA_DIR, "goldfish.jpg")
        with open(image_path, "rb") as f:
            image_data = f.read()

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







