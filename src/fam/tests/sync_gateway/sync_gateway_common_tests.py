
import sys
import time
import subprocess
import requests
from fam.database import SyncGatewayWrapper
from fam.mapper import ClassMapper
from fam.tests.sync_gateway.config import *
from fam.tests.models.test01 import Dog, Cat, Person, JackRussell, Monkey, Monarch, Monster
from fam.tests.common import common_test_classes

from fam.utils import couchbase_utils

current_module = sys.modules[__name__]

SYNC_GATEWAY_PATH = "sync_gateway"

def iterSyncGatewayTests():

    for test_class in common_test_classes:
        name = "{}SyncGateway".format(test_class.__name__)

        @classmethod
        def setUpClass(cls):

            bucket_name = "sync_gateway"
            gateway_name = "sync_gateway"

            couchbase_utils.make_bucket_and_gateway(COUCHBASE_LOCAL_URL,
                                COUCHBASE_ADMIN,
                                COUCHBASE_ADMIN_PASSWORD,
                                bucket_name,
                                COUCHDB_SYNC_ADMIN_URL,
                                gateway_name,
                                'function(doc) {channel("public");}',
                                guest=True,
                                force=True)
            time.sleep(6)

        @classmethod
        def tearDownClass(cls):

            bucket_name = "sync_gateway"
            gateway_name = "sync_gateway"
            # remove the bucket
            couchbase_utils.delete_bucket_and_gateway(COUCHBASE_LOCAL_URL,
                                    COUCHBASE_ADMIN,
                                    COUCHBASE_ADMIN_PASSWORD,
                                    bucket_name,
                                    COUCHDB_SYNC_ADMIN_URL,
                                    gateway_name)

        def setUp(self):

            self.bucket_name = "sync_gateway"
            self.gateway_name = "sync_gateway"

            couchbase_utils.flush_a_bucket(COUCHBASE_LOCAL_URL, COUCHBASE_ADMIN, COUCHBASE_ADMIN_PASSWORD, self.bucket_name)

            cmd = "{} -url http://localhost:8091".format(SYNC_GATEWAY_PATH)

            print "starting gateway"
            time.sleep(1)
            self.gateway = subprocess.Popen(cmd, shell=True)
            time.sleep(1)

            for i in range(0,5):
                try:
                    couchbase_utils.add_guest_to_gateway(COUCHDB_SYNC_ADMIN_URL, "sync_gateway")
                except requests.ConnectionError as e:
                    time.sleep(2**i)
                    print "failing {}".format(i)
                    continue
                break


            mapper = ClassMapper([Dog, Cat, Person, JackRussell, Monkey, Monarch, Monster])
            url = "http://%s:%s" % (SYNC_GATEWAY_HOST, SYNC_GATEWAY_ADMIN_PORT)
            self.db = SyncGatewayWrapper(mapper, url, SYNC_GATEWAY_NAME)
            self.db.update_designs()
            super(self.__class__, self).setUp()

        def tearDown(self):

            # stop the gateway
            print "stopping gateway"
            self.gateway.terminate()
            return

        methods = {
            "setUp": setUp,
            "tearDown":tearDown,
            "setUpClass": setUpClass,
            "tearDownClass": tearDownClass
        }

        setattr(current_module, name, type(name, (test_class,), methods))



iterSyncGatewayTests()

