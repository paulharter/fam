import os

from fam.database import CouchbaseLiteServerWrapper
from config import *
from fam import namespaces
from blud_base_tests import CouchBaseTests

namespaces.add_models("fam.tests", os.path.join(os.path.dirname(__file__), "models"))

class CBLiteModelTests(CouchBaseTests):

    def setUp(self):
        self.db = CouchbaseLiteServerWrapper(CBLITE_URL, CBLITE_NAME, reset=True)
        # self.db = CouchDBWrapper(CBLITE_URL, CBLITE_NAME, reset=True)

    def tearDown(self):
        pass


