import os
import unittest
from fam.database import CouchDBWrapper
from fam.mapper import ClassMapper

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

    def test_create_index(self):
        filepath = os.path.join(THIS_DIR, "animal_views.js")

        as_dict = self.db.mapper._js_design_as_doc(filepath)

        expected = {
            "_id": "_design/animal_views",
            "views": {
                "cat_legs": {
                    "map": "function(doc) {\n  if (doc.type == \"cat\") {\n    emit(doc.legs, doc);\n  }\n}"
                }
            }
        }

        self.assertEqual(as_dict, expected)


    def test_query_view(self):

        paul = Person(name="Paul")
        self.db.put(paul)
        cat1 = Cat(owner=paul, legs=4)
        self.db.put(cat1)
        cat2 = Cat(owner=paul, legs=3)
        self.db.put(cat2)
        three_legged_cats = Cat.all_with_n_legs(self.db, 3)
        self.assertEqual(len(three_legged_cats), 1)

        self.assertEqual(three_legged_cats[0].key, cat2.key)


    def test_long_polling(self):
        paul = Person(name="Paul")
        self.db.put(paul)
        cat1 = Cat(owner=paul, legs=4)
        self.db.put(cat1)
        cat2 = Cat(owner=paul, legs=3)
        self.db.put(cat2)
        three_legged_cats = self.db.view("animal_views/cat_legs", key=3)
        self.assertEqual(len(three_legged_cats), 1)
        self.assertEqual(three_legged_cats[0].key, cat2.key)