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
                "title": "A Fam object model for class glowinthedark.co.uk/test:Cat",
                "required": ['legs', 'namespace', 'owner_id', 'type'],
                "properties": {
                    "_id": {"type": "string"},
                    "_rev": {"type": "string"},
                    "name": {
                        "type": "string"
                    },
                    "colour": {
                        "type": "string"
                    },
                    "namespace": {
                        "pattern": "glowinthedark.co.uk/test",
                        "type": "string"
                    },
                    "owner_id": {
                        "type": "string"
                    },
                    "_deleted": {
                        "type": "boolean"
                    },
                    "tail": {
                        "type": "boolean"
                    },
                    "legs": {
                        "type": "number"
                    },
                    "type": {
                        "pattern": "cat",
                        "type": "string"
                    },
                    "schema": {
                        "type": "string"
                    },
                    "email": {
                        "type": "string",
                        "pattern": "^([-!#$%&'*+/=?^_`{}|~0-9a-zA-Z]+(\\.[-!#$%&'*+/=?^_`{}|~0-9a-zA-Z]+)*|^\"([\\001-\\010\\013\\014\\016-\\037!#-\\[\\]-\\177]|\\\\[\\001-011\\013\\014\\016-\\177])*\")@(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\\.)+[a-zA-Z]{2,6}\\.?$"
                    }
                },
                "additionalProperties": False,
                "$schema": "http://json-schema.org/draft-04/schema#",
                "type": "object"
            }

            cat_schema = createJsonSchema(Cat)

            print(json.dumps(cat_schema, indent=4))
            self.maxDiff = None
            self.assertEqual(expected, cat_schema)


        def test_make_a_validator(self):


            validator = ModelValidator(None)

            validator.add_schema(test01.NAMESPACE, "cat", Cat)
            validator.add_schema(test01.NAMESPACE, "person", Person)

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

            validator = ModelValidator(None, classes=[Cat, Person])

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



