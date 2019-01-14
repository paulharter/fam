from __future__ import absolute_import
import os
import unittest
from fam.database import CouchDBWrapper
from fam.mapper import ClassMapper
from fam.buffer.buffer_views import FamWriteBufferViews
from fam.tests.test_couchdb.config import *
from fam.tests.models.test01 import Dog, Cat, Person

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(THIS_DIR, "data")

class CacheTests(unittest.TestCase):


    def setUp(self):
        self.mapper = ClassMapper([Dog, Cat, Person])
        self.db = CouchDBWrapper(self.mapper, COUCHDB_URL, COUCHDB_NAME, reset=True)
        self.db.update_designs()

    def tearDown(self):
        self.db.session.close()


    def test_make_views(self):

        views = FamWriteBufferViews(self.mapper)
        paul = Person(name="paul")
        dog = Dog(name="woofer", owner=paul)
        views.index_obj(dog)
        self.assertTrue(views.indexes.get("glowinthedark_co_uk_test_person_dogs") != None)
        self.assertTrue(views.indexes["glowinthedark_co_uk_test_person_dogs"][paul.key][dog.key] == dog)


    def test_query_views(self):

        views = FamWriteBufferViews(self.mapper)
        paul = Person(name="paul")
        dog = Dog(name="woofer", owner=paul)
        views.index_obj(dog)
        obj = views.query_view("glowinthedark.co.uk/test/person_dogs", key=paul.key)
        self.assertEqual(obj, [dog])


    def test_views_keys(self):

        views = FamWriteBufferViews(self.mapper)
        paul = Person(name="paul")
        dog = Dog(name="woofer", owner=paul)
        views.index_obj(dog)

        print("keys: ", views.indexes.keys())

        self.assertEqual(set(views.indexes.keys()), {'glowinthedark_co_uk_test_person_animals',
                                                'glowinthedark_co_uk_test_person_dogs',
                                                'raw_all',
                                                'glowinthedark_co_uk_test_dog_kennel_club_membership'})




