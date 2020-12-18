import simplejson as json
import traceback
import uuid
import datetime
import types
import sys
import six
from copy import deepcopy

from fam.fam_json import object_default

from .constants import *
from .exceptions import *
from .fields import *

__all__ = [
    "BoolField",
    "NumberField",
    "StringField",
    "ListField",
    "DictField",
    "ObjectField",
    "LatLongField",
    "DateTimeField",
    "BytesField",
    "DecimalField",
    "FractionField",
    "ReferenceTo",
    "ReferenceFrom",
    "EmailField",
    "GenericObject",
    "FamObject"
]

class NotSet():
    pass

# NOT_SET = NotSet()

def current_xml_time():
    now = datetime.datetime.utcnow()
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")


## this provides a class based wrapper


class GenericMetaclass(type):

    def __new__(cls, name, bases, dct):
        attrs = dct.copy()
        # take a copy of this classes own fields
        attrs["cls_fields"] = {} if attrs["fields"] is None else attrs["fields"].copy()

        if attrs.get("fields") is None:
            attrs["fields"] = {}
        for b in bases:
            if hasattr(b, "fields"):
                attrs["fields"].update(b.fields)

        #check that the names of all ref to fields end with _id
        for fieldname, field in attrs["fields"].items():
            if isinstance(field, ReferenceTo) and not fieldname.endswith("_id"):
                raise FamError("All ReferenceTo field names must end with _id, %s doesn't" % fieldname)

        attrs[TYPE_STR] = name.lower()
        newcls = super(GenericMetaclass, cls).__new__(cls, name, bases, attrs)
        module = sys.modules[newcls.__module__]
        if hasattr(module, "NAMESPACE"):
            attrs[NAMESPACE_STR] = module.NAMESPACE
        else:
            attrs[NAMESPACE_STR] = "genericbase"
        newcls = super(GenericMetaclass, cls).__new__(cls, name, bases, attrs)
        return newcls


# class FamObject(object, metaclass=GenericMetaclass):
class FamObject(six.with_metaclass(GenericMetaclass)):
    use_rev = True
    additional_properties = False
    grants_access = False
    # extra sync gateway keywords that are used by sync function
    sg_allow_public_write = False

    # __metaclass__ = GenericMetaclass

    fields = {}
    acl = None

    def __init__(self, key=None, rev=None, **kwargs):

        type_name = self.__class__.__name__.lower()

        namespace = self.__class__.namespace.lower()

        self.key = key if key is not None else u"%s_%s" % (type_name, str(uuid.uuid4()))
        if rev is not None:
            self.rev = rev

        self._properties = {}

        for k, v in kwargs.items():
            if not k.startswith("_"):
                setattr(self, k, v)

        self._db = None

        if kwargs.get(TYPE_STR) is None:
            self._properties[TYPE_STR] = type_name

        self._check_defaults()

        if kwargs.get(NAMESPACE_STR) is None:
            self._properties[NAMESPACE_STR] = namespace
        else:
            if self._properties[NAMESPACE_STR] != namespace:
                raise Exception("the given namespace doesn't match the class")

    @classmethod
    def all(cls, db):
        return db.get_all_type(cls.namespace, cls.type)


    def _get_namespace(self):
        return self._properties.get(NAMESPACE_STR)

    def _get_type(self):
        return self._properties.get(TYPE_STR)

    def _get_properties(self):
        prop = self._properties.copy()
        del prop[TYPE_STR]
        del prop[NAMESPACE_STR]
        return prop


    def _check_defaults(self):
        for field_name, field in self.__class__.fields.items():
            if field.default is not None and not field_name in self._properties:
                self._properties[field_name] = field.get_default()

    def _check_immutable(self, existing):
        for field_name, field in self.__class__.fields.items():
            if field.immutable:
                attr = getattr(existing, field_name)
                if attr is not None and getattr(self, field_name) != attr:
                    raise FamImmutableError("You can't change the value of {} on a {} it has been made immutable: {}".format(field_name, self.__class__.__name__, getattr(existing, field_name)))





    @classmethod
    def get_unique_instance(cls, db, field_name, value):

        field = cls.fields.get(field_name)
        if field is None:
            return None

        if not field.unique:
            return None

        type_name = cls._type_with_ref(field_name)
        return db.get_unique_instance(cls.namespace, type_name, field_name, value)


    @classmethod
    def create(cls, db, key=None, **kwargs):
        obj = cls(key=key, **kwargs)
        obj._pre_save_new_cb(db)
        created = db.set_object(obj)
        if obj.use_rev and hasattr(created, "rev") and created.rev is not None:
            obj.rev = created.rev
        obj._post_save_new_cb(db)
        obj._db = db
        return obj


    def save_without_checks(self, db):
        self._pre_save_new_cb(db)
        created = db.set_object(self)
        if self.use_rev and hasattr(created, "rev") and created.rev is not None:
            self.rev = created.rev
        self._post_save_new_cb(db)
        self._db = db


    def save(self, db):

        if db.check_on_save:
            return self.save_with_checks(db)
        else:
            return self.save_without_checks(db)


    def save_with_checks(self, db):

        self._db = db

        existing = FamObject.get(db, self.key, class_name=self.type)

        if existing:
            # doc = result.value
            rev = existing.rev

            self._check_immutable(existing)

            # raise a conflict if revs different
            if self.use_rev and rev != self.rev:
                if not self.resolve_write_conflict(existing, rev):
                    raise FamResourceConflict("bad rev id: %s, rev: %s db_rev: %s" % (self.key, self.rev, rev))

            self._pre_save_update_cb(db, existing._properties)
            # just force the rev if not using it
            result = db.set_object(self, rev=self.rev if self.use_rev else rev)

            if self.use_rev and hasattr(result, "rev"):
                self.rev = result.rev

            self._post_save_update_cb(db)
            updated = True
        else:
            self._pre_save_new_cb(db)
            result = db.set_object(self)
            self._post_save_new_cb(db)
            updated = False

        if self.use_rev and hasattr(result, "rev"):
            self.rev = result.rev

        return updated


    def resolve_write_conflict(self, existing_doc, existing_rev):
        return False


    def delete(self, db):
        self._pre_delete_cb(db)
        db._delete(self.key, self.rev, self.type)
        self._post_delete_cb(db)
        self.delete_references(db)
        # db.sync_up()


    @classmethod
    def delete_key(cls, db, key):
        obj = cls.get(db, key)
        obj.delete(db)



    def delete_references(self, db):
        fields_set = list(self.__class__.fields.items())
        for field_name, field in fields_set:
            if isinstance(field, ReferenceTo):
                if field.cascade_delete:
                    if field_name.endswith("_id"):
                        obj = getattr(self, field_name[:-3])
                        if obj is not None:
                            obj.delete(db)
                    else:
                        raise Exception("should have _id")

            if isinstance(field, ReferenceFrom):
                type_name = self.__class__._type_with_ref(field_name)
                objs = self._db.get_refs_from(self.namespace, type_name, field_name, self.key, field)

                if field.cascade_delete:
                    for obj in objs:
                        obj.delete(db)
                else:
                    for obj in objs:
                        del obj._properties[field.fkey]
                        obj.save(db)

    def __str__(self):
        return self.as_json()


    def as_dict(self):
        d = {}
        d.update(self.properties)
        d[NAMESPACE_STR] = self.namespace
        d[TYPE_STR] = self.type
        d["_id"] = self.key
        if self.rev is not None:
            d["_rev"] = self.rev
        return d

    def as_json(self):
        d = {}
        d.update(self.properties)
        d[NAMESPACE_STR] = self.namespace
        d[TYPE_STR] = self.type
        d["_id"] = self.key
        if self.rev is not None:
            d["_rev"] = self.rev
        return json.dumps(d, sort_keys=True, indent=4, default=object_default, separators=(',', ': '))


    def __eq__(self, other):

        if self.key != other.key:
            return False

        if self.use_rev and self.rev != other.rev:
            return False

        if self.type != other.type:
            return False

        keys = set(other.properties.keys()).intersection(set(self.properties.keys()))

        for k in keys:
            if k != "schema" and k != "channels":
                if other._properties[k] != self._properties[k]:
                    return False
        return True


    @classmethod
    def get(cls, db, key, class_name=None):
        # ugly thing to get around cache double dispatch
        cn = class_name if class_name is not None else cls.__name__.lower()
        if not hasattr(db, "_get"):
            #this will call back here but using the correct db
            return db.get(key, class_name=cn)

        result = db._get(key, class_name=cn)
        if result is None:
            return None
        doc = result.value
        rev = result.rev
        return cls._from_doc(db, key, rev, doc)


    @classmethod
    def _from_doc(cls, db, key, rev, doc):

        if "_id" in doc.keys():
            del doc["_id"]

        if "_rev" in doc.keys():
            del doc["_rev"]

        correctCls = db.class_for_type_name(doc.get(TYPE_STR), doc.get(NAMESPACE_STR))
        if correctCls is None:
            raise Exception("couldn't find class {} for doc {}".format(doc.get(TYPE_STR), json.dumps(doc, indent=4)))

        obj = correctCls(key=key, rev=rev, **doc)
        obj._db = db
        return obj


    @classmethod
    def from_json(cls, db, as_json):
        key = as_json["key"]
        rev = as_json.get("rev")
        doc = as_json["properties"].copy()
        doc[NAMESPACE_STR] = as_json[NAMESPACE_STR]
        doc[TYPE_STR] = as_json[TYPE_STR]

        return cls._from_doc(db, key, rev, doc)


    def _pre_save_new_cb(self, db):
        if hasattr(self, "pre_save_new_cb"):
            self.pre_save_new_cb(db)
    
    def _post_save_new_cb(self, db):
        if hasattr(self, "post_save_new_cb"):
            self.post_save_new_cb(db)

    def _changes_cb(self, db, queue, new=False, **kwargs):
        if hasattr(self, "changes_cb"):
            self.changes_cb(db, queue, new=new, **kwargs)

    def _pre_save_update_cb(self, db, old_properties):
        if hasattr(self, "pre_save_update_cb"):
            self.pre_save_update_cb(db, old_properties)

    def _post_save_update_cb(self, db):
        if hasattr(self, "post_save_update_cb"):
            self.post_save_update_cb(db)

    def _pre_delete_cb(self, db):
        if hasattr(self, "pre_delete_cb"):
            self.pre_delete_cb(db)

    def _post_delete_cb(self, db):
        if hasattr(self, "post_delete_cb"):
            self.post_delete_cb(db)


    @classmethod
    def n1ql(cls, db, query, with_revs=False, *args, **kwargs):
        if with_revs:
            rows = db._n1ql_with_rev(query, *args, **kwargs)
        else:
            rows = db._n1ql(query, *args, **kwargs)
        return [GenericObject._from_doc(db, row.key, None, row.value) for row in rows]



    @classmethod
    def view(cls, db, view_name, **kwargs):
        if db.database_type in ["sync_gateway", "null"]:
            rows = db.view(view_name, **kwargs)
            return [GenericObject._from_doc(db, row.key, row.rev, row.value) for row in rows]
        else:
            return cls.view_iterator(db, view_name, **kwargs)


    @classmethod
    def view_iterator(cls, db, view_name, **kwargs):

        if "limit" in kwargs:
            rows = db.view(view_name, **kwargs)
            for row in rows:
                yield GenericObject._from_doc(db, row.key, row.rev, row.value)
        else:

            limit = 100
            skip = 0

            while True:
                rows =  db.view(view_name, limit=limit, skip=skip, **kwargs)
                if len(rows) == 0:
                    break
                skip += limit
                for row in rows:
                    yield GenericObject._from_doc(db, row.key, row.rev, row.value)



    @classmethod
    def changes(cls, db, **kwargs):
        last_seq, rows = db._changes(**kwargs)

        changeset = []

        for row in rows:
            try:
                changeset.append(GenericObject._from_doc(db, row.key, row.rev, row.value))
            except Exception as e:
                print("BAD!!! swallowing all exceptions in blud changes")


        return last_seq, changeset
        # return last_seq, [GenericObject._from_doc(db, row.key, row.rev, row.value) for row in rows]

    @classmethod
    def _query_view(cls, db, view_name, key):
        rows =  db.view(view_name, key=key)
        return [GenericObject._from_doc(db, row.key, row.rev, row.value) for row in rows]


    @classmethod
    def from_row(cls, db, row):
        return GenericObject._from_doc(db, row.key, row.rev, row.value)


    @classmethod
    def _type_with_ref(cls, name):

        if name in cls.cls_fields.keys():
            return cls.type

        for base in cls.__bases__:
            found = base._type_with_ref(name)
            if found:
                return found

        return None



    def __getattr__(self, name):
        field = self.__class__.fields.get(name)
        if isinstance(field, ReferenceFrom):
            if self._db is None:
                traceback.print_stack()
                raise Exception("no db")
            # look at super class gypes to find clas with ref
            type_name = self.__class__._type_with_ref(name)
            return self._db.get_refs_from(self.namespace, type_name, name, self.key, field)


        if "%s_id" % name in self.properties.keys():
            id_name = "%s_id" % name
            ref = self.__class__.fields.get(id_name)
            if isinstance(ref, ReferenceTo):
                if self._db is None:
                    traceback.print_stack()
                    raise Exception("no db")
                # return GenericObject.get(self._db, self._properties[id_name])
                return self._db.get(self._properties[id_name], class_name=ref.refcls)

        if name in self._properties.keys():
            # print("found in properties", name)
            # if it is a subclass of stringfield for string formats
            # if isinstance(field, StringField) and not field.__class__ == StringField:
            #     if hasattr(field, "from_json"):
            #         return field.from_json(self._properties[name])
            return self._properties[name]


        if name in self.__class__.fields:
            return None
        elif "%s_id" % name in self.__class__.fields:
            return None
        elif name == "rev":
            return None
        else:
            # print("self: ", self, name)
            raise AttributeError("Not found %s" % name)


    def update(self, values, db=None):

        if db is not None:
            use_db = db
        elif "_db" in self.__dict__:
            use_db = self._db
        else:
            return

        if hasattr(use_db, "update"):
            use_db.update(self.namespace, self.type, self.key, values)
            for k, v in values.items():
                setattr(self, k, v)
        else:
            for k, v in values.items():
                setattr(self, k, v)
            self.save(use_db)

    def _update_property(self, key, value, field):

        self._properties[key] = value


    def __setattr__(self, name, value):

        if name in RESERVED_PROPERTY_NAMES:
            self.__dict__[name] = value
            return

        field = self.fields.get(name)

        alias = "%s_id" % name
        if alias in self.fields.keys():
            self._update_property(alias, value.key, field)

        elif name in self.fields or name in ("type", "namespace", "schema", "update_seconds", "update_nanos") or self.additional_properties :
            if field is not None:
                if field.immutable and name in self._properties:
                    raise FamImmutableError("You cannot change the immutable property %s" % name)
                if isinstance(field, ObjectField) and not isinstance(value, field.cls):
                    if hasattr(field.cls, "from_json"):
                        value = field.cls.from_json(value)
                    else:
                        value = field.from_json(value)

                if isinstance(field, ListField) and field.item_cls is not None:
                    #cast the items in the list into a certain class
                    value = [field.item_cls.from_json(i) for i in value]

                # if issubclass(field.__class__, StringField) and not (isinstance(value, str) or value is None):
                #     value = field.to_json(value)

            self._update_property(name, value, field)
        elif name.startswith("_"):
            self.__dict__[name] = value
            return
        else:
            raise FamValidationError("""You cant use the property name %s on the class %s
            If you would like to set additional properties on this class that are not specified
            set the class attribute "additional_properties" to True.
            """ % (name, self.__class__.__name__))


    namespace = property(_get_namespace)
    type = property(_get_type)
    properties = property(_get_properties)


GenericObject = FamObject
