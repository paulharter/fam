import unittest

import firebase_admin

from fam.tests.models.test01 import Dog, Cat, Person, JackRussell, Monkey, Monarch, NAMESPACE
from fam.database import FirestoreWrapper
from fam.mapper import ClassMapper

from fam.tests.test_firestore.config import CREDS

class TestFireStoreCollections(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        mapper = ClassMapper([Dog, Cat, Person, JackRussell, Monkey, Monarch])
        cls.db = FirestoreWrapper(mapper, CREDS, namespace=NAMESPACE)
        cls.clear_db()

    @classmethod
    def tearDownClass(cls):
        firebase_admin.delete_app(cls.db.app)

    @classmethod
    def clear_db(cls):
        cls.db.delete_all("dog")
        cls.db.delete_all("cat")
        cls.db.delete_all("person")
        cls.db.delete_all("jackrussell")
        cls.db.delete_all("monkey")
        cls.db.delete_all("dog__kennel_club_membership")



    def test_update_cat(self):
        paul = Person(name="paul")
        paul.save(self.db)
        cat = Cat(name="whiskers", owner_id=paul.key, legs=2)
        cat.save(self.db)
        cat.name = "blackie"
        cat.save(self.db)

        self.assertEqual(cat.name, "blackie")
        self.assertEqual(cat._properties["name"], "blackie")
        self.assertFalse("name" in cat.__dict__.keys())

        got = Cat.get(self.db, cat.key)

        self.assertEqual(got.name, "blackie")


