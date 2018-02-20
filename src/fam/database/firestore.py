import json
import time

import requests
from requests.exceptions import HTTPError

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import jsonschema

from google.cloud.exceptions import NotFound

from fam.exceptions import *
from fam.constants import *
from fam.database.base import BaseDatabase
from fam.database.couchdb import ResultWrapper

from grpc._channel import _Rendezvous

from fam.blud import GenericObject

from .custom_token import CustomToken


"""

get(key, class_name)
update(key, class_name, **kwargs)
delete(item)


"""

def refresh_check(func):
    def func_wrapper(instance, *args, **kwargs):
        now = time.time()
        if instance.expires is not None and instance.expires < now + 10:
            instance.refresh()
        try:
            return func(instance, *args, **kwargs)
        except _Rendezvous as e:
            if instance.expires is not None:
                instance.refresh()
            return func(instance, *args, **kwargs)
    return func_wrapper


def raise_detailed_error(request_object):
    try:
        request_object.raise_for_status()
    except HTTPError as e:
        # raise detailed error message
        # TODO: Check if we get a { "error" : "Permission denied." } and handle automatically
        raise HTTPError(e, request_object.text)


class FirestoreWrapper(BaseDatabase):

    def query_view(self, view_name, **kwargs):
        raise NotImplementedError

    def changes(self, since=None, channels=None, limit=None, feed=None, timeout=None, filter=None):
        raise NotImplementedError

    database_type = "firestore"

    def __init__(self,
                 mapper,
                 creds_path,
                 project_id=None,
                 custom_token=None,
                 api_key=None,
                 validator=None,
                 read_only=False
                 ):

        self.mapper = mapper
        self.validator = validator
        self.read_only = read_only
        self.api_key = api_key

        self.expires = None

        # Use a service account

        if creds_path is None:
            self.user = self.sign_in_with_custom_token(custom_token)
            self.update_expires()
            self.creds = CustomToken(self.user["idToken"], project_id)
            firebase_admin.initialize_app(self.creds)
        else:
            try:
                self.creds = credentials.Certificate(creds_path)
                firebase_admin.initialize_app(self.creds)
            except ValueError as e:
                print("already initaialised")

        self.db = firestore.client()


    def update_expires(self):
        self.expires = time.time() + int(self.user["expiresIn"])


    def sign_in_with_custom_token(self, token):
        request_ref = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyCustomToken?key={0}".format(self.api_key)
        headers = {"content-type": "application/json; charset=UTF-8"}
        data = json.dumps({"returnSecureToken": True, "token": token})
        request_object = requests.post(request_ref, headers=headers, data=data)
        raise_detailed_error(request_object)
        return request_object.json()


    def refresh(self):

        refresh_token = self.user["refreshToken"]
        request_ref = "https://securetoken.googleapis.com/v1/token?key={0}".format(self.api_key)
        headers = {"content-type": "application/json; charset=UTF-8"}
        data = json.dumps({"grantType": "refresh_token", "refreshToken": refresh_token})
        request_object = requests.post(request_ref, headers=headers, data=data)
        raise_detailed_error(request_object)
        request_object_json = request_object.json()

        self.user = {
            "userId": request_object_json["user_id"],
            "idToken": request_object_json["id_token"],
            "refreshToken": request_object_json["refresh_token"],
            "expiresIn": request_object_json["expires_in"]
        }

        oauth_creds = self.creds.get_credential()
        oauth_creds.token = request_object_json["id_token"]


    @refresh_check
    def _set(self, key, value, rev=None):

        if self.read_only:
            raise Exception("This db is read only")

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

        self.db.collection(value["type"]).document(key).set(value)
        return ResultWrapper.from_couchdb_json(value)


    @refresh_check
    def _get(self, key, class_name):
        doc_ref = self.db.collection(class_name).document(key)
        try:
            doc = doc_ref.get()
            return ResultWrapper.from_couchdb_json(doc.to_dict())
        except NotFound:
            return None


    def _get_refs_from(self, key, type_name, field_name):
        type_ref = self.db.collection(type_name)
        query_ref = type_ref.where(field_name, u'==', key)
        docs = query_ref.get()
        rows = [ResultWrapper.from_couchdb_json(doc.to_dict()) for doc in docs]
        objs = [GenericObject._from_doc(self, row.key, row.rev, row.value) for row in rows]
        return objs


    @refresh_check
    def get_all_type(self, namespace, type_name):
        all_sub_class_names = self.mapper.get_all_subclass_names(namespace, type_name)

        objs = []
        for type_name in all_sub_class_names:
            objs += self.get_single_type(namespace, type_name)
        return objs


    @refresh_check
    def get_single_type(self, namespace, type_name):
        type_ref = self.db.collection(type_name)
        docs = type_ref.get()
        rows = [ResultWrapper.from_couchdb_json(doc.to_dict()) for doc in docs]
        objs = [GenericObject._from_doc(self, row.key, row.rev, row.value) for row in rows]
        return objs


    @refresh_check
    def get_refs_from(self, namespace, type_name, name, key, field):
        all_sub_class_names = self.mapper.get_all_subclass_names(namespace, field.refcls)
        objs = []
        for class_name in all_sub_class_names:
            objs += self._get_refs_from(key, class_name, field.fkey)
        return objs


    @refresh_check
    def get_with_value(self, namespace, type_name, field_name, value):
        return self._get_refs_from(value, type_name, field_name)


    @refresh_check
    def _delete(self, key, rev, type_name):

        if self.read_only:
            raise Exception("This db is read only")
        self.db.collection(type_name).document(key).delete()


    @refresh_check
    def delete_all(self, type_name):
        coll_ref = self.db.collection(type_name)
        self._delete_collection(coll_ref, 10)


    def set_unique_doc(self, type_name, key, field_name, value):

        doc_ref = self.db.collection(type_name).document(key)

        unique_type_name = "%s__%s" % (type_name, field_name)
        if value is not None:
            unique_doc_ref = self.db.collection(unique_type_name).document(value)
            try:
                unique_doc = unique_doc_ref.get()
                ## if it exists then check to see if its owned by another
                if unique_doc.to_dict()["owner"] != key:
                    raise FamUniqueError("The value %s for %s is already taken" % (value, field_name))
                else:
                    # no op in the case where the value is already set
                    return
            except NotFound:
                unique_doc_ref.set({"owner": key})

        # delete any existing
        doc = doc_ref.get()
        as_dict = doc.to_dict()
        existing_key = as_dict.get(field_name)
        if existing_key is not None:
            existing_unique_doc_ref = self.db.collection(unique_type_name).document(existing_key)
            existing_unique_doc_ref.delete()


    def query_snapshots(self, firebase_query, batch_size=100):
        return self.query_snapshots_iterator(firebase_query, batch_size=batch_size)

    def query_snapshots_iterator(self, firebase_query, batch_size):

        skip = 0
        query = firebase_query.order_by(u'_id').limit(batch_size)

        while True:
            docs = query.get()
            docs_list = list(docs)
            if len(docs_list) == 0:
                break
            for doc_snapshot in docs_list:
                yield doc_snapshot
            last_doc = docs_list[-1]
            last_id = last_doc.to_dict()["_id"]
            query = firebase_query.order_by(u'_id').start_after({
                u'_id': last_id
            }).limit(batch_size)

    @refresh_check
    def update(self, type_name, key, field_name, value, field):
        print(type_name, key, field_name, value, field)

        doc_ref = self.db.collection(type_name).document(key)

        if field.unique:
            self.set_unique_doc(type_name, key, field_name, value)

        value = firestore.DELETE_FIELD if value is None else value
        doc_ref.update({field_name: value})


    def _delete_collection(self, coll_ref, batch_size):
        docs = coll_ref.limit(10).get()
        deleted = 0

        for doc in docs:
            doc.reference.delete()
            deleted = deleted + 1

        if deleted >= batch_size:
            return self._delete_collection(coll_ref, batch_size)