import json
import os
import unittest
from fam.exceptions import FamValidationError
from fam.tests.models import test01
from fam.tests.models.test01 import Dog, Cat, Person, JackRussell

from fam.schema.writer import createJsonSchema
from fam.schema.validator import ModelValidator

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(THIS_DIR, "data")

class SchemaBaseTests:

    class SchemaTests(unittest.TestCase):

        db = None

        def test_make_a_schema(self):
            expected = {
                "title": "A Fam object model for class glowinthedark.co.uk/test/1:Cat",
                "required": [
                    "legs",
                    "owner_id"
                ],
                "properties": {
                    "colour": {
                        "type": "string"
                    },
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
                    },
                    "tail": {
                        "type": "boolean"
                    },
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
