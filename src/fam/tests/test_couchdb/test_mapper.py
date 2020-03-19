import os
import shutil
import unittest
from fam.database import CouchDBWrapper
from fam.mapper import ClassMapper
from fam.schema.validator import ModelValidator
from fam.exceptions import FamValidationError
from fam.tests.test_couchdb.config import *
from fam.tests.models import test01
from fam.tests.models.test01 import Dog, Cat, Person, JackRussell
from fam.blud import StringField

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(THIS_DIR, "data")
DESIGN_PATH = os.path.join(DATA_PATH, "design_ref.json")

class MapperValidationTests(unittest.TestCase):

    def test_make_a_validator(self):

        mapper = ClassMapper([Dog, Cat, Person, JackRussell])
        validator = ModelValidator(None, classes=[Dog, Cat, Person, JackRussell])
        self.db = CouchDBWrapper(mapper, COUCHDB_URL, COUCHDB_NAME, reset=True, validator=validator)
        self.db.update_designs()

        paul = Person(name="paul")
        paul.save(self.db)
        cat = Cat(name="whiskers", owner_id=paul.key, legs=4)
        cat.save(self.db)


        self.assertEqual(cat.owner, paul)
        self.assertEqual(cat.owner.name, "paul")

        cat = Cat(name="puss", owner_id=paul.key)

        self.assertRaises(FamValidationError, cat.save, self.db)

        self.db.session.close()


    def test_make_a_validator_from_modules(self):

        mapper = ClassMapper([], modules=[test01])
        validator = ModelValidator(mapper)
        self.db = CouchDBWrapper(mapper, COUCHDB_URL, COUCHDB_NAME, reset=True, validator=validator)
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

        self.db.session.close()

        # print dog.as_json()


    def test_included_refs_from_in_validator(self):
        mapper = ClassMapper([], modules=[test01])
        validator = ModelValidator(mapper)
        self.db = CouchDBWrapper(mapper, COUCHDB_URL, COUCHDB_NAME, reset=True, validator=validator)
        self.db.update_designs()

        paul = Person(name="paul")
        paul.save(self.db)

        paul_id = paul.key
        cat = Cat(name="whiskers", owner_id=paul.key, legs=4)
        cat.save(self.db)
        self.assertEqual(cat.owner, paul)
        self.assertEqual(cat.owner.name, "paul")

        paul = Person.get(self.db, paul_id)

        paul.save(self.db)

        self.db.session.close()



    def test_string_format(self):

        mapper = ClassMapper([], modules=[test01])
        validator = ModelValidator(mapper)
        self.db = CouchDBWrapper(mapper, COUCHDB_URL, COUCHDB_NAME, reset=True, validator=validator)
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
        self.assertRaises(FamValidationError, self.db.put, cat)

        self.db.session.close()

