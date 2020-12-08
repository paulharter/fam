import unittest
import firebase_admin
import os

os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
os.environ["GCLOUD_PROJECT"] = "localtest"

from fam.exceptions import *
from fam.tests.models.test01 import GenericObject, Dog, Cat, Person, NAMESPACE
from fam.tests.models.test04 import House, Fence
from fam.extra_types.lat_long import LatLong

from fam.database import FirestoreWrapper
from fam.mapper import ClassMapper

from fam.tests.test_firestore.fixtures import clear_db


class TestFirestoreFields(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        mapper = ClassMapper([House, Fence])
        cls.db = FirestoreWrapper(mapper, None, namespace=NAMESPACE)
        if cls.db.db.project != "localtest":
            raise Exception("wrong db: %s" % cls.db.db.project)

    @classmethod
    def tearDownClass(cls):
        firebase_admin.delete_app(cls.db.app)

    def setUp(self) -> None:
        clear_db()

    def test_geopoint(self):

        loc = LatLong(51.2345, -1.4533)
        house = House.create(self.db, name="my house", location=loc)
        house2 = House.get(self.db, house.key)
        self.assertTrue(type(house2.location) == LatLong)
        self.assertEqual(house2.location.latitude, 51.2345)


    def test_polyline(self):

        loc1 = LatLong(51.2345, -1.4533)
        loc2 = LatLong(51.3345, -1.4533)
        loc3 = LatLong(51.3345, -1.3533)
        loc4 = LatLong(51.2345, -1.3533)

        fence = Fence.create(self.db, name="my house", boundary=[loc1, loc2, loc3, loc4])

        self.assertTrue(type(fence.boundary[2]) == LatLong)
