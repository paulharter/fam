import unittest
import json
import time
import os

from google.cloud.firestore_v1beta1 import GeoPoint

import fam
from fam.exceptions import *
from fam.tests.models.test01 import GenericObject, Dog, Cat, Person, NAMESPACE
from fam.tests.models.test04 import House, Fence
from fam.extra_types.lat_long import LatLong

from fam.database import FirestoreWrapper
from fam.mapper import ClassMapper

SECRETS_DIR = os.path.join(os.path.dirname(fam.__file__), "tests", "secrets")


class TestDB(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        creds_path = os.path.join(SECRETS_DIR, "earth-rover-test-d241bce5266d.json")
        mapper = ClassMapper([House, Fence])
        cls.db = FirestoreWrapper(mapper, creds_path, namespace=NAMESPACE)
        cls.clear_db()


    @classmethod
    def clear_db(cls):
        cls.db.delete_all("house")



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
