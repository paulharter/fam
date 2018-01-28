import sys
import os
import time
import subprocess
from fam.database import SyncGatewayWrapper
from fam.mapper import ClassMapper
from fam.tests.test_sync_gateway.config import *
from fam.tests.models.test01 import Dog, Cat, Person, JackRussell, Monkey, Monarch, Monster
from fam.tests.common import common_test_classes

current_module = sys.modules[__name__]

TEST_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(TEST_DIR, "common", "data")

def iterSyncGatewayTests():

    for test_class in common_test_classes:
        name = "{}SyncGateway".format(test_class.__name__)

        def setUp(self):

            cmd = "{} -log=* -url walrus: ".format(SYNC_GATEWAY_PATH)
            # print cmd

            time.sleep(0.25)
            self.gateway = subprocess.Popen(cmd, shell=True)
            time.sleep(0.25)
            filepath = os.path.join(DATA_PATH, "animal_views.js")
            mapper = ClassMapper([Dog, Cat, Person, JackRussell, Monkey, Monarch, Monster], designs=[filepath])

            url = "http://%s:%s" % (SYNC_GATEWAY_ADMIN_HOST, SYNC_GATEWAY_ADMIN_PORT)
            self.db = SyncGatewayWrapper(mapper, url, SYNC_GATEWAY_NAME)
            self.db.update_designs()
            super(self.__class__, self).setUp()

        def tearDown(self):
            # stop the gateway
            self.gateway.kill()

        methods = {
            "setUp": setUp,
            "tearDown":tearDown
        }

        setattr(current_module, name, type(name, (test_class,), methods))


## not running the gateway tests for circle as walrus doesnt work properly there
iterSyncGatewayTests()

