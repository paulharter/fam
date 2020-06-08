import sys
import os
from fam.database import CouchDBWrapper, get_db
from fam.mapper import ClassMapper
from fam.tests.models.test01 import Dog, Cat, Person, JackRussell, Monkey, Monarch, Monster
from fam.tests.common import common_test_classes

current_module = sys.modules[__name__]

from fam.tests.test_couchdb.config import *

TEST_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(TEST_DIR, "common", "data")

def iterCouchDBTests():

    for test_class in common_test_classes:

        name = "{}CouchDB".format(test_class.__name__)

        def setUp(self):
            filepath = os.path.join(DATA_PATH, "animal_views.js")
            mapper = ClassMapper([Dog, Cat, Person, JackRussell, Monkey, Monarch, Monster], designs=[filepath])

            self.db = CouchDBWrapper(mapper, COUCHDB_URL, COUCHDB_NAME, reset=True)
            # self.db = get_db("couchdb", mapper, "localhost", db_name="test", reset=True)
            self.db.update_designs()
            super(self.__class__, self).setUp()

        def tearDown(self):
            self.db.session.close()

        methods = {
            "setUp": setUp,
            "tearDown":tearDown
        }

        setattr(current_module, name, type(name, (test_class,), methods))

iterCouchDBTests()
