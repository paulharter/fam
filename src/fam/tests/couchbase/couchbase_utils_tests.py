import unittest
import requests
from config import *
import time

from fam.utils import couchbase_utils

class CouchbaseTests(object):


    def test_talk_to_server(self):
        rsp = requests.get("%s/pools/nodes" % (COUCHBASE_LOCAL_URL))
        self.assertTrue(rsp.status_code < 300)


    def test_make_and_delete_a_bucket(self):

        bucket_name = "test_bucket"
        origional_count = couchbase_utils.number_of_buckets(COUCHBASE_LOCAL_URL, COUCHBASE_ADMIN, COUCHBASE_ADMIN_PASSWORD)

        couchbase_utils.make_a_bucket(COUCHBASE_LOCAL_URL, COUCHBASE_ADMIN, COUCHBASE_ADMIN_PASSWORD, bucket_name)
        count = couchbase_utils.number_of_buckets(COUCHBASE_LOCAL_URL, COUCHBASE_ADMIN, COUCHBASE_ADMIN_PASSWORD)
        self.assertEquals(count, origional_count + 1)


        couchbase_utils.delete_a_bucket(COUCHBASE_LOCAL_URL, COUCHBASE_ADMIN, COUCHBASE_ADMIN_PASSWORD, bucket_name)
        count = couchbase_utils.number_of_buckets(COUCHBASE_LOCAL_URL, COUCHBASE_ADMIN, COUCHBASE_ADMIN_PASSWORD)
        self.assertEquals(count, origional_count)


    def test_make_flush_a_bucket(self):

        bucket_name = "test_bucket"
        couchbase_utils.delete_a_bucket(COUCHBASE_LOCAL_URL, COUCHBASE_ADMIN, COUCHBASE_ADMIN_PASSWORD, bucket_name)


        origional_count = couchbase_utils.number_of_buckets(COUCHBASE_LOCAL_URL, COUCHBASE_ADMIN, COUCHBASE_ADMIN_PASSWORD)

        couchbase_utils.make_a_bucket(COUCHBASE_LOCAL_URL, COUCHBASE_ADMIN, COUCHBASE_ADMIN_PASSWORD, bucket_name)
        count = couchbase_utils.number_of_buckets(COUCHBASE_LOCAL_URL, COUCHBASE_ADMIN, COUCHBASE_ADMIN_PASSWORD)
        self.assertEquals(count, origional_count + 1)

        time.sleep(1)

        couchbase_utils.flush_a_bucket(COUCHBASE_LOCAL_URL, COUCHBASE_ADMIN, COUCHBASE_ADMIN_PASSWORD, bucket_name)


        couchbase_utils.delete_a_bucket(COUCHBASE_LOCAL_URL, COUCHBASE_ADMIN, COUCHBASE_ADMIN_PASSWORD, bucket_name)
        count = couchbase_utils.number_of_buckets(COUCHBASE_LOCAL_URL, COUCHBASE_ADMIN, COUCHBASE_ADMIN_PASSWORD)
        self.assertEquals(count, origional_count)


    def test_ensure_empty_bucket(self):

        bucket_name = "test_bucket"
        origional_count = couchbase_utils.number_of_buckets(COUCHBASE_LOCAL_URL, COUCHBASE_ADMIN, COUCHBASE_ADMIN_PASSWORD)


        couchbase_utils.make_a_bucket(COUCHBASE_LOCAL_URL, COUCHBASE_ADMIN, COUCHBASE_ADMIN_PASSWORD, bucket_name)
        count = couchbase_utils.number_of_buckets(COUCHBASE_LOCAL_URL, COUCHBASE_ADMIN, COUCHBASE_ADMIN_PASSWORD)
        self.assertEquals(count, origional_count + 1)

        couchbase_utils.make_a_bucket(COUCHBASE_LOCAL_URL, COUCHBASE_ADMIN, COUCHBASE_ADMIN_PASSWORD, bucket_name, force=True)
        count = couchbase_utils.number_of_buckets(COUCHBASE_LOCAL_URL, COUCHBASE_ADMIN, COUCHBASE_ADMIN_PASSWORD)
        self.assertEquals(count, origional_count + 1)

        couchbase_utils.delete_a_bucket(COUCHBASE_LOCAL_URL, COUCHBASE_ADMIN, COUCHBASE_ADMIN_PASSWORD, bucket_name)
        count = couchbase_utils.number_of_buckets(COUCHBASE_LOCAL_URL, COUCHBASE_ADMIN, COUCHBASE_ADMIN_PASSWORD)
        self.assertEquals(count, origional_count)


class SyncGatewayTests(unittest.TestCase):


    def test_make_a_gateway(self):

        bucket_name = "test_bucket"

        couchbase_utils.make_a_bucket(COUCHBASE_LOCAL_URL, COUCHBASE_ADMIN, COUCHBASE_ADMIN_PASSWORD, bucket_name, force=True)

        try:
            couchbase_utils.make_a_gateway(COUCHDB_SYNC_ADMIN_URL, "test_gateway", COUCHBASE_LOCAL_URL, bucket_name, "function(doc) {channel(doc.channels);}", force=True)
            couchbase_utils.delete_a_gateway(COUCHDB_SYNC_ADMIN_URL, "test_gateway")

        finally:
            couchbase_utils.delete_a_bucket(COUCHBASE_LOCAL_URL, COUCHBASE_ADMIN, COUCHBASE_ADMIN_PASSWORD, bucket_name)



    def test_add_guest(self):

        bucket_name = "test_bucket"

        couchbase_utils.make_a_bucket(COUCHBASE_LOCAL_URL, COUCHBASE_ADMIN, COUCHBASE_ADMIN_PASSWORD, bucket_name, force=True)


        try:
            couchbase_utils.make_a_gateway(COUCHDB_SYNC_ADMIN_URL, "test_gateway", COUCHBASE_LOCAL_URL, bucket_name, "function(doc) {channel(doc.channels);}", force=True)
            couchbase_utils.add_guest_to_gateway(COUCHDB_SYNC_ADMIN_URL, "test_gateway")
            couchbase_utils.delete_a_gateway(COUCHDB_SYNC_ADMIN_URL, "test_gateway")

        finally:
            couchbase_utils.delete_a_bucket(COUCHBASE_LOCAL_URL, COUCHBASE_ADMIN, COUCHBASE_ADMIN_PASSWORD, bucket_name)



class BigFatTest(unittest.TestCase):

    def test_making_both_bucket_and_gateway(self):

        bucket_name = "test_bucket"
        gateway_name = "test_gateway"

        try:
            couchbase_utils.make_bucket_and_gateway(COUCHBASE_LOCAL_URL,
                                COUCHBASE_ADMIN,
                                COUCHBASE_ADMIN_PASSWORD,
                                bucket_name,
                                COUCHDB_SYNC_ADMIN_URL,
                                gateway_name,
                                "function(doc) {channel(doc.channels);}",
                                guest=True,
                                force=True)



        finally:
            couchbase_utils.delete_bucket_and_gateway(COUCHBASE_LOCAL_URL,
                                COUCHBASE_ADMIN,
                                COUCHBASE_ADMIN_PASSWORD,
                                bucket_name,
                                COUCHDB_SYNC_ADMIN_URL,
                                gateway_name)