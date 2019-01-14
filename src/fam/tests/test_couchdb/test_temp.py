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

    def test_delete_cat_refs(self):
        paul = Person(name="paul")
        paul.save(self.db)
        cat = Cat(name="whiskers", owner_id=paul.key, legs=2)
        cat.save(self.db)
        key = cat.key
        cat2 = Cat(name="puss", owner_id=paul.key, legs=2)
        cat2.save(self.db)
        revivedcat1 = self.db.get(key)

        self.assertTrue(revivedcat1 is not None)

        paul.delete(self.db)
        revivedcat2 = self.db.get(key)
        print("revivedcat2:" , revivedcat2)
        self.assertTrue(revivedcat2 is None, "revivedcat2: %s" % revivedcat2)