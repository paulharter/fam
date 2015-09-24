import json
import unittest

from fam.tests.models.test01 import GenericObject, Dog, Cat, Person, JackRussell, NAMESPACE

from fam.schema.writer import writeJsonSchema

class SchemalTests(unittest.TestCase):

    cat_schema = writeJsonSchema(Cat)

    print json.dumps(cat_schema, indent=4)