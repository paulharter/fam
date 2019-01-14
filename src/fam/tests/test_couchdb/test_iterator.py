from __future__ import absolute_import
import os
import unittest
from fam.database import CouchDBWrapper
from fam.mapper import ClassMapper
from fam.buffer import buffered_db
from fam.tests.test_couchdb.config import *
from fam.tests.models.test01 import Dog, Cat, Person

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(THIS_DIR, "data")

class CacheTests(unittest.TestCase):

    def setUp(self):
        mapper = ClassMapper([Dog, Cat, Person])
        self.db = CouchDBWrapper(mapper, COUCHDB_URL, COUCHDB_NAME, reset=True)
        self.db.update_designs()

    def tearDown(self):
        self.db.session.close()



    def test_iterate_dogs(self):

        me = Person(name="paul")
        self.db.put(me)

        for i in range(500):
            dog = Dog(name="dog_%s" % i, owner=me)
            self.db.put(dog)

        counter = 0
        for dog in me.dogs:
            counter += 1

        self.assertEqual(counter, 500)