from __future__ import absolute_import
import unittest
import os
import time
import json
import subprocess
from fam.database import SyncGatewayWrapper
from fam.mapper import ClassMapper
from fam.tests.test_sync_gateway.config import *
from fam.tests.models.test01 import Cat, Dog, Person
from fam.acl.writer import write_sync_function, _requirements_from_mapper
from fam.utils import couchbase_utils

from fam.exceptions import *

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(TEST_DIR, "data")

"""
Actors are people who do things

users: a set of named users
roles: a set of people who have any of given roles
owner: an owner as named in the doc
anyone: anyone as long as we know who they are

Actions are things they can do:

create: Create a new document with a new id
update: Make a change to an existing document
delete: Delete an existing document

"""


class testPermissions(unittest.TestCase):

        def setUp(self):

            self.gateway = None
            self.db = None

            self.mapper = ClassMapper([Cat, Dog])

            self.start_gateway()



        def start_gateway(self):

            cmd = "{} -log=* -url walrus: ".format(SYNC_GATEWAY_PATH)
            # print cmd

            time.sleep(0.25)
            self.gateway = subprocess.Popen(cmd, shell=True)
            time.sleep(0.25)

            admin_url = "http://%s:%s" % (SYNC_GATEWAY_ADMIN_HOST, SYNC_GATEWAY_ADMIN_PORT)
            self.admin_db = SyncGatewayWrapper(self.mapper, admin_url, SYNC_GATEWAY_NAME)
            self.admin_db.update_designs()
            self.add_users()


        def add_users(self):

            admin_url = "http://%s:%s" % (SYNC_GATEWAY_ADMIN_HOST, SYNC_GATEWAY_ADMIN_PORT)

            couchbase_utils.add_person_to_gateway(admin_url,
                                                  SYNC_GATEWAY_NAME,
                                                  "paul_id",
                                                  "paul",
                                                  "password1",
                                                  admin_channels=["cars", "paul"])

            couchbase_utils.add_person_to_gateway(admin_url,
                                                  SYNC_GATEWAY_NAME,
                                                  "sol_id",
                                                  "sol",
                                                  "password2",
                                                  admin_channels=["sol"])

            paul_url = "http://paul:password1@%s:%s" % (SYNC_GATEWAY_HOST, SYNC_GATEWAY_PORT)
            self.paul_db = SyncGatewayWrapper(self.mapper, paul_url, SYNC_GATEWAY_NAME)

            sol_url = "http://sol:password2@%s:%s" % (SYNC_GATEWAY_HOST, SYNC_GATEWAY_PORT)
            self.sol_db = SyncGatewayWrapper(self.mapper, sol_url, SYNC_GATEWAY_NAME)


        def tearDown(self):
            # stop the gateway
            if self.gateway is not None:
                self.gateway.kill()


        def test_ensure_designs(self):

            for namespace_name, namespace in self.admin_db.mapper.namespaces.items():
                view_namespace = namespace_name.replace("/", "_")
                key = "_design/%s" % view_namespace
                doc = self.mapper.get_design(namespace, namespace_name, self.admin_db.FOREIGN_KEY_MAP_STRING)
                doc["_id"] = key
                existing = self.admin_db.get_design(key)
                matches = self.admin_db._new_matches_existing(doc, existing)
                self.assertTrue(matches)

            # Add another class
            self.admin_db.mapper._add_classes([Person])

            for namespace_name, namespace in self.admin_db.mapper.namespaces.items():
                view_namespace = namespace_name.replace("/", "_")
                key = "_design/%s" % view_namespace
                doc = self.mapper.get_design(namespace, namespace_name, self.admin_db.FOREIGN_KEY_MAP_STRING)
                doc["_id"] = key
                existing = self.admin_db.get_design(key)
                matches = self.admin_db._new_matches_existing(doc, existing)

                self.assertFalse(matches)