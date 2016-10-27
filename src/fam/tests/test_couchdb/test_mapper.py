import os
import shutil
import unittest
from fam.database import CouchDBWrapper
from fam.mapper import ClassMapper
from fam.exceptions import FamValidationError
from fam.tests.test_couchdb.config import *
from fam.tests.models import test01
from fam.tests.models.test01 import Dog, Cat, Person, JackRussell
from fam.blud import StringField

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

        # print dog.as_json()


    def test_included_refs_from_in_validator(self):
        mapper = ClassMapper([], modules=[test01])
        self.db = CouchDBWrapper(mapper, COUCHDB_URL, COUCHDB_NAME, reset=True)
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
        self.assertRaises(FamValidationError, self.db.put, cat)


class WritingSchemaTests(unittest.TestCase):


    def test_make_a_validator_from_modules(self):

        mutations_path = os.path.join(DATA_PATH, "mutations")
        schemata_path = os.path.join(DATA_PATH, "schemata")
        dog_dir = os.path.join(DATA_PATH, "schemata", "glowinthedark.co.uk", "test", "dog")

        if os.path.exists(mutations_path):
            shutil.rmtree(mutations_path)

        os.makedirs(mutations_path)

        if os.path.exists(schemata_path):
            shutil.rmtree(schemata_path)

        mapper = ClassMapper([], modules=[test01], schema_dir=DATA_PATH)
        mapper.validator.write_out_schemata()

        # did it write a schema
        dog_schemas = os.listdir(dog_dir)
        self.assertEqual(len(dog_schemas), 1)
        self.assertTrue(dog_schemas[0].endswith(".json"))

        mapper = ClassMapper([Dog, Cat, Person, JackRussell], schema_dir=DATA_PATH)
        mapper.validator.write_out_schemata()

        # wthout a change there is no mutations
        mutation_names = os.listdir(mutations_path)
        self.assertTrue(mutation_names == [])

        Dog.fields["hat"] = StringField()

        mapper = ClassMapper([Dog, Cat, Person, JackRussell], schema_dir=DATA_PATH)
        mapper.validator.write_out_schemata()

        # did it write a schema
        dog_schemas = os.listdir(dog_dir)
        # print dog_schemas
        self.assertEqual(len(dog_schemas), 2)

        # now there is one
        mutation_names = os.listdir(mutations_path)
        self.assertFalse(mutation_names == [])

        self.db = CouchDBWrapper(mapper, COUCHDB_URL, COUCHDB_NAME, reset=True)
        self.db.update_designs()

        dog = Dog(name="woofer")
        dog.save(self.db)

        self.assertTrue(dog.schema.startswith("glowinthedark.co.uk/test/dog/"))
