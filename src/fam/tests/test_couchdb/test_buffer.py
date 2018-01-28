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
        pass


    def test_cache_saves(self):

        with buffered_db(self.db) as dbc:
            dog = Dog(name="woofer")
            dbc.put(dog)

        got = self.db.get(dog.key)

        self.assertTrue(got is not None)


    def test_cache_doesnt_save(self):
        # doesnt save until were done

        with buffered_db(self.db) as dbc:
            dog = Dog(name="woofer")
            dbc.put(dog)
            got = self.db.get(dog.key)
            self.assertTrue(got is None)

        got = self.db.get(dog.key)
        self.assertTrue(got is not None)

    def test_cache_gets(self):
        # doesnt save until were done

        with buffered_db(self.db) as dbc:
            dog = Dog(name="woofer")
            dbc.put(dog)
            fetched = dbc.get(dog.key)
            self.assertTrue(fetched is not None)
            self.assertEqual(id(dog), id(fetched))


    def test_cache_gets_from_db(self):

        dog = Dog(name="woofer")
        self.db.put(dog)

        with buffered_db(self.db) as dbc:
            fetched = dbc.get(dog.key)
            self.assertTrue(fetched is not None)
            self.assertNotEqual(id(dog), id(fetched))
            fetched_again = dbc.get(dog.key)

            self.assertEqual(id(fetched), id(fetched_again))

    def test_cache_gets_change_from_db(self):

        dog = Dog(name="woofer")
        self.db.put(dog)

        with buffered_db(self.db) as dbc:
            fetched = dbc.get(dog.key)
            self.assertTrue(fetched is not None)
            self.assertNotEqual(id(dog), id(fetched))
            fetched_again = dbc.get(dog.key)
            self.assertTrue(fetched_again is not None)

            self.assertEqual(id(fetched), id(fetched_again))
            dog.name = "fly"
            self.db.put(dog)

            fetched_yet_again = dbc.get(dog.key)
            self.assertTrue(fetched_yet_again is not None)

            self.assertEqual(id(fetched), id(fetched_yet_again))
            self.assertEqual(fetched_yet_again.name, 'fly')
            fetched_yet_again.name = "bluebottle"
            db_fetched = self.db.get(dog.key)
            self.assertEqual(db_fetched.name, 'fly')

        db_fetched = self.db.get(dog.key)
        self.assertEqual(db_fetched.name, 'fly')


    def test_saves_putted(self):

        dog = Dog(name="woofer")
        self.db.put(dog)

        with buffered_db(self.db) as dbc:
            fetched = dbc.get(dog.key)
            fetched.name = "bluebottle"
            dbc.put(fetched)

        db_fetched = self.db.get(dog.key)
        self.assertEqual(db_fetched.name, 'bluebottle')



    def test_refs_from(self):

        with buffered_db(self.db) as dbc:

            person = Person(name="paul")
            dbc.put(person)

            dog = Dog(name="woofer", owner=person)
            dbc.put(dog)

            self.assertEqual(person.dogs, [dog])

