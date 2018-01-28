import unittest
import os
import time
import json
import subprocess
from fam.database import SyncGatewayWrapper
from fam.mapper import ClassMapper
from fam.tests.test_sync_gateway.config import *
from fam.tests.models.acl import Car, Bike, Boat
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

            self.mapper = ClassMapper([Car, Boat])

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


        def test_get_user(self):

            user_info = self.admin_db.user("paul")
            # print user_info
            self.assertTrue(user_info != None)
            roles = user_info["admin_roles"]

            self.assertEqual(roles, ["paul_id"])


        def test_create_role(self):

            role_info = self.admin_db.role("new_role")
            # print "role: ",  role_info
            self.assertTrue(role_info == None)

            self.admin_db.ensure_role("new_role")

            role_info = self.admin_db.role("new_role")
            # print "role: ",  role_info
            self.assertTrue(role_info != None)


        def test_add_role(self):

            user_info = self.admin_db.user("paul")
            self.assertTrue(user_info != None)
            roles = user_info["admin_roles"]
            self.assertEqual(roles, ["paul_id"])
            channels = user_info["admin_channels"]
            self.assertEqual(set(channels), set(["cars", "paul"]))

            success = self.admin_db.ensure_user_role("paul", "new_role")

            self.assertTrue(success)

            user_info = self.admin_db.user("paul")
            self.assertTrue(user_info != None)
            roles = user_info["admin_roles"]
            channels = user_info["admin_channels"]
            self.assertEqual(set(roles), set(["paul_id", "new_role"]))
            self.assertEqual(set(channels), set(["cars", "paul"]))





