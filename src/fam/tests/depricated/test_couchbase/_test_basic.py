import os

import unittest
from fam.database import CouchbaseWrapper
from fam.mapper import ClassMapper

from fam.tests.models.test01 import Dog, Cat

COUCHBASE_HOST = "127.0.0.1"
COUCHBASE_BUCKET = "test"


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(THIS_DIR, "data")

class CacheTests(unittest.TestCase):

    def setUp(self):
        mapper = ClassMapper([Dog, Cat])
        self.db = CouchbaseWrapper(mapper, COUCHBASE_HOST, COUCHBASE_BUCKET, read_only=False)

    def tearDown(self):
        pass

    def test_save(self):
        dog = Dog(name="fly")
        dog.save(self.db)

    def test_get(self):
        dog = Dog(name="fly")
        dog.save(self.db)
        dog_key = dog.key
        got_dog = self.db.get(dog_key)
        self.assertEqual(dog.name, got_dog.name)

    def test_n1ql(self):
        dog = Dog(name="fly")
        dog.save(self.db)
        dogs = self.db.n1ql('SELECT META(test), * FROM test WHERE type="dog" and name="fly"')
