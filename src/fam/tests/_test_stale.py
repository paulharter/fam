import unittest
import requests
import json
import time
import subprocess

DB_HOST = "192.168.99.100"
COUCHBASE_URL = "http://192.168.99.100:8091"

SYNC_GATEWAY_PATH = "/Users/paul/Dropbox/glowinthedark/spate/Flotsam/bin/sync_gateway_versions/1.3/sync_gateway"

# SYNC_GATEWAY_PATH = "/usr/local/bin/sync_gateway"
SYNC_GATEWAY_VIEW_URL = "%s/_design/%s/_view/%s?stale=false&key=\"%s\""

DESIGN_ID = "test"
DOG_ID = "dog"
OWNER_ID = "owner"
DB_NAME = "sync_gateway"

ONE_DESIGN = {
    "_id": DESIGN_ID,
    "views": {
        "person_dogs": {
            "map": "function(doc, meta) {\n    var resources = [\"dog\"];\n    if (resources.indexOf(doc.type) != -1){\n        doc._rev = meta.rev;\n        emit(doc.owner_id, doc);\n    }\n}"
        }
    }
}

VIEW_URL = SYNC_GATEWAY_VIEW_URL
DB_PORT = "4985"
DB_URL = "http://%s:%s/%s" % (DB_HOST, DB_PORT, DB_NAME)

DOG = {
    "type": "dog",
    "owner_id": OWNER_ID,
    "name": "fly"
}

class ViewTests(unittest.TestCase):

    def setUp(self):
        rsp = requests.post("%s/pools/default/buckets/%s/controller/doFlush" % (COUCHBASE_URL, DB_NAME), auth=("couchbase", "password"))
        if rsp.status_code != 200:
            raise Exception("failed to flush bucket %s : %s" % (rsp.status_code, rsp.text))

        # time.sleep(4)
        #
        # cmd = "{} -log=* -url {}".format(SYNC_GATEWAY_PATH, COUCHBASE_URL)
        #
        # print cmd
        #
        # time.sleep(0.25)
        # self.gateway = subprocess.Popen(cmd, shell=True)
        # time.sleep(0.25)



    def tearDown(self):
        pass
        # stop the gateway
        # self.gateway.kill()

    def put_in_db(self, key, value):

        url = "%s/%s" % (DB_URL, key)
        rsp = requests.put(url,
                           data=json.dumps(value, indent=4, sort_keys=True),
                           headers={"Content-Type": "application/json", "Accept": "application/json"})

        print rsp.text
        self.assertEqual(rsp.status_code, 201)


    def query_view(self, design_id, view_name, key):
        url = VIEW_URL % (DB_URL, design_id, view_name, key)
        rsp = requests.get(url)
        print rsp.text
        self.assertEqual(rsp.status_code, 200)
        results = rsp.json()
        return results["rows"]


    def test_design_with_one_view(self):
        time.sleep(4)

        rows = self.query_view(DESIGN_ID, "person_dogs", OWNER_ID)

        self.assertEqual(len(rows), 0)

        # put the design in the database
        self.put_in_db("_design/%s" % DESIGN_ID, ONE_DESIGN)

        time.sleep(1)

        #put the dog doc in the database
        self.put_in_db(DOG_ID, DOG)

        # query the view
        rows = self.query_view(DESIGN_ID, "person_dogs", OWNER_ID)

        # should find 1 row
        self.assertEqual(len(rows), 1)

