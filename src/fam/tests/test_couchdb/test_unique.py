import os
import unittest
from fam.database import CouchDBWrapper
from fam.mapper import ClassMapper

from fam.exceptions import *
from fam.tests.test_couchdb.config import *
from fam.tests.models.test01 import Dog, Cat, Person, JackRussell

THIS_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(THIS_DIR, "data")


class IndexTests(unittest.TestCase):

    db = None

    def setUp(self):
        filepath = os.path.join(THIS_DIR, "animal_views.js")
        mapper = ClassMapper([Dog, Cat, Person, JackRussell], designs=[filepath])
        self.db = CouchDBWrapper(mapper, COUCHDB_URL, COUCHDB_NAME, reset=True)
        self.db.update_designs()

    def tearDown(self):
        self.db.session.close()


    def test_uniqueness(self):

        paul = Person(name="paul")
        self.db.put(paul)
        dog1 = Dog.create(self.db, name="rufus", owner_id=paul.key, kennel_club_membership="123456")
        dog2 = Dog.create(self.db, name="fly", owner_id=paul.key)

        # raises if setting one value
        self.assertRaises(FamUniqueError, dog2.update, {"kennel_club_membership": "123456"})
        self.assertIsNone(dog2.kennel_club_membership)

        # raises if creating a new one
        self.assertRaises(FamUniqueError, Dog.create, self.db, name="steve", owner_id=paul.key, kennel_club_membership="123456")

    def test_uniqueness_delete(self):

        paul = Person(name="paul")
        self.db.put(paul)
        dog1 = Dog.create(self.db, name="rufus", owner_id=paul.key, kennel_club_membership="123456")

        dog1.delete(self.db)
        dog2 = Dog.create(self.db, name="another", owner_id=paul.key, kennel_club_membership="123456")


    def test_get_unique(self):

        paul = Person(name="paul")
        self.db.put(paul)
        dog1 = Dog.create(self.db, name="rufus", owner_id=paul.key, kennel_club_membership="123456")

        dog2 = Dog.get_unique_instance(self.db, "kennel_club_membership", "123456")
        self.assertIsNotNone(dog2)
        self.assertTrue(dog2.kennel_club_membership == "123456")
