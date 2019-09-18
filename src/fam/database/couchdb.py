import simplejson as json
import copy


from fam.fam_json import object_default
import jsonschema
from copy import deepcopy

from fam.exceptions import *
from fam.constants import *
from fam.utils import requests_shim as requests
from fam.database.base import BaseDatabase, FamDbAuthException

from fam.utils.backoff import http_backoff
from .couchdb_adapter import CouchDBDataAdapter


JSON_KEY_STRINGS = ["endkey", "end_key", "key", "keys", "startkey", "start_key"]


class ResultWrapper(object):

    def __init__(self, key, rev, value):
        self.key = key
        self.rev = rev
        self.value = value


    @classmethod
    def from_couchdb_json(cls, as_json):
        key = as_json["_id"]
        rev = as_json.get("_rev")
        if rev is not None:
            rev = rev
            del as_json["_rev"]
        else:
            rev = None
        del as_json["_id"]
        value = as_json

        # if rev is None:
        #     print "****************************"
        #     print as_json
        #     print "****************************"
        # else:
        #     if rev[1:2] != "-":
        #         print "****************************"
        #         print rev
        #         print as_json
        #         print "****************************"

        return cls(key, rev, value)


    @classmethod
    def from_couchdb_view_json(cls, as_json):
        key = as_json["id"]
        rev = as_json["doc"]["_rev"]
        value = deepcopy(as_json["doc"])
        del value["_id"]
        del value["_rev"]
        return cls(key, rev, value)


    @classmethod
    def from_gateway_view_json(cls, as_json):
        # the format of this seems to be changing quite a bit
        try:
            key = as_json["id"]
            value = deepcopy(as_json["value"])
            sync = value.get("_sync")
            if sync is not None:
                rev = sync["rev"]
                del value["_sync"]
            elif value.get("_rev"):
                rev = as_json["value"]["_rev"]
                del value["_rev"]
            else:
                rev = None
        except KeyError as e:
            print("key error raised in from_gateway_view_json on object: %s" % json.dumps(as_json, indent=4))
            raise e

        # if rev[1:2] != "-":
        #     print "how is this rev wrong!: ", rev
        #     print as_json


        return cls(key, rev, value)


def auth(func):
    def func_wrapper(instance, *args, **kwargs):
        try:
            return func(instance, *args, **kwargs)
        except FamDbAuthException:
            instance.authenticate()
            return func(instance, *args, **kwargs)
    return func_wrapper


def ensure_views(func):
    def func_wrapper(db, *args, **kwargs):
        try:
            return func(db, *args, **kwargs)
        except FamViewError:
            db.update_designs()
            return func(db, *args, **kwargs)
    return func_wrapper


class CouchDBWrapper(BaseDatabase):

    VIEW_URL = "%s/%s/_design/%s/_view/%s"
    # "%s/%s/_design/%s/_view/%s?stale=false&key=\"%s\""

    database_type = "couchdb"
    supports_skip = True
    check_on_save = True

    def __init__(self, mapper,
                 db_url,
                 db_name,
                 reset=False,
                 remote_url=None,
                 continuous=False,
                 validator=None,
                 read_only=False
                 ):

        self.mapper = mapper
        self.validator = validator
        self.read_only = read_only

        self.cookies = {}

        self.remote_url = remote_url
        self.db_name = db_name
        self.db_url = db_url
        self.session = requests.Session()
        self.data_adapter = CouchDBDataAdapter()

        url = "%s/%s" % (db_url, db_name)

        replicator_url = "{}/_config/replicator/db".format(self.db_url)
        self.replicator_db = self.session.get(replicator_url).json()

        if reset:
            self.replicator_db = self.clear_all_replications()
            rsp = self.session.get(url)
            if rsp.status_code == 200:
                rsp = self.session.delete("%s/%s" % (db_url, db_name))
                if rsp.status_code == 401:
                    raise Exception("Error deleting CB database: 401 Unauthorized")
                if rsp.status_code == 400:
                    raise Exception("Error deleting CB database: 400 Bad Request")

        rsp = self.session.get(url)
        if rsp.status_code == 200:
            print("exists", db_name, db_url)

        if rsp.status_code == 404:
            rsp = self.session.put(url)
            if rsp.status_code == 401:
                raise Exception("Error creating CB database: 401 Unauthorized")
            if rsp.status_code == 400:
                raise Exception("Error creating CB database: 400 Bad Request")
            if not(rsp.status_code == 201 or rsp.status_code == 412):
                raise Exception("Unknown Error creating cb database: %s" % rsp.status_code)

            #if this is a new database then set the replications running
            self.continuous = continuous
            if continuous:
                self.sync_both_continuous()



    def info(self):

        url = "%s/%s" % (self.db_url, self.db_name)
        rsp = self.session.get(url)

        if rsp.status_code == 200:
            return rsp.json()

        return None


    def get_design(self, key):
        return self._get(key)

    def ensure_role(self, role_name):
        pass

    def ensure_user_role(self, username, role):
        pass

    @auth
    def _get(self, key, class_name=None):
        url = "%s/%s/%s" % (self.db_url, self.db_name, key)
        # print "_get: ", url
        rsp = self.session.get(url)
        if rsp.status_code == 200:
            return ResultWrapper.from_couchdb_json(self.data_adapter.deserialise(rsp.json()))
        if rsp.status_code == 404:
            # print "not found: ", key
            return None
        if rsp.status_code == 401:
            raise FamDbAuthException(" %s %s" % (rsp.status_code, rsp.text))
        raise Exception("Unknown Error getting cb doc: %s %s" % (rsp.status_code, rsp.text))


    def get_refs_from(self, namespace, type_name, name, key, field):
        view_namespace = namespace.replace("/", "_")
        view_name = "%s/%s_%s" % (view_namespace, type_name, name)
        return self.query_view(view_name, key=key)


    def get_with_value(self, namespace, type_name, field_name, value):
        view_namespace = namespace.replace("/", "_")
        view_name = "%s/%s_%s" % (view_namespace, type_name, field_name)
        return self.query_view(view_name, key=value)

    def get_all_type(self, namespace, type_name):
        return self.query_view("raw/all", key=type_name)


    def set_object(self, obj, rev=None):

        return self._set(obj.key, obj._properties, rev=rev)


    @http_backoff
    def _set(self, key, input_value, rev=None, backoff=False):

        value = self.data_adapter.serialise(input_value)

        if self.read_only:
            raise Exception("This db is read only")

        if "type" in value:
            self._check_uniqueness(key, value)

        if self.validator is not None:
            if "namespace" in value and not "schema" in value:
                schema_id = self.validator.schema_id_for(value["namespace"], value["type"])
                if schema_id is not None:
                    value["schema"] = schema_id
            try:
                self.validator.validate(value)
            except jsonschema.ValidationError as e:
                raise FamValidationError(e)


        value["_id"] = key
        if rev:
            value["_rev"] = rev

        url = "%s/%s/%s" % (self.db_url, self.db_name, key)

        rsp = self.session.put(url, data=json.dumps(value,
                                                    indent=4,
                                                    sort_keys=True,
                                                    default=object_default),
                               headers={"Content-Type": "application/json", "Accept": "application/json"})

        if rsp.status_code == 200 or rsp.status_code == 201:
            if rsp.content:
                value["_rev"] = rsp.json()["rev"]

            return ResultWrapper.from_couchdb_json(self.data_adapter.deserialise(value))
        else:
            raise FamResourceConflict("Unknown Error setting CBLite doc: %s %s" % (rsp.status_code, rsp.text))


    def _delete(self, key, rev, classname):

        if self.read_only:
            raise Exception("This db is read only")

        rsp = self.session.delete("%s/%s/%s?rev=%s" % (self.db_url, self.db_name, key, rev))
        if rsp.status_code == 200 or rsp.status_code == 202:
            return
        raise FamResourceConflict("Unknown Error deleting cb doc: %s %s" % (rsp.status_code, rsp.text))


    def _wrapper_from_view_json(self, as_json):
        return ResultWrapper.from_couchdb_view_json(self.data_adapter.deserialise(as_json))


    def _encode_for_view_query(self, kwargs):
        encoded = {}
        for k, v in kwargs.items():
            encoded[k] = json.dumps(v) if k in JSON_KEY_STRINGS else v
        return encoded


    # @ensure_views
    def view(self, name, raw=False, **kwargs):
        design_doc_id, view_name = name.split("/")

        kwargs["include_docs"] = "true"

        url = self.VIEW_URL % (self.db_url, self.db_name, design_doc_id, view_name)
        rsp = self.session.get(url, params=self._encode_for_view_query(kwargs))

        if rsp.status_code == 200:
            results = rsp.json()
            if raw:
                return results
            rows = results["rows"]
            return [self._wrapper_from_view_json(row) for row in rows]

        raise FamViewError("Unknown Error view cb doc: %s %s %s" % (rsp.status_code, rsp.text, url))


    def authenticate(self):
        pass


    @auth
    def _changes(self, since=None, channels=None, limit=1000, feed=None, timeout=None, filter=None):
        url = "%s/%s/_changes" % (self.db_url, self.db_name)
        params = {"include_docs":"true"}
        if since is not None:
            params["since"] = json.dumps(since)
        if filter is not None and channels is not None:
            raise Exception("you can't specify both filter and channels")
        if filter is not None:
            params["filter"] = filter
        if channels is not None:
            params["filter"] = "sync_gateway/bychannel"
            params["channels"] = ",".join(channels)
        if limit is not None:
            params["limit"] = limit
        if feed is not None:
            params["feed"] = feed
            if feed in ("longpoll", "continuous"):
                if timeout is None:
                    params["timeout"] = 60000
                else:
                    params["timeout"] = timeout
        rsp = self.session.get(url, params=params, cookies=self.cookies)
        # rsp = self.session.get(url, cookies=self.cookies)
        if rsp.status_code == 200:
            results = rsp.json()
            last_seq = results.get("last_seq")
            rows = results.get("results")
            return last_seq, [ResultWrapper.from_couchdb_json(self.data_adapter.deserialise(row["doc"])) for row in rows if "doc" in row.keys() and row["doc"].get(TYPE_STR) is not None]
        if rsp.status_code == 404:
            return None, None
        if rsp.status_code == 403:
            raise FamDbAuthException()
        raise Exception("Unknown Error getting CB doc: %s %s" % (rsp.status_code, rsp.text))


    def clear_all_replications(self):
        return

        url = "{}/_config/replicator/db".format(self.db_url)
        old_replicator_db = self.session.get(url).json()
        new_replicator_db = "replicator_a" if old_replicator_db != "replicator_a" else "replicator_b"
        rsp = self.session.put("{}/{}".format(self.db_url, new_replicator_db))

        if rsp.status_code == 201 or rsp.status_code == 412:
            #set the new db
            self.session.put(url, data=json.dumps(new_replicator_db))
            #delete the old one
            if old_replicator_db != "_replicator":
                rsp = self.session.delete("%s/%s" % (self.db_url, old_replicator_db))
            return new_replicator_db
        else:
           raise Exception("failed to create new replication db")


    def sync_both_continuous(self):

        self.create_sync_up_continuous(self.replicator_db)
        self.create_sync_down_continuous(self.replicator_db)


    def create_sync_down_continuous(self, replicator_db):

        if self.remote_url is None:
            raise Exception("can't sync up nowhere")

        attrs = {"create_target": False,
                 "source": self.remote_url,
                 "target": self.db_name,
                 "continuous": True,
                 "_id": "flotsam_sync_down"
                 }

        headers = {"Content-Type": "application/json"}

        rsp = self.session.post("%s/%s" % (self.db_url, replicator_db), data=json.dumps(attrs), headers=headers)
        if rsp.status_code < 300:
            print("sync down created")
            return

        raise Exception("Error creating sync down: %s %s" % (rsp.status_code, rsp.text))



    def create_sync_up_continuous(self, replicator_db):

        if self.remote_url is None:
            raise Exception("can't sync up nowhere")

        attrs = {"create_target": False,
                 "source": self.db_name,
                 "target": self.remote_url,
                 "continuous": True,
                 "_id": "flotsam_sync_up"
                 }

        headers = {"Content-Type": "application/json"}

        rsp = self.session.post("%s/%s" % (self.db_url, replicator_db), data=json.dumps(attrs), headers=headers)
        if rsp.status_code < 300:
            print("sync_up created")
            return
        raise Exception("Error creating sync up to remote: %s %s" % (rsp.status_code, rsp.text))



    def sync_up(self):

        if self.remote_url is not None:
            attrs = {"create_target": False,
                     "source": self.db_name,
                     "target": self.remote_url}

            headers = {"Content-Type": "application/json"}

            rsp = self.session.post("%s/_replicate" % self.db_url, data=json.dumps(attrs), headers=headers)
            if rsp.status_code < 300:
                return
            raise Exception("Unknown Error syncing up to remote: %s %s" % (rsp.status_code, rsp.text))


    def sync_down(self, continuous=False):

        if self.remote_url is not None:

            attrs = {"create_target": False,
                     "source": self.remote_url,
                     "target": self.db_name}

            headers = {"Content-Type": "application/json"}

            rsp = self.session.post("%s/_replicate" % self.db_url, data=json.dumps(attrs), headers=headers)
            if rsp.status_code < 300:
                return
            raise Exception("Unknown Error syncing up to remote: %s %s" % (rsp.status_code, rsp.text))


    def flush(self):

        rsp = self.session.post("%s/%s/_ensure_full_commit" % (self.db_url, self.db_name))
        if rsp.status_code <= 201:
                return
        raise Exception("Unknown Error _ensure_full_commit in remote: %s %s" % (rsp.status_code, rsp.text))


    def ensure_design_doc(self, key, doc):
        if self.read_only:
            raise Exception("This db is read only")

        # first put it into dev
        dev_key = key.replace("_design/", "_design/dev_")
        dev_doc = copy.deepcopy(doc)
        dev_doc["_id"] = dev_key

        previous_dev = self._get(dev_key)

        # print "self.db_url: ", self.db_url, self.db_name

        self._set(dev_key, dev_doc, rev=None if previous_dev is None else previous_dev.rev)

        # then get it back again to compare
        existing = self._get(key)
        existing_dev = self._get(dev_key)

        if existing == existing_dev:
            pass
            # print("************  designs up to date ************")
        else:
            # print("************  updating designs ************")
            # print("new_design: ", doc)
            self._set(key, doc, rev=None if existing is None else existing.rev)



    def _raw_design_doc(self):

        design_doc = {
            "views": {
                "all": {
                    "map": "function(doc) {emit(doc.type, null);}"
                }
            }
        }

        return design_doc


    def update_designs(self):

        ## simple type index
        doc = self._raw_design_doc()
        key = "_design/raw"

        doc["_id"] = key

        self.ensure_design_doc(key, doc)


        ## relational indexes
        for namespace_name, namespace in self.mapper.namespaces.items():

            view_namespace = namespace_name.replace("/", "_")
            key = "_design/%s" % view_namespace

            doc = self.mapper.get_design(namespace, namespace_name, self.FOREIGN_KEY_MAP_STRING)
            doc["_id"] = key
            self.ensure_design_doc(key, doc)

        ## extra indexes
        for doc in self.mapper.extra_design_docs():
            key = doc["_id"]
            self.ensure_design_doc(key, doc)


    def get_unique_instance(self, namespace, type_name, field_name, value):

        view_namespace = namespace.replace("/", "_")
        view_name = "%s/%s_%s" % (view_namespace, type_name, field_name)
        all_existing = self.query_view(view_name, key=value)
        all_non_null = [o for o in all_existing if getattr(o, field_name, None)]
        how_many_existing = len(all_non_null)

        if how_many_existing > 1:
            raise FamUniqueError("more than {} with a {} of value {}".format(type_name, field_name, value))
        elif how_many_existing == 1:
            return all_non_null[0]
        else:
            return None


    def _check_uniqueness(self, key, value):


        type_name = value["type"]
        namespace = value["namespace"]

        cls = self.mapper.get_class(type_name, namespace)

        for field_name in value:
            if field_name in cls.fields:
                field = cls.fields[field_name]
                if field.unique:
                    this_value = value.get(field_name)
                    if this_value is None:
                        continue

                    type_name = cls._type_with_ref(field_name)
                    existing = self.get_unique_instance(namespace, type_name, field_name, this_value)

                    if existing and existing.key != key:
                        raise FamUniqueError("more than {} with a {} of value {}".format(type_name, field_name, this_value))