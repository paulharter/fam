import unittest
import json
import time
import os


from fam.exceptions import *
from fam.tests.models.test01 import GenericObject, Dog, Cat, Person, JackRussell, Monkey, Monarch, NAMESPACE
from fam.tests.models.test04 import House

from fam.database import FirestoreWrapper
from fam.database import CouchDBWrapper
from fam.extra_types.lat_long import LatLong

from fam.mapper import ClassMapper

from fam.firestore_sync.syncer import FirestoreSyncer

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))


class TestDB(unittest.TestCase):


    def setUp(self):
        creds_path = os.path.join(ROOT_DIR, "secrets", "earth-rover-test-d241bce5266d.json")
        mapper = ClassMapper([Dog, Cat, Person, JackRussell, Monkey])
        self.firestore = FirestoreWrapper(mapper, creds_path)
        self.couchdb = CouchDBWrapper(mapper, "http://localhost:5984", db_name="test", reset=True)
        self.couchdb.update_designs()
        self.clear_db()


    def clear_db(self):
        self.firestore.delete_all("dog")
        self.firestore.delete_all("cat")
        self.firestore.delete_all("person")
        self.firestore.delete_all("jackrussell")
        self.firestore.delete_all("monkey")


    def test_app(self):
        self.assertNotEqual(self.firestore, None)


    def test_query_generator(self):

        paul = Person.create(self.firestore, name="paul")
        dog1 = Dog.create(self.firestore, name="woofer", owner=paul)
        dog2 = Dog.create(self.firestore, name="tiny", owner=paul)
        dog3 = Dog.create(self.firestore, name="fly", owner=paul)

        dogs_ref = self.firestore.db.collection("dog")
        q = dogs_ref.where("owner_id", "==", paul.key)

        dogs = self.firestore.query_items(q, batch_size=1)
        dogs_list = list(dogs)
        self.assertTrue(isinstance(dogs_list[0], Dog))

        self.assertEquals(len(dogs_list), 3)


    def test_sync_down(self):

        paul = Person.create(self.firestore, name="paul")
        sol = Person.create(self.firestore, name="sol")
        dog1 = Dog.create(self.firestore, name="woofer", owner=paul)
        dog2 = Dog.create(self.firestore, name="tiny", owner=paul)
        dog3 = Dog.create(self.firestore, name="fly", owner=paul)

        dogs_ref = self.firestore.db.collection("dog")

        syncer = FirestoreSyncer(self.couchdb, self.firestore)
        syncer.add_query(dogs_ref.where("owner_id", "==", paul.key))

        dogs = Dog.all(self.couchdb)
        dogs_list = list(dogs)
        self.assertEqual(len(dogs_list), 0)

        syncer.sync_down()

        dogs = Dog.all(self.couchdb)
        dogs_list = list(dogs)
        self.assertEqual(len(dogs_list), 3)


    def test_sync_down_since(self):

        paul = Person.create(self.firestore, name="paul")
        sol = Person.create(self.firestore, name="sol")
        dog1 = Dog.create(self.firestore, name="woofer", owner=paul)
        dog2 = Dog.create(self.firestore, name="tiny", owner=paul)
        dog3 = Dog.create(self.firestore, name="fly", owner=paul)

        dogs_ref = self.firestore.db.collection("dog")

        syncer = FirestoreSyncer(self.couchdb, self.firestore)
        syncer.add_query(dogs_ref.where("owner_id", "==", paul.key))

        dogs = Dog.all(self.couchdb)
        dogs_list = list(dogs)
        self.assertEqual(len(dogs_list), 0)

        syncer.sync_down()
        dogs = Dog.all(self.couchdb)
        dogs_list = list(dogs)
        self.assertEqual(len(dogs_list), 3)

        dog3.update({"name":"jelly"})
        syncer.sync_down()
        updated = self.couchdb.get(dog3.key)

        self.assertEqual(updated.name, "jelly")


    def test_sync_up(self):

        paul = Person.create(self.firestore, name="paul")
        sol = Person.create(self.firestore, name="sol")
        dog1 = Dog.create(self.firestore, name="woofer", owner=paul)
        dog2 = Dog.create(self.firestore, name="tiny", owner=paul)
        dog3 = Dog.create(self.firestore, name="fly", owner=paul)

        dogs_ref = self.firestore.db.collection("dog")

        syncer = FirestoreSyncer(self.couchdb, self.firestore)
        syncer.add_query(dogs_ref.where("owner_id", "==", paul.key))

        dogs = Dog.all(self.couchdb)
        dogs_list = list(dogs)
        self.assertEqual(len(dogs_list), 0)

        syncer.sync_down()
        dogs = Dog.all(self.couchdb)
        dogs_list = list(dogs)
        self.assertEqual(len(dogs_list), 3)

        dog4 = Dog.create(self.couchdb, name="di", owner_id=paul.key)
        dog5 = Dog.create(self.couchdb, name="stevie", owner_id=paul.key)

        syncer.sync_up()
        dogs = list(paul.dogs)
        self.assertEqual(len(dogs), 5)


    # def test_sync_geo_point(self):
    #
    #     paul = Person.create(self.firestore, name="paul")
    #     sol = Person.create(self.firestore, name="sol")
    #
    #     loc = LatLong(latitude=51.2345, longitude=-1.4533)
    #     house = House.create(self.db, name="my house", location=loc)
    #
    #

