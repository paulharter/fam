import unittest
import os

os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
os.environ["GCLOUD_PROJECT"] = "localtest"

import firebase_admin
from fam.exceptions import *
from fam.tests.models.test01 import GenericObject, Dog, Cat, Person, JackRussell, Monkey, Monarch, NAMESPACE
from fam.database import FirestoreWrapper
from fam.mapper import ClassMapper
from fam.database.firestore_contexts import FirestoreBatchContext
from fam.tests.test_firestore.fixtures import clear_db

class TestContexts(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        mapper = ClassMapper([Dog, Cat, Person, JackRussell, Monkey, Monarch])
        cls.db = FirestoreWrapper(mapper, None, namespace=NAMESPACE)
        if cls.db.db.project != "localtest":
            raise Exception("wrong db: %s" % cls.db.db.project)

    @classmethod
    def tearDownClass(cls):
        firebase_admin.delete_app(cls.db.app)

    def setUp(self) -> None:
        clear_db()

    def test_app(self):
        self.assertNotEqual(self.db, None)

    def test_batch_put_delayed(self):

        with FirestoreBatchContext(self.db) as bdb:
            dog = Dog(name="woofer")
            bdb.put(dog)
            got = Dog.get(self.db, dog.key)
            self.assertIsNone(got)

        got = Dog.get(self.db, dog.key)
        self.assertIsNotNone(got)
        self.assertEqual(len(bdb.results), 1 )


    def test_batch_puts_atomic(self):

        try:
            with FirestoreBatchContext(self.db) as bdb:
                cat = Cat(name="blaze")
                bdb.put(cat)
                cat2 = Cat(name="muse", car="fiat")
                bdb.put(cat2)
        except Exception as e:
            print(e)

        got = Cat.get(self.db, cat.key)
        self.assertIsNone(got)
