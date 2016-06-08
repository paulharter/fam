import os
import shutil
import unittest
from fam.database import CouchDBWrapper
from fam.mapper import ClassMapper
from fam.blud import FamObject

from fam.tests.test_couchdb.config import *

from fam.tests.models.test01 import Dog, Cat


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(THIS_DIR, "data")

class CacheTests(unittest.TestCase):

    def setUp(self):
        mapper = ClassMapper([Dog, Cat])
        self.db = CouchDBWrapper(mapper, COUCHDB_URL, COUCHDB_NAME, reset=True)
        self.db.update_designs()

    def tearDown(self):
        pass

    def test_changes(self):
        dog = Dog(name="fly")
        dog.save(self.db)
        all = Dog.all(self.db)
        self.assertEqual(len(all), 1)
        last_seq, objects = FamObject.changes(self.db)
        dog2 = Dog(name="shep")
        dog2.save(self.db)
        last_seq, objects = FamObject.changes(self.db, since=last_seq)
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], dog2)


    def test_changes_limit(self):
        dog = Dog(name="fly")
        dog.save(self.db)
        all = Dog.all(self.db)
        self.assertEqual(len(all), 1)
        last_seq, objects = FamObject.changes(self.db)
        dog2 = Dog(name="shep")
        dog2.save(self.db)
        dog3 = Dog(name="bob")
        dog3.save(self.db)
        last_seq, objects = FamObject.changes(self.db, since=last_seq, limit=1)
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], dog2)
        last_seq, objects = FamObject.changes(self.db, since=last_seq, limit=1)
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], dog3)