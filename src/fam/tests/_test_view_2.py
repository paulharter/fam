import time
import subprocess
import unittest
import requests
import json

DB_HOST = "localhost"

SYNC_GATEWAY_PATH = "/usr/local/bin/sync_gateway"
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
    "name": "rufus"
}

class ViewTests(unittest.TestCase):

    def setUp(self):
        cmd = "{} -log=* -url walrus:".format(SYNC_GATEWAY_PATH)

        time.sleep(0.25)
        self.gateway = subprocess.Popen(cmd, shell=True)
        time.sleep(0.25)


    def tearDown(self):
        # stop the gateway
        self.gateway.kill()


    def put_in_db(self, key, value):
        url = "%s/%s" % (DB_URL, key)
        rsp = requests.put(url,
                           data=json.dumps(value, indent=4, sort_keys=True),
                           headers={"Content-Type": "application/json", "Accept": "application/json"})
        self.assertEqual(rsp.status_code, 201)

    def query_view(self, design_id, view_name, key):
        url = VIEW_URL % (DB_URL, design_id, view_name, key)
        rsp = requests.get(url)
        # print rsp.text
        self.assertEqual(rsp.status_code, 200)
        results = rsp.json()
        return results["rows"]


    def test_view_without_previous_request(self):
        # put the design in the database
        self.put_in_db("_design/%s" % DESIGN_ID, ONE_DESIGN)

        # put the dog doc in the database
        self.put_in_db(DOG_ID, DOG)

        # query the view
        rows = self.query_view(DESIGN_ID, "person_dogs", OWNER_ID)

        # should find 1 row
        self.assertEqual(len(rows), 1)


    def test_view_with_previous_request(self):
        # put the design in the database
        self.put_in_db("_design/%s" % DESIGN_ID, ONE_DESIGN)

        # this previous request causes the next to fail!
        rows = self.query_view(DESIGN_ID, "person_dogs", OWNER_ID)

        # should find 1 row
        self.assertEqual(len(rows), 0)

        # put the dog doc in the database
        self.put_in_db(DOG_ID, DOG)

        # query the view
        rows = self.query_view(DESIGN_ID, "person_dogs", OWNER_ID)

        # should find 1 row
        self.assertEqual(len(rows), 1)



