import unittest
import time
import sys
import subprocess
import requests
import json
from fam.utils import couchbase_utils

from fam.tests.models.test01 import Dog, Cat, Person, JackRussell, Monarch, NAMESPACE
from fam.mapper import ClassMapper

from fam.database import CouchDBWrapper, SyncGatewayWrapper

COUCHDB_URL = "http://localhost:5984"
COUCHDB_NAME = "test"

REMOTE_URL ="http://paul:password@localhost:4984/sync_gateway"

SYNC_GATEWAY_HOST = "localhost"
SYNC_GATEWAY_PORT = "4984"
SYNC_GATEWAY_ADMIN_PORT = "4985"
SYNC_GATEWAY_NAME = "sync_gateway"

if sys.platform.startswith('linux'):
    SYNC_GATEWAY_PATH = "/opt/couchbase-sync-gateway/bin/sync_gateway"
else:
    SYNC_GATEWAY_PATH = "sync_gateway"


class SingleReplicationTests(unittest.TestCase):

        def setUp(self):

            mapper = ClassMapper([Dog, Cat, Person, JackRussell, Monarch])

            #a new walrus sync gateway
            cmd = "{} -log HTTP+,Changes+,Events+    -url walrus:".format(SYNC_GATEWAY_PATH)

            time.sleep(0.5)
            self.gateway = subprocess.Popen(cmd, shell=True)
            time.sleep(0.25)

            url = "http://%s:%s" % (SYNC_GATEWAY_HOST, SYNC_GATEWAY_ADMIN_PORT)
            self.sync_gateway = SyncGatewayWrapper(mapper, url, SYNC_GATEWAY_NAME)

            couchbase_utils.add_person_to_gateway(url, SYNC_GATEWAY_NAME, "test_person", "paul", "password", admin_channels=["public"])

            # and set up a new couchdb replicating to it
            self.couchdb = CouchDBWrapper(mapper, COUCHDB_URL, COUCHDB_NAME, reset=True, remote_url=REMOTE_URL)


        def tearDown(self):

            self.couchdb.clear_all_replications()

            # stop the gateway
            print "tear_down"
            self.gateway.kill()


        def test_put_into_couchdb(self):
            dog = Dog(name="woofer", channels=["*"])
            dog.save(self.couchdb)
            self.assertEqual(dog.namespace, NAMESPACE)
            self.assertEqual(dog.type, "dog")
            self.assertEqual(dog.name, "woofer")
            self.assertEqual(dog.__class__, Dog)
            self.assertNotEqual(dog.key, None)


        def test_put_into_sync_gateway(self):
            dog = Dog(name="woofer")
            dog.save(self.sync_gateway)
            self.assertEqual(dog.namespace, NAMESPACE)
            self.assertEqual(dog.type, "dog")
            self.assertEqual(dog.name, "woofer")
            self.assertEqual(dog.__class__, Dog)
            self.assertNotEqual(dog.key, None)


        def test_single_replication_up(self):
            dog = Dog(key="test_dog", name="woofer")
            dog.save(self.couchdb)
            sync_dog = self.sync_gateway.get("test_dog")
            self.assertEqual(sync_dog, None)
            self.couchdb.sync_up()
            # time.sleep(2)
            sync_dog = self.sync_gateway.get("test_dog")
            self.assertNotEqual(sync_dog, None)


        def test_single_replication_down(self):
            dog = Dog(key="test_dog", name="woofer", channels=["public"])
            dog.save(self.sync_gateway)
            self.couchdb.sync_down()
            # time.sleep(2)
            sync_dog = self.couchdb.get("test_dog")
            self.assertNotEqual(sync_dog, None)


class ContinuousReplicationTests(unittest.TestCase):

        def setUp(self):

            mapper = ClassMapper([Dog, Cat, Person, JackRussell, Monarch])

            #a new walrus sync gateway
            cmd = "{} -log HTTP+,Changes+,Events+    -url walrus:".format(SYNC_GATEWAY_PATH)

            time.sleep(0.25)
            self.gateway = subprocess.Popen(cmd, shell=True)
            time.sleep(0.25)

            url = "http://%s:%s" % (SYNC_GATEWAY_HOST, SYNC_GATEWAY_ADMIN_PORT)
            self.sync_gateway = SyncGatewayWrapper(mapper, url, SYNC_GATEWAY_NAME)

            couchbase_utils.add_person_to_gateway(url, SYNC_GATEWAY_NAME, "test_person", "paul", "password", admin_channels=["public"])

            # and set up a new couchdb replicating to it
            self.couchdb = CouchDBWrapper(mapper, COUCHDB_URL, COUCHDB_NAME, reset=True, remote_url=REMOTE_URL, continuous=True)


        def tearDown(self):

            self.couchdb.clear_all_replications()

            # stop the gateway
            print "tear_down"
            self.gateway.kill()


        def test_single_replication_up(self):
            dog = Dog(key="test_dog", name="woofer")
            dog.save(self.couchdb)
            time.sleep(1)
            sync_dog = self.sync_gateway.get("test_dog")
            self.assertNotEqual(sync_dog, None)


        def test_single_replication_down(self):
            dog = Dog(key="test_dog", name="woofer", channels=["public"])
            dog.save(self.sync_gateway)
            time.sleep(1)
            sync_dog = self.couchdb.get("test_dog")
            self.assertNotEqual(sync_dog, None)

