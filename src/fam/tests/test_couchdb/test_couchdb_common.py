import sys
from fam.database import CouchDBWrapper
from fam.mapper import ClassMapper
from fam.tests.models.test01 import Dog, Cat, Person, JackRussell, Monkey, Monarch, Monster
from fam.tests.common import common_test_classes

current_module = sys.modules[__name__]

from fam.tests.test_couchdb.config import *

def iterCouchDBTests():

    for test_class in common_test_classes:

        name = "{}CouchDB".format(test_class.__name__)

        def setUp(self):
            mapper = ClassMapper([Dog, Cat, Person, JackRussell, Monkey, Monarch, Monster])
            self.db = CouchDBWrapper(mapper, COUCHDB_URL, COUCHDB_NAME, reset=True)
            self.db.update_designs()
            super(self.__class__, self).setUp()

        def tearDown(self):
            pass

        methods = {
            "setUp": setUp,
            "tearDown":tearDown
        }

        setattr(current_module, name, type(name, (test_class,), methods))

iterCouchDBTests()
