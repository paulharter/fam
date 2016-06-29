import sys
import time
import subprocess
from fam.database import SyncGatewayWrapper
from fam.mapper import ClassMapper
from fam.tests.test_sync_gateway.config import *
from fam.tests.models.test01 import Dog, Cat, Person, JackRussell, Monkey, Monarch, Monster
from fam.tests.common import common_test_classes

current_module = sys.modules[__name__]

def iterSyncGatewayTests():

    for test_class in common_test_classes:
        name = "{}SyncGateway".format(test_class.__name__)

        def setUp(self):

            cmd = "{} -url walrus:".format(SYNC_GATEWAY_PATH)

            time.sleep(0.25)
            self.gateway = subprocess.Popen(cmd, shell=True)
            time.sleep(0.25)

            mapper = ClassMapper([Dog, Cat, Person, JackRussell, Monkey, Monarch, Monster])
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

