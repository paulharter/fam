import couchdb
import json
from couchbase.exceptions import NotFoundError
from couchbase import Couchbase
from couchbase.views.params import Query
from couchbase.views.iterator import View
import namespaces
from fam import couchbase_utils

import requests

import time


class ResultWrapper(object):

    def __init__(self, d):
        self.key = d["_id"]
        self.cas = d["_rev"]
        del d["_id"]
        del d["_rev"]
        self.value = d


class CouchbaseLiteServerWrapper(object):

    def __init__(self, db_url, db_name, reset=False, remote_url=None):

        # print "*****  CouchbaseLiteServerWrapper  ********"

        self.remote_url = remote_url
        self.db_name = db_name
        self.db_url = db_url

        url = "%s/%s" % (db_url, db_name)

        if reset:

            rsp = requests.get(url)

            if rsp.status_code == 200:
                rsp = requests.delete("%s/%s" % (db_url, db_name))
                if rsp.status_code == 401:
                    raise Exception("Error deleting CBLite database: 401 Unauthorized")
                if rsp.status_code == 400:
                    raise Exception("Error deleting CBLite database: 400 Bad Request")


        rsp = requests.get(url)

        if rsp.status_code == 200:

            print "exists", db_name, db_url

        if rsp.status_code == 404:
            rsp = requests.put(url)
            if rsp.status_code == 401:
                raise Exception("Error creating CBLite database: 401 Unauthorized")
            if rsp.status_code == 400:
                raise Exception("Error creating CBLite database: 400 Bad Request")
            if rsp.status_code == 201:
                namespaces.update_cblite_designs(db_name, db_url)
            if not(rsp.status_code == 201 or rsp.status_code == 412):
                raise Exception("Unknown Error creating CBLite database: %s" % rsp.status_code)


    def get(self, key):

        rsp = requests.get("%s/%s/%s" % (self.db_url, self.db_name, key))

        if rsp.status_code == 200:
            return ResultWrapper(rsp.json())

        if rsp.status_code == 404:
            return None

        raise Exception("Unknown Error getting CBLite doc: %s %s" % (rsp.status_code, rsp.text))


    def set(self, key, value, cas=None):

        value["_id"] = key
        if cas:
            value["_rev"] = cas

        rsp = requests.post("%s/%s" % (self.db_url, self.db_name), data=json.dumps(value), headers={"Content-Type": "application/json"})

        if rsp.status_code == 200 or rsp.status_code == 201:
            value["_rev"] = rsp.json()["rev"]
            return ResultWrapper(value)
        else:
            raise Exception("Unknown Error setting CBLite doc: %s %s" % (rsp.status_code, rsp.text))



    def delete(self, key, cas):

        rsp = requests.delete("%s/%s/%s?rev=%s" % (self.db_url, self.db_name, key, cas))
        if rsp.status_code == 200 or rsp.status_code == 202:
            return

        raise Exception("Unknown Error deleting CBLite doc: %s %s" % (rsp.status_code, rsp.text))


    def view(self, name, key):

        design_doc_id, view_name = name.split("/")
        url = "%s/%s/_design/%s/_view/%s" % (self.db_url, self.db_name, design_doc_id, view_name)
        rsp = requests.get(url)

        if rsp.status_code == 200:
            results = rsp.json()
            rows = results["rows"]
            return [(row["id"], row["value"]["_rev"], row["value"]) for row in rows if row["key"] == key]

        raise Exception("Unknown Error view CBLite doc: %s %s" % (rsp.status_code, rsp.text))

    #
    # def query(self, *attr, **kwargs):
    #     return self.db.query(*attr, **kwargs)
    #

    def sync_up(self):
        if self.remote_url is not None:

            attrs = {"create_target": False,
                     "source": self.db_name,
                     "target": self.remote_url}

            rsp = requests.post("%s/_replicate" % self.db_url, data=json.dumps(attrs), headers={"Content-Type": "application/json"})

            if rsp.status_code == 200:
                return

            raise Exception("Unknown Error syncing up CBLite: %s %s" % (rsp.status_code, rsp.text))



    def sync_down(self):
        if self.remote_url is not None:

            attrs = {"create_target": False,
                     "source": self.remote_url,
                     "target": self.db_name}

            rsp = requests.post("%s/_replicate" % self.db_url, data=json.dumps(attrs), headers={"Content-Type": "application/json"})

            if rsp.status_code == 200:
                return

            raise Exception("Unknown Error syncing down CBLite: %s %s" % (rsp.status_code, rsp.text))


    def __getattr__(self, name):
        return self.get(name)



class CouchDBWrapper(object):

    def __init__(self, db_url, db_name, reset=False, remote_url=None):

        self.remote_url = remote_url
        self.db_name = db_name
        self.server = couchdb.Server(db_url)

        if reset:
            try:
                self.server.delete(db_name)
            except couchdb.http.ResourceNotFound:
                pass

        try:
            self.db = self.server[db_name]
        except couchdb.ResourceNotFound:
            self.db = self.server.create(db_name)
            namespaces.update_designs(db_url)

    def get(self, key):
        try:
            return ResultWrapper(self.db[key])
        except couchdb.ResourceNotFound:
            return None
        except TypeError:##why is this happening?
            try:
                return ResultWrapper(self.db[key])
            except TypeError:
                return None
            except couchdb.ResourceNotFound:
                return None


    def set(self, key, value, cas=None):
        if cas:
            value["_rev"] = cas
        self.db[key] = value
        return ResultWrapper(value)

    def delete(self, key, cas):
        return self.db.delete({"_id": key, "_rev": cas})

    def view(self, name, key):
        results = self.db.view(name)
        rows = results[key]
        return [(row.value["_id"], row.value["_rev"], row.value) for row in rows]

    def query(self, *attr, **kwargs):
        return self.db.query(*attr, **kwargs)

    def sync_up(self):
        if self.remote_url is not None:
            try:
                self.server.replicate(self.db_name, self.remote_url)
            except couchdb.ServerError, e:
                print "remote url: ", self.remote_url
                print e
            except Exception, e:
                print "remote url: ", self.remote_url
                print e


    def sync_down(self):
        if self.remote_url is not None:
            self.server.replicate(self.remote_url, self.db_name)

    def __getattr__(self, name):
        return getattr(self.db, name)



class CouchbaseWrapper(object):

    def __init__(self, host, port, db_name, user_name, password, reset=False):

        print "*****  CouchbaseWrapper  ********"

        db_url = "http://%s:%s" % (host, port)

        if reset:
            try:
                couchbase_utils.flush_a_bucket(db_url, user_name, password, db_name)
            except Exception:
                couchbase_utils.make_a_bucket(db_url, user_name, password, db_name, force=True, flush=True)
                time.sleep(2)

        namespaces.update_designs_couchbase(db_name, host)

        self.db = Couchbase.connect(bucket=db_name, host=host)


    def get(self, key):
        try:
            return self.db.get(key)
        except NotFoundError:
            return None


    def set(self, key, value, cas=0):
        return self.db.set(key, value, cas)

    def delete(self, key, cas):
        return self.db.delete(key, cas)

    def view(self, name, key):
        design, view = name.split("/")

        q = Query(
            stale=False,
            inclusive_end=True,
            mapkey_range=[key]
        )

        view = View(self.db, design, view, query=q)
        return [(row.docid, None, row.value) for row in view]


    def query(self, *attr, **kwargs):
        return self.db.query(*attr, **kwargs)

    def __getattr__(self, name):
        return getattr(self.db, name)

    def sync_up(self):
        return



def get_db_connection(db_url, db_name, reset=False, remote_url=None):
    return CouchDBWrapper(db_url, db_name, reset, remote_url)