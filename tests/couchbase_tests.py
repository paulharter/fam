import unittest
import os
import requests
import time
import json
from fam.database import CouchDBWrapper, CouchbaseWrapper
from config import *
from fam.tests.models.test01 import Dog, Cat, Person, JackRussell, NAMESPACE
from fam import namespaces
from blood_base_tests import CouchBaseTests

namespaces.add_models("fam.tests", os.path.join(os.path.dirname(__file__), "models"))



class CouchbaseModelTests(CouchBaseTests):


    def setUp(self):
        self.db = CouchbaseWrapper(COUCHBASE_HOST, COUCHBASE_PORT, COUCHBASE_BUCKET, COUCHBASE_ADMIN, COUCHBASE_ADMIN_PASSWORD, reset=True)

    def tearDown(self):
        pass

