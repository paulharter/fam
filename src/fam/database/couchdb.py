import json
from copy import deepcopy
import fam.namespaces as namespaces
from fam.utils import requests_shim as requests


class ResultWrapper(object):

    def __init__(self, key, cas, value):
        self.key = key
        self.cas = cas
        self.value = value

    @classmethod
    def from_couchdb_json(cls, as_json):
        key = as_json["_id"]
        rev = as_json.get("_rev")
        if rev is not None:
            cas = rev
            del as_json["_rev"]
        else:
            cas = None
        del as_json["_id"]
        value = as_json
        return cls(key, cas, value)

    @classmethod
    def from_couchdb_view_json(cls, as_json):
        key = as_json["id"]
        cas = as_json["value"]["_rev"]
        value = deepcopy(as_json["value"])
        del value["_id"]
        del value["_rev"]
        return cls(key, cas, value)

    @classmethod
    def from_gateway_view_json(cls, as_json):
        key = as_json["id"]
        cas = as_json["value"]["_sync"]["rev"]
        value = deepcopy(as_json["value"])
        del value["_sync"]
        return cls(key, cas, value)


class CouchDBWrapper(object):

    VIEW_URL = "%s/%s/_design/%s/_view/%s?key=\"%s\""

    def __init__(self, db_url, db_name, reset=False, remote_url=None):
        self.remote_url = remote_url
        self.db_name = db_name
        self.db_url = db_url

        url = "%s/%s" % (db_url, db_name)

        if reset:
            rsp = requests.get(url)
            if rsp.status_code == 200:
                rsp = requests.delete("%s/%s" % (db_url, db_name))
                if rsp.status_code == 401:
                    raise Exception("Error deleting CB database: 401 Unauthorized")
                if rsp.status_code == 400:
                    raise Exception("Error deleting CB database: 400 Bad Request")

        rsp = requests.get(url)
        if rsp.status_code == 200:
            print "exists", db_name, db_url

        if rsp.status_code == 404:
            rsp = requests.put(url)
            if rsp.status_code == 401:
                raise Exception("Error creating CB database: 401 Unauthorized")
            if rsp.status_code == 400:
                raise Exception("Error creating CB database: 400 Bad Request")
            if rsp.status_code == 201:
                namespaces.update_designs_in_db(self)
            if not(rsp.status_code == 201 or rsp.status_code == 412):
                raise Exception("Unknown Error creating cb database: %s" % rsp.status_code)


    def get(self, key):

        rsp = requests.get("%s/%s/%s" % (self.db_url, self.db_name, key))
        if rsp.status_code == 200:
            return ResultWrapper.from_couchdb_json(rsp.json())
        if rsp.status_code == 404:
            return None
        raise Exception("Unknown Error getting cb doc: %s %s" % (rsp.status_code, rsp.text))


    def set(self, key, value, cas=None):

        value["_id"] = key
        if cas:
            value["_rev"] = cas

        url = "%s/%s/%s" % (self.db_url, self.db_name, key)
        rsp = requests.put(url, data=json.dumps(value), headers={"Content-Type": "application/json", "Accept": "application/json"})
        if rsp.status_code == 200 or rsp.status_code == 201:
            if rsp.content:
                value["_rev"] = rsp.json()["rev"]
            return ResultWrapper.from_couchdb_json(value)
        else:
            raise Exception("Unknown Error setting CBLite doc: %s %s" % (rsp.status_code, rsp.text))


    def delete(self, key, cas):
        rsp = requests.delete("%s/%s/%s?rev=%s" % (self.db_url, self.db_name, key, cas))
        if rsp.status_code == 200 or rsp.status_code == 202:
            return
        raise Exception("Unknown Error deleting cb doc: %s %s" % (rsp.status_code, rsp.text))


    def _wrapper_from_view_json(self, as_json):
        return ResultWrapper.from_couchdb_view_json(as_json)


    def view(self, name, key):

        design_doc_id, view_name = name.split("/")
        url = self.VIEW_URL % (self.db_url, self.db_name, design_doc_id, view_name, key)
        rsp = requests.get(url)

        if rsp.status_code == 200:
            results = rsp.json()
            rows = results["rows"]
            return [self._wrapper_from_view_json(row) for row in rows]

        raise Exception("Unknown Error view cb doc: %s %s %s" % (rsp.status_code, rsp.text, url))


    def changes(self, since=None, channels=None, limit=None):

        url = "%s/%s/_changes" % (self.db_url, self.db_name)
        params = {"include_docs":"true"}
        if since is not None:
            params["since"] = since
        if channels is not None:
            params["filter"] = "sync_gateway/bychannel"
            params["channels"] = ",".join(channels)
        if limit is not None:
            params["limit"] = limit
        rsp = requests.get(url, params=params)
        if rsp.status_code == 200:
            results = rsp.json()
            last_seq = results.get("last_seq")
            rows = results.get("results")
            return last_seq, [ResultWrapper.from_couchdb_json(row["doc"]) for row in rows if row["doc"].get("type") is not None]
        if rsp.status_code == 404:
            return None, None

        raise Exception("Unknown Error getting CB doc: %s %s" % (rsp.status_code, rsp.text))


    def sync_up(self):
        if self.remote_url is not None:
            attrs = {"create_target": False,
                     "source": self.db_name,
                     "target": self.remote_url}

            headers = {"Content-Type": "application/json",
                       }

            rsp = requests.post("%s/_replicate" % self.db_url, data=json.dumps(attrs), headers=headers)
            if rsp.status_code == 200:
                return
            raise Exception("Unknown Error syncing up CBLite: %s %s" % (rsp.status_code, rsp.text))



    def sync_down(self):
        if self.remote_url is not None:
            attrs = {"create_target": False,
                     "source": self.remote_url,
                     "target": self.db_name}

            rsp = requests.post("%s/_replicate" % self.db_name, data=json.dumps(attrs), headers={"Content-Type": "application/json"})
            if rsp.status_code == 200:
                return
            raise Exception("Unknown Error syncing down CBLite: %s %s" % (rsp.status_code, rsp.text))

    def __getattr__(self, name):
        return self.get(name)


