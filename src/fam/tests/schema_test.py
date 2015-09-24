import json
import jsonschema
import unittest
from fam.database import CouchDBWrapper
from fam.mapper import ClassMapper
from fam.exceptions import FamValidationError
from config import *
from fam.tests.models import test01
from fam.tests.models.test01 import GenericObject, Dog, Cat, Person, JackRussell, NAMESPACE

from fam.schema.writer import createJsonSchema
from fam.schema.validator import ModelValidator

class SchemalTests(unittest.TestCase):

    def setUp(self):
        mapper = ClassMapper([Dog, Cat, Person, JackRussell])
        self.db = CouchDBWrapper(mapper, COUCHDB_URL, COUCHDB_NAME, reset=True)
        self.db.update_designs()

    def tearDown(self):
        pass


    def test_make_a_schema(self):

        expected = {
            "title": "A Fam object model for class glowinthedark.co.uk/test/1:Cat",
            "required": [
                "legs",
                "owner_id"
            ],
            "properties": {
                "name": {
                    "type": "string"
                },
                "namespace": {
                    "pattern": "glowinthedark.co.uk/test/1",
                    "type": "string"
                },
                "legs": {
                    "type": "number"
                },
                "type": {
                    "pattern": "cat",
                    "type": "string"
                },
                "email": {
                    "pattern": """^([-!#$%&'*+/=?^_`{}|~0-9a-zA-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9a-zA-Z]+)*|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*")@(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}\.?$""",
                    "type": "string"
                },
                "owner_id": {
                    "type": "string"
                }
            },
            "additionalProperties": False,
            "$schema": "http://json-schema.org/draft-04/schema#",
            "type": "object",
            "id": "glowinthedark.co.uk/test/1::cat"
        }



        cat_schema = createJsonSchema(Cat)

        print json.dumps(cat_schema, indent=4)
        self.maxDiff = None
        self.assertEqual(expected, cat_schema)


    def test_make_a_validator(self):

        cat_schema = createJsonSchema(Cat)
        person_schema = createJsonSchema(Person)
        validator = ModelValidator()
        validator.add_schema(cat_schema)
        validator.add_schema(person_schema)

        #add validator to db
        self.db.validator = validator

        paul = Person(name="paul")
        paul.save(self.db)
        cat = Cat(name="whiskers", owner_id=paul.key, legs=4)
        cat.save(self.db)
        self.assertEqual(cat.owner, paul)
        self.assertEqual(cat.owner.name, "paul")

        cat = Cat(name="puss", owner_id=paul.key)

        self.assertRaises(FamValidationError, cat.save, self.db)


    def test_make_a_validator_from_classes(self):

        validator = ModelValidator(classes=[Cat, Person])

        #add validator to db
        self.db.validator = validator

        paul = Person(name="paul")
        paul.save(self.db)
        cat = Cat(name="whiskers", owner_id=paul.key, legs=4)
        cat.save(self.db)
        self.assertEqual(cat.owner, paul)
        self.assertEqual(cat.owner.name, "paul")

        cat = Cat(name="puss", owner_id=paul.key)

        self.assertRaises(FamValidationError, cat.save, self.db)


    def test_make_a_validator_from_modules(self):

        validator = ModelValidator(modules=[test01])

        #add validator to db
        self.db.validator = validator

        paul = Person(name="paul")
        paul.save(self.db)
        cat = Cat(name="whiskers", owner_id=paul.key, legs=4)
        cat.save(self.db)
        self.assertEqual(cat.owner, paul)
        self.assertEqual(cat.owner.name, "paul")

        cat = Cat(name="puss", owner_id=paul.key)

        self.assertRaises(FamValidationError, cat.save, self.db)


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

        cat = Cat(name="puss", owner_id=paul.key)

        self.assertRaises(FamValidationError, cat.save, self.db)

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
