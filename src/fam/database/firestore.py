import json
import time
import sys
import copy
import os

import requests
from requests.exceptions import HTTPError

import firebase_admin
from firebase_admin import credentials, firestore, auth
from google.cloud.firestore import transactional
from google.api_core.exceptions import PermissionDenied

from fam.exceptions import *
from fam.constants import *
from fam.database.base import BaseDatabase
from fam.database.couchdb import ResultWrapper
from fam.database.firestore_adapter import FirestoreDataAdapter

from grpc._channel import _Rendezvous

from fam.blud import GenericObject

from .custom_token import CustomToken

if sys.version_info[0] < 3:
    PYTHON_VERSION = 2
else:
    PYTHON_VERSION = 3


"""

get(key, class_name)
update(key, class_name, **kwargs)
delete(item)


"""

def catch_permission(func):
    def func_wrapper(instance, *args, **kwargs):
        try:
            return func(instance, *args, **kwargs)
        except PermissionDenied as e:
            raise FamPermissionError("You don't have permission access this resource: %s origional error: %s" % (args, e))
    return func_wrapper


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
    check_on_save = False

    def __init__(self,
                 mapper,
                 creds_path,
                 project_id=None,
                 custom_token=None,
                 api_key=None,
                 validator=None,
                 read_only=False,
                 name=None,
                 namespace=None,
                 default_options = {}
                 ):

        self.mapper = mapper
        self.validator = validator

        ##give it a reverse ref
        if validator is not None:
            self.validator.db = self

        self.read_only = read_only
        self.api_key = api_key
        self.namespace = namespace
        self.expires = None
        self.data_adapter = FirestoreDataAdapter()

        # Use a service account
        options = copy.deepcopy(default_options)
        options["httpTimeout"] = 5

        app = None
        self.user = None
        self.expires = None
        self.creds = None

        if custom_token is not None:
            # from device client
            self.user = self.sign_in_with_custom_token(custom_token)
            self.update_expires()
            self.creds = CustomToken(self.user["idToken"], project_id)

            app_name = name if name else firebase_admin._DEFAULT_APP_NAME

            try:
                app = firebase_admin.get_app(name=app_name)
            except ValueError as e:
                # ugly hack to account for different behaviour of google libs
                try:
                    app = firebase_admin.initialize_app(self.creds, name=app_name, options=options)
                except Exception as e:
                    self.creds = self.creds.get_credential()
                    app = firebase_admin.initialize_app(self.creds, name=app_name, options=options)


        elif creds_path is not None:
            # in dev with service creds
            try:
                self.creds = credentials.Certificate(creds_path)
                app = firebase_admin.initialize_app(self.creds, options=options)
            except ValueError as e:
                pass
                # print("already initaialised")
        else:
            # in app engine environment
            already_initialised = firebase_admin._DEFAULT_APP_NAME in firebase_admin._apps
            if not already_initialised:
                app = firebase_admin.initialize_app(options=options)

        self.db = firestore.client(app=app)
        self.app = app


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


    def set_object(self, obj, rev=None):
        return self._set(obj.key, obj._properties)


    @refresh_check
    def _set(self, key, input_value, rev=None):

        if self.read_only:
            raise Exception("This db is read only")

        value = self.data_adapter.serialise(input_value)

        type_name = value["type"]
        namespace = value["namespace"]

        if self.validator is not None:
            if "namespace" in value and not "schema" in value:
                schema_id = self.validator.schema_id_for(namespace, type_name)
                # print("schema_id", schema_id)
                if schema_id is not None:
                    value["schema"] = schema_id
            # try:
            #     self.validator.validate(value)
            # except jsonschema.ValidationError as e:
            #     raise FamValidationError(e)

        value["_id"] = key
        sans_metadata = copy.deepcopy(value)
        del sans_metadata["type"]
        del sans_metadata["namespace"]

        unique_field_names = self._check_for_unique_fields(namespace, type_name, value)

        if unique_field_names:
            transaction = self.db.transaction()
            set_with_unique_fields(transaction, self.db, type_name, key, sans_metadata, unique_field_names)
        else:
            doc_ref = self.db.collection(type_name).document(key)
            self._set_ref(doc_ref, sans_metadata)

        return ResultWrapper.from_couchdb_json(value)


    #############################################
    # these are here to isolate certain calls to firestore library so that contexts can override them easily
    ############################################

    @catch_permission
    def _stream_ref(self, doc_ref):
        return self._stream_doc_ref(doc_ref)

    def _stream_doc_ref(self, doc_ref):
        return doc_ref.stream()

    @catch_permission
    def _get_ref(self, doc_ref):
        return self._get_doc_ref(doc_ref)

    def _get_doc_ref(self, doc_ref):
        return doc_ref.get()

    @catch_permission
    def _set_ref(self, doc_ref, value):
        self._set_doc_ref(doc_ref, value)

    def _set_doc_ref(self, doc_ref, value):
        doc_ref.set(value)

    @catch_permission
    def _update_ref(self, doc_ref, value):
        doc_ref.update(value)

    def _update_doc_ref(self, doc_ref, value):
        doc_ref.update(value)

    ############################################

    def _work_out_class(self, key, class_name):
        if key.startswith(class_name):
            return class_name
        subclasses = self.mapper.get_all_subclass_names(self.namespace, class_name)
        for cn in subclasses:
            if key.startswith(cn):
                return cn
        raise Exception("can't work out class name %s %s" % (key, class_name))


    @refresh_check
    def _get(self, key, class_name):

        single_class_name = self._work_out_class(key, class_name)
        doc_ref = self.db.collection(single_class_name).document(key)
        snapshot = self._get_ref(doc_ref)
        if not snapshot.exists:
            return None
        as_json = self.value_from_snapshot(snapshot)
        return ResultWrapper.from_couchdb_json(as_json)


    def value_from_snapshot(self, snapshot):
        as_json = self.data_adapter.deserialise(snapshot.to_dict())
        # as_json["_id"] = snapshot.reference.id
        as_json["type"] = snapshot.reference.parent.id
        as_json["namespace"] = self.namespace
        return as_json


    def _get_refs_from(self, key, type_name, field_name):
        type_ref = self.db.collection(type_name)
        query_ref = type_ref.where(field_name, u'==', key)
        snapshots = self._stream_ref(query_ref)
        rows = [ResultWrapper.from_couchdb_json(self.value_from_snapshot(snapshot)) for snapshot in snapshots]
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
        snapshots = self._stream_ref(type_ref)
        rows = [ResultWrapper.from_couchdb_json(self.value_from_snapshot(snapshot)) for snapshot in snapshots]
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

        doc_ref = self.db.collection(type_name).document(key)

        try:
            doc = doc_ref.get()
        except PermissionDenied as e:
            raise FamPermissionError("You don't have permission access this resource: %s" % doc_ref)

        as_dict = doc.to_dict()

        unique_field_names = self._check_for_unique_fields(self.namespace, type_name, as_dict)

        if unique_field_names:
            unique_values = {k : as_dict[k] for k in unique_field_names}
            transaction = self.db.transaction()
            delete_with_unique_values(transaction, self.db, type_name, key, unique_values)
        else:
            doc_ref.delete()


    @refresh_check
    def delete_all(self, type_name):
        coll_ref = self.db.collection(type_name)
        self._delete_collection(coll_ref, 10)

    def _query_items_simple(self, firebase_query):
        snapshots = self._stream_ref(firebase_query)
        results = []
        for snapshot in snapshots:
            wrapper = ResultWrapper.from_couchdb_json(self.value_from_snapshot(snapshot))
            results.append(GenericObject.from_row(self, wrapper))
        return results


    def query_items(self, firebase_query, batch_size=None, order_by=u'_id'):
        if batch_size is not None:
            return self.query_items_iterator(firebase_query, batch_size=batch_size, order_by=order_by)
        else:
            return self._query_items_simple(firebase_query)


    def query_snapshots(self, firebase_query, batch_size=100):
        return self.query_snapshots_iterator(firebase_query, batch_size=batch_size)


    def query_items_iterator(self, firebase_query, batch_size, order_by=u'_id'):

        for snapshot in self.query_snapshots_iterator(firebase_query, batch_size=batch_size, order_by=order_by):
            wrapper = ResultWrapper.from_couchdb_json(self.value_from_snapshot(snapshot))
            obj = GenericObject.from_row(self, wrapper)
            yield obj


    def query_snapshots_iterator(self, firebase_query, batch_size, order_by=u'_id'):

        skip = 0
        query = firebase_query.order_by(order_by).limit(batch_size)

        while True:
            docs = self._stream_ref(query)
            docs_list = list(docs)
            if len(docs_list) == 0:
                break
            for doc_snapshot in docs_list:
                yield doc_snapshot
            last_doc = docs_list[-1]
            last_value = last_doc.to_dict()[order_by]
            query = firebase_query.order_by(order_by).start_after({
                order_by: last_value
            }).limit(batch_size)


    @refresh_check
    def update(self, namespace, type_name, key, input_value):

        if self.read_only:
            raise Exception("This db is read only")

        values = self.data_adapter.serialise(input_value)
        unique_field_names = self._check_for_unique_fields(namespace, type_name, values)

        if unique_field_names:
            transaction = self.db.transaction()
            update_with_unique_fields(transaction, self.db, type_name, key, values, unique_field_names)
        else:
            doc_ref = self.db.collection(type_name).document(key)
            self._update_ref(doc_ref, values)


    def _delete_collection(self, coll_ref, batch_size):
        docs = self._stream_ref(coll_ref.limit(10))
        deleted = 0

        for doc in docs:
            doc.reference.delete()
            deleted = deleted + 1

        if deleted >= batch_size:
            return self._delete_collection(coll_ref, batch_size)


    ##############   unique stuff ##########################

    def _check_for_unique_fields(self, namespace, type_name, value):

        cls = self.mapper.get_class(type_name, namespace)
        unique_field_names = []

        for field_name, field_value in value.items():
            if field_name in cls.fields:
                field = cls.fields[field_name]
                if field.unique:
                    unique_field_names.append(field_name)

        return unique_field_names


    def get_unique_instance(self, namespace, type_name, field_name, value):
        unique_type_name = "%s__%s" % (type_name, field_name)
        unique_doc_ref = self.db.collection(unique_type_name).document(value)

        doc = self._get_ref(unique_doc_ref)

        if doc.exists:
            as_dict = doc.to_dict()
            wrapper = self._get(as_dict["owner"], as_dict["type_name"])
            return GenericObject._from_doc(self, wrapper.key, wrapper.rev, wrapper.value)
        else:
            return None


##########  transactional unique functions


@transactional
def set_with_unique_fields(transaction, client, type_name, key, values, unique_field_names):
    _create_unique_field_docs(client, type_name, key, values, unique_field_names, transaction)
    doc_ref = client.collection(type_name).document(key)
    try:
        transaction.set(doc_ref, values)
    except PermissionDenied as e:
        raise FamPermissionError("You don't have permission access this resource: %s" % key)


@transactional
def update_with_unique_fields(transaction, client, type_name, key, values, unique_field_names):
    _create_unique_field_docs(client, type_name, key, values, unique_field_names, transaction)
    doc_ref = client.collection(type_name).document(key)
    try:
        transaction.update(doc_ref, values)
    except PermissionDenied as e:
        raise FamPermissionError("You don't have permission access this resource: %s" % key)

@transactional
def delete_with_unique_values(transaction, client, type_name, key, unique_values):
    _clear_unique_docs(client, type_name, unique_values, transaction)
    doc_ref = client.collection(type_name).document(key)
    transaction.delete(doc_ref)


def _create_unique_field_docs(client, type_name, key, value, unique_field_names, transaction):

    to_set = []

    # check all the unique objects and fail if any are bad before setting anything
    for field_name in unique_field_names:
        field_value = value[field_name]
        ref_name_fieldname = _get_unique_ref(client, type_name, key, field_name, field_value, transaction)
        if ref_name_fieldname is not None:
            to_set.append(ref_name_fieldname)

    if len(to_set) > 0:
        doc_ref = client.collection(type_name).document(key)
        try:
            doc = doc_ref.get(transaction=transaction)
        except PermissionDenied as e:
            raise FamPermissionError("You don't have permission access this resource: %s" % key)

        as_dict = doc.to_dict() if doc.exists else None
        for unique_doc_ref, unique_type_name, field_name in to_set:
            try:
                transaction.set(unique_doc_ref, {"owner": key, "type_name": type_name})
            except PermissionDenied as e:
                raise FamPermissionError("You don't have permission access this resource: %s" % unique_doc_ref)
            if as_dict is not None:
                existing_key = as_dict.get(field_name)
                if existing_key is not None:
                    existing_unique_doc_ref = client.collection(unique_type_name).document(
                        existing_key)
                    try:
                        transaction.delete(existing_unique_doc_ref)
                    except PermissionDenied as e:
                        raise FamPermissionError("You don't have permission access this resource: %s" % existing_unique_doc_ref)


def _get_unique_ref(client, type_name, key, field_name, field_value, transaction):
    unique_type_name = "%s__%s" % (type_name, field_name)
    unique_doc_ref = client.collection(unique_type_name).document(field_value)
    try:
        unique_doc = unique_doc_ref.get(transaction=transaction)
    except PermissionDenied as e:
        raise FamPermissionError("You don't have permission access this resource: %s" % unique_doc_ref)
    if unique_doc.exists:
        ## if it exists then check to see if its owned by another
        if unique_doc.to_dict()["owner"] != key:
            raise FamUniqueError("The value %s for %s is already taken" % (field_value, field_name))
        else:
            # no op in the case where the value is already set
            return None
    else:
        ## go ahead and set the new one
        return unique_doc_ref, unique_type_name, field_name


def _clear_unique_docs(client, type_name, unique_values, transaction):

    for field_name, field_value in unique_values.items():
        unique_type_name = "%s__%s" % (type_name, field_name)
        unique_doc_ref = client.collection(unique_type_name).document(field_value)
        try:
            transaction.delete(unique_doc_ref)
        except PermissionDenied as e:
            raise FamPermissionError("You don't have permission access this resource: %s" % unique_doc_ref)

