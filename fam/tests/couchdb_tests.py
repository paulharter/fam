import os

from fam.database import CouchDBWrapper
from config import *
from fam import namespaces
from blud_base_tests import CouchBaseTests

namespaces.add_models("fam.tests", os.path.join(os.path.dirname(__file__), "models"))

class CouchDBModelTests(CouchBaseTests):


    def setUp(self):
        self.db = CouchDBWrapper(COUCHDB_URL, COUCHDB_NAME, reset=True)


    def tearDown(self):
        pass

