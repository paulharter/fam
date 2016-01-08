import os
import unittest
from fam.database import CouchDBWrapper
from fam.mapper import ClassMapper
from fam.exceptions import FamValidationError
from fam.tests.couchdb.config import *
from fam.tests.models import test01
from fam.tests.models.test01 import Dog, Cat, Person, JackRussell

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(THIS_DIR, "data")

class MapperValidationTests(unittest.TestCase):

    def test_make_a_validator(self):

        mapper = ClassMapper([Dog, Cat, Person, JackRussell])
        self.db = CouchDBWrapper(mapper, COUCHDB_URL, COUCHDB_NAME, reset=True)
        self.db.update_designs()

        paul = Person(name="paul")
        paul.save(self.db)
        cat = Cat(name="whiskers", owner_id=paul.key, legs=4)
        cat.save(self.db)
        self.assertEqual(cat.owner, paul)
        self.assertEqual(cat.owner.name, "paul")

        cat = Cat(name="puss", owner_id=paul.key)

        self.assertRaises(FamValidationError, cat.save, self.db)


    def test_make_a_validator_from_modules(self):

        mapper = ClassMapper([], modules=[test01])
        self.db = CouchDBWrapper(mapper, COUCHDB_URL, COUCHDB_NAME, reset=True)
        self.db.update_designs()

        paul = Person(name="paul")
        paul.save(self.db)
        cat = Cat(name="whiskers", owner_id=paul.key, legs=4)
        cat.save(self.db)
        self.assertEqual(cat.owner, paul)
        self.assertEqual(cat.owner.name, "paul")

        #missing legs
        cat = Cat(name="puss", owner_id=paul.key)

        self.assertRaises(FamValidationError, cat.save, self.db)

        #additional properties
        def failing_cat():
            cat = Cat(name="puss", owner_id=paul.key, legs=2, collar="green")

        self.assertRaises(FamValidationError, failing_cat)
        dog = Dog(name="fly")
        self.db.put(dog)
        dog.tail = "long"
        self.db.put(dog)

        print dog.as_json()



    def test_string_format(self):

        mapper = ClassMapper([], modules=[test01])
        self.db = CouchDBWrapper(mapper, COUCHDB_URL, COUCHDB_NAME, reset=True)
        self.db.update_designs()

        paul = Person(name="paul")
        paul.save(self.db)
        cat = Cat(name="whiskers", owner_id=paul.key, legs=4)
        cat.save(self.db)
        self.assertEqual(cat.owner, paul)
        self.assertEqual(cat.owner.name, "paul")

        cat = Cat(name="puss", owner_id=paul.key, legs=3, email="paul@glowinthedark.co.uk")
        cat.save(self.db)
        cat.email = "paulglowinthedark.co.uk"
        self.assertRaises(FamValidationError, self.db.save, cat)


class WritingSchemaTests(unittest.TestCase):


    def test_make_a_validator_from_modules(self):

        mapper = ClassMapper([], modules=[test01])
        mapper.validator.write_out_schemata(DATA_PATH)