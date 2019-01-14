import json
import time
import sys
import copy

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
                 namespace=None
                 ):

        self.mapper = mapper
        self.validator = validator
        self.read_only = read_only
        self.api_key = api_key
        self.namespace = namespace

        self.expires = None

        self.data_adapter = FirestoreDataAdapter()

        # Use a service account

        options = {"httpTimeout": 5}

        app = None

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
                print("already initaialised")
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

        value = self.data_adapter.serialise(input_value)
        self._check_uniqueness(key, value)

        if self.read_only:
            raise Exception("This db is read only")

        if self.validator is not None:
            if "namespace" in value and not "schema" in value:
                schema_id = self.validator.schema_id_for(value["namespace"], value["type"])
                # print("schema_id", schema_id)
                if schema_id is not None:
                    value["schema"] = schema_id
            try:
                self.validator.validate(value)
            except jsonschema.ValidationError as e:
                raise FamValidationError(e)

        type = value["type"]
        value["_id"] = key
        sans_metadata = copy.deepcopy(value)

        del sans_metadata["type"]
        del sans_metadata["namespace"]

        self.db.collection(type).document(key).set(sans_metadata)
        return ResultWrapper.from_couchdb_json(value)



    def _work_out_class(self, key, class_name):

        if isinstance(class_name, list):
            for cn in class_name:
                if key.startswith(cn):
                    return cn
            raise Exception("can't work out class name %s %s" % (key, class_name))
        else:
            return class_name


    @refresh_check
    def _get(self, key, class_name):

        single_class_name = self._work_out_class(key, class_name)
        doc_ref = self.db.collection(single_class_name).document(key)

        try:
            snapshot = doc_ref.get()
            if not snapshot.exists:
                return None
            as_json = self.value_from_snapshot(snapshot)
            return ResultWrapper.from_couchdb_json(as_json)
        except NotFound:
            return None


    def value_from_snapshot(self, snapshot):
        as_json = self.data_adapter.deserialise(snapshot.to_dict())
        # as_json["_id"] = snapshot.reference.id
        as_json["type"] = snapshot.reference.parent.id
        as_json["namespace"] = self.namespace
        return as_json


    def _get_refs_from(self, key, type_name, field_name):
        type_ref = self.db.collection(type_name)
        query_ref = type_ref.where(field_name, u'==', key)
        snapshots = query_ref.get()
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
        self._clear_uniqueness_typed(key, type_name)
        self.db.collection(type_name).document(key).delete()


    @refresh_check
    def delete_all(self, type_name):
        coll_ref = self.db.collection(type_name)
        self._delete_collection(coll_ref, 10)

    def _query_items_simple(self, firebase_query):
        snapshots = firebase_query.get()
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
            docs = query.get()
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

        values = self.data_adapter.serialise(input_value)

        self._check_uniqueness_typed(namespace, type_name, key, values)
        doc_ref = self.db.collection(type_name).document(key)
        if self.read_only:
            raise Exception("This db is read only")

        for k, v in values.items():
            if v is None:
                values[k] = firestore.DELETE_FIELD
        doc_ref.update(values)


    def _delete_collection(self, coll_ref, batch_size):
        docs = coll_ref.limit(10).get()
        deleted = 0

        for doc in docs:
            doc.reference.delete()
            deleted = deleted + 1

        if deleted >= batch_size:
            return self._delete_collection(coll_ref, batch_size)


    ##############   unique stuff ##########################


    def _get_unique_ref(self, type_name, key, field_name, field_value):
        unique_type_name = "%s__%s" % (type_name, field_name)
        unique_doc_ref = self.db.collection(unique_type_name).document(field_value)
        try:
            unique_doc = unique_doc_ref.get()
            if unique_doc is None or not unique_doc.exists:
                return unique_doc_ref, unique_type_name, field_name
            ## if it exists then check to see if its owned by another
            if unique_doc.to_dict()["owner"] != key:
                raise FamUniqueError("The value %s for %s is already taken" % (field_value, field_name))
            else:
                # no op in the case where the value is already set
                return None
        except NotFound:
            ## go ahead and set the new one
            return unique_doc_ref, unique_type_name, field_name


    def _check_uniqueness(self, key, value):

        type_name = value["type"]
        namespace = value["namespace"]
        self._check_uniqueness_typed(namespace, type_name, key, value)


    def _clear_uniqueness_typed(self, key, type_name):

        doc_ref = self.db.collection(type_name).document(key)
        doc = doc_ref.get()
        as_dict = doc.to_dict()

        type_name = doc.reference.parent.id

        cls = self.mapper.get_class(type_name, self.namespace)

        for field_name, field_value in as_dict.items():
            if field_name in cls.fields:
                field = cls.fields[field_name]
                if field.unique:
                    unique_type_name = "%s__%s" % (type_name, field_name)
                    unique_doc_ref = self.db.collection(unique_type_name).document(field_value)
                    unique_doc_ref.delete()


    def _check_uniqueness_typed(self, namespace, type_name, key, value):

        cls = self.mapper.get_class(type_name, namespace)

        to_set = []

        # check all the unique objects and fail if any are bad before setting anything
        for field_name, field_value in value.items():
            if field_name in cls.fields:
                field = cls.fields[field_name]
                if field.unique:
                    ref_name_fieldname = self._get_unique_ref(type_name, key, field_name, field_value)
                    if ref_name_fieldname is not None:
                        to_set.append(ref_name_fieldname)

        if len(to_set) > 0:

            try:
                doc_ref = self.db.collection(type_name).document(key)
                doc = doc_ref.get()
                as_dict = doc.to_dict()
            except NotFound:
                as_dict = None

            for unique_doc_ref, unique_type_name, field_name in to_set:

                unique_doc_ref.set({"owner": key, "type_name": type_name})

                if as_dict is not None:
                    existing_key = as_dict.get(field_name)
                    if existing_key is not None:
                        existing_unique_doc_ref = self.db.collection(unique_type_name).document(existing_key)
                        existing_unique_doc_ref.delete()




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
                unique_doc_ref.set({"owner": key, "type_name": type_name})

        # delete any existing
        try:
            doc = doc_ref.get()
            as_dict = doc.to_dict()
            existing_key = as_dict.get(field_name)
            if existing_key is not None:
                existing_unique_doc_ref = self.db.collection(unique_type_name).document(existing_key)
                existing_unique_doc_ref.delete()
        except NotFound:
            # this is fine it just means there is no suxh doc yet
            pass


    def get_unique_instance(self, namespace, type_name, field_name, value):
        unique_type_name = "%s__%s" % (type_name, field_name)
        unique_doc_ref = self.db.collection(unique_type_name).document(value)
        try:
            doc = unique_doc_ref.get()
            as_dict = doc.to_dict()
            wrapper = self._get(as_dict["owner"], as_dict["type_name"])
            return GenericObject._from_doc(self, wrapper.key, wrapper.rev, wrapper.value)

        except NotFound:
            return None