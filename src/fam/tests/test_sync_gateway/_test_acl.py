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



        def start_gateway(self, conf_file_path):

            cmd = "{} -log=* {}".format(SYNC_GATEWAY_PATH, conf_file_path)
            print cmd

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


        def test_index_permissions(self):

            expected = {
                "create": {
                    "car": {
                        "owner": True
                    },
                    "boat": {
                        "owner": True,
                        "withoutAccess": True
                    }
                },
                "update": {
                    "car": [
                        {
                            "fields": [
                                "access"
                            ],
                            "role": []
                        },
                        {
                            "owner": True,
                            "fields": [
                                "colour"
                            ]
                        }
                    ],
                    "boat": [
                        {
                            "role": []
                        }
                    ]
                },
                "delete": {
                    "car": {
                        "owner": True
                    },
                    "boat": {
                        "owner": True
                    }
                }
            }



            requirements = _requirements_from_mapper(self.mapper)

            print json.dumps(requirements, indent=4)

            self.assertEqual(expected, requirements)


        def test_write_permissions(self):

            src_path = os.path.join(DATA_PATH, "sync_conf_template")
            dst_path = os.path.join(DATA_PATH, "sync_conf")

            if os.path.exists(dst_path):
                os.remove(dst_path)

            write_sync_function(src_path, dst_path, self.mapper)

            self.start_gateway(dst_path)


        def test_owner_create(self):

            self.test_write_permissions()

            car = Car(colour="red", stars=3, owner_name="paul", channels=["cars", "sol"])
            self.paul_db.put(car)

            car.colour = "green"
            self.paul_db.put(car)
            car.stars = 2
            self.paul_db.put(car)
            self.paul_db.delete(car)

            car2 = Car(colour="green", owner_name="sol", channels=["cars", "sol"])
            self.assertRaises(FamResourceConflict, self.paul_db.put, car2)


        def test_non_owner_permissions(self):

            self.test_write_permissions()

            car = Car(colour="red", stars=3, owner_name="paul", channels=["cars", "sol"])
            self.paul_db.put(car)
            sols_car = self.sol_db.get(car.key)

            ## changing green fails
            sols_car.colour = "green"
            self.assertRaises(FamResourceConflict, self.sol_db.put, sols_car)

            ## changing stars works
            sols_car.colour = "red"
            sols_car.stars = 2
            self.sol_db.put(sols_car)

            # check nn owner cant delete
            self.assertRaises(FamResourceConflict, self.sol_db.delete, sols_car)


        def test_wrong_owner_create_fails(self):

            self.test_write_permissions()
            car = Car(colour="red", stars=3, owner_name="sol", channels=["cars", "sol"])
            self.assertRaises(FamResourceConflict, self.paul_db.put, car)


        def test_create_access(self):
            self.test_write_permissions()
            car1 = Car(colour="red", stars=3, owner_name="sol", channels=["sol"])
            self.sol_db.put(car1)
            self.sol_db.get(car1.key)

            car2 = Car(colour="green", stars=2, owner_name="sol", channels=["paul"])
            self.assertRaises(Exception, self.sol_db.put, car2)
            self.sol_db.get(car2.key)


        def test_change_access_without_permission_fails(self):
            self.test_write_permissions()
            car = Car(colour="red", stars=3, owner_name="paul", channels=["cars"])
            self.paul_db.put(car)
            car.access = ["sol"]
            self.assertRaises(FamResourceConflict, self.paul_db.put, car)


        def test_change_access(self):
            self.test_write_permissions()
            car = Car(key="cars", colour="red", stars=3, owner_name="paul", channels=["cars"])
            self.paul_db.put(car)

            ## sol cant get car
            self.assertRaises(Exception, self.sol_db.get, "cars")

            car.access = ["sol"]
            self.admin_db.put(car)
            self.sol_db.get(car.key)


        def test_no_access(self):
            self.test_write_permissions()
            bike = Bike(wheels = 2)
            self.assertRaises(Exception, self.paul_db.put, bike)


        def test_no_access_admin(self):
            self.test_write_permissions()
            bike = Bike(wheels=2)
            self.admin_db.put(bike)


        def test_own_access_create(self):

            self.test_write_permissions()
            boat_id = "boaty"
            boat = Boat(key=boat_id, name="steve", is_sail=True, owner_name="paul", access=["paul"], channels=[boat_id])
            self.paul_db.put(boat)




