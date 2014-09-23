import unittest
import os
import requests
import time
from fam.database import CouchDBWrapper
from config import *
from fam.tests.models.test01 import Dog
from fam import namespaces
from fam import couchbase_utils

namespaces.add_models("fam.tests", os.path.join(os.path.dirname(__file__), "models"))
# namespaces.update_designs(COUCHDB_URL)


class SyncGatewayTests(unittest.TestCase):

    def setUp(self):

        self.bucket_name = "sync_bucket"
        self.gateway_name = "sync_gateway"

        couchbase_utils.add_guest_to_gateway(COUCHDB_SYNC_ADMIN_URL, "sync_gateway")

        # couchbase_utils.make_bucket_and_gateway(COUCHBASE_LOCAL_URL,
        #                     COUCHBASE_ADMIN,
        #                     COUCHBASE_ADMIN_PASSWORD,
        #                     self.bucket_name,
        #                     COUCHDB_SYNC_ADMIN_URL,
        #                     self.gateway_name,
        #                     'function(doc) {channel("public");}',
        #                     guest=True,
        #                     force=True)


        self.db = self._new_local_db()


    def _new_local_db(self):
        return CouchDBWrapper(COUCHDB_URL, COUCHDB_NAME, reset=True, remote_url="%s/%s" % (COUCHDB_SYNC_URL, self.gateway_name))


    def tearDown(self):
        return
        couchbase_utils.delete_bucket_and_gateway(COUCHBASE_LOCAL_URL,
                                COUCHBASE_ADMIN,
                                COUCHBASE_ADMIN_PASSWORD,
                                self.bucket_name,
                                COUCHDB_SYNC_ADMIN_URL,
                                self.gateway_name)


    def test_sync(self):
        time.sleep(4)
        dog = Dog(name="woofer")
        dog.save(self.db)
        key = dog.key
        self.db.sync_up()
        time.sleep(1)
        self.db = self._new_local_db()
        dog = Dog.get(self.db, key)
        self.assertEqual(dog, None)
        self.db.sync_down()
        dog = Dog.get(self.db, key)
        self.assertNotEqual(dog, None)
        self.assertEqual(dog.name, "woofer")
        self.assertEqual(dog.key, key)



