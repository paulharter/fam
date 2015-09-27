import json
import uuid
import datetime
import types
import sys

from .constants import *
from .exceptions import *

__all__ = [
    "BoolField",
    "NumberField",
    "StringField",
    "ListField",
    "DictField",
    "ReferenceTo",
    "ReferenceFrom",
    "GenericObject"
]

class Field(object):
    
    object = "base"
    
    def __init__(self, required=False, immutable=False):
        self.required = required
        self.immutable = immutable


    def is_correct_type(self, value):
        return True

    
    def __str__(self):
        attr = []
        if self.required:
            attr.append(FIELD_REQUIRED)
        return " ".join(attr)

    as_string = property(__str__)


class BoolField(Field):

    def is_correct_type(self, value):
        return type(value) == types.BooleanType or type(value) == types.NoneType

class NumberField(Field):

    def is_correct_type(self, value):
        return type(value) == types.IntType or type(value) == types.LongType or type(value) == types.FloatType or type(value) == types.NoneType

class StringField(Field):

    def is_correct_type(self, value):
        return type(value) == types.StringType or type(value) == types.UnicodeType or type(value) == types.NoneType

class ListField(Field):

    def is_correct_type(self, value):
        return type(value) == types.ListType or type(value) == types.NoneType

class DictField(Field):

    def is_correct_type(self, value):
        return type(value) == types.DictType or type(value) == types.NoneType


class ReferenceTo(Field):

    def __init__(self, refns, refcls, required=False, immutable=False, delete="nothing"):
        self.refns = refns
        self.refcls = refcls
        self.delete = delete
        super(ReferenceTo, self).__init__(required, immutable)

    def is_correct_type(self, value):
        return type(value) == types.StringType or type(value) == types.UnicodeType or type(value) == types.NoneType

    def __str__(self):
        attr = []

        attr.append("ns:%s"  % self.refns)
        attr.append("resource:%s"  % self.refcls)

        if self.required:
            attr.append(FIELD_REQUIRED)
        return " ".join(attr)

    as_string = property(__str__)

class ReferenceFrom(Field):

    def __init__(self, refns, refcls, fkey, required=False, immutable=False, delete="nothing"):
        self.refns = refns
        self.refcls = refcls
        self.fkey = fkey
        self.delete = delete
        super(ReferenceFrom, self).__init__(required, immutable)

    def __str__(self):
        attr = []
        attr.append("ns:%s"  % self.refns)
        attr.append("resource:%s"  % self.refcls)
        attr.append("key:%s"  % self.fkey)
        if self.required:
            attr.append(FIELD_REQUIRED)
        return " ".join(attr)

    as_string = property(__str__)

def current_xml_time():
    now = datetime.datetime.utcnow()
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")


## this provides a class based wrapper

class GenericMetaclass(type):

    def __new__(cls, name, bases, dct):
        attrs = dct.copy()
        if attrs.get("fields") is None:
            attrs["fields"] = {}
        for b in bases:
            if hasattr(b, "fields"):
                attrs["fields"].update(b.fields)

        #check that the names of all ref to fields end with _id
        for fieldname, field in attrs["fields"].iteritems():
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


class GenericObject(object):
    use_rev = True
    additional_properties = False
    __metaclass__ = GenericMetaclass
    fields = {}

    def __init__(self, key=None, rev=None, **kwargs):

        type_name = self.__class__.__name__.lower()
        namespace = self.__class__.namespace.lower()

        self.key = key if key is not None else u"%s_%s" % (type_name, unicode(uuid.uuid4()))
        if rev is not None:
            self.rev = rev

        self._properties = {}

        for k, v in kwargs.iteritems():
            setattr(self, k, v)

        self._db = None

        if kwargs.get(TYPE_STR) is None:
            self._properties[TYPE_STR] = type_name

        #TODO fix this for super classes ???
        # else:
        #     if self._properties[TYPE_STR] != type_name:
        #         raise Exception("dont match %s %s" % (self._properties[TYPE_STR], type_name))

        if kwargs.get(NAMESPACE_STR) is None:
            self._properties[NAMESPACE_STR] = namespace
        else:
            if self._properties[NAMESPACE_STR] != namespace:
                raise Exception("the given namespace doesn't match the class")

    @classmethod
    def all(cls, db):
        return cls._query_view(db, "raw/all", cls.type)

    @classmethod
    def changes(cls, db, since=None, channels=None, limit=None, feed="normal"):
        last_seq, rows  =  db.changes(since=since, channels=channels, limit=limit, feed=feed)
        objects = [GenericObject._from_doc(db, row.key, row.rev, row.value) for row in rows]
        return last_seq, objects

    def _get_namespace(self):
        return self._properties.get(NAMESPACE_STR)

    def _get_type(self):
        return self._properties.get(TYPE_STR)

    def _get_properties(self):
        prop = self._properties.copy()
        del prop[TYPE_STR]
        del prop[NAMESPACE_STR]
        return prop

    def save(self, db):
        self._db = db
        result = db.get(self.key)
        if result:
            doc = result.value
            rev = result.rev
            if self.rev:# if it has a revision
                if rev != self.rev:
                    raise FamResourceConflict("bad rev id: %s, rev: %s db_rev: %s" % (self.key, self.rev, rev))
            else:
                if not self.use_rev:
                    self.rev = rev
                else:
                    raise FamResourceConflict("bad rev id: %s, rev: %s db_rev: %s" % (self.key, self.rev, rev))
            self.pre_save_update_cb(doc)
            if self.use_rev and self.rev:
                result = db._set(self.key, self._properties, rev=self.rev)
                self.rev = result.rev
            else:
                result = db._set(self.key, self._properties, rev=self.rev)
                self.rev = result.rev
            self.post_save_update_cb()
            db.sync_up()
            return "updated"
        else:
            self.pre_save_new_cb()
            result = db._set(self.key, self._properties)
            self.post_save_new_cb()
            db.sync_up()

        if self.use_rev:
            self.rev = result.rev
        return "new"


    def delete(self, db):
        self.pre_delete_cb()
        db._delete(self.key, self.rev)
        self.post_delete_cb()
        self.delete_references(db)
        db.sync_up()


    @classmethod
    def delete_key(cls, db, key):
        obj = cls.get(db, key)
        obj.delete(db)


    def delete_references(self, db):
        for field_name, field in self.__class__.fields.iteritems():
            if isinstance(field, ReferenceTo):
                if field.delete == "cascade":
                    if field_name.endswith("_id"):
                        obj = getattr(self, field_name[:-3])
                        if obj is not None:
                            obj.delete(db)
                    else:
                        raise Exception("should have _id")
            if isinstance(field, ReferenceFrom):

                view_namespace = self.namespace.replace("/", "_")
                view_name = "%s/%s_%s" % (view_namespace, self.type, field_name)
                objs = self._query_view(self._db, view_name, self.key)

                if field.delete == "cascade":
                    for obj in objs:
                        obj.delete(db)
                else:
                    for obj in objs:
                        del obj._properties[field.fkey]
                        obj.save(db)


    def as_json(self):
        d = {}
        d.update(self.properties)
        d[NAMESPACE_STR] = self.namespace
        d[TYPE_STR] = self.type
        d["_id"] = self.key
        if self.rev is not None:
            d["_rev"] = self.rev
        return json.dumps(d, sort_keys=True, indent=4, separators=(',', ': '))


    def __eq__(self, other):
        equal = True

        if self.key != other.key:
            equal = False

        if self.use_rev and self.rev != other.rev:
            equal = False

        if self.type != other.type:
            equal = False

        for k in other.properties.keys():
            if other._properties[k] != self._properties[k]:
                equal = False
        return equal


    @classmethod
    def get(cls, db, key):
        result = db._get(key)
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
            raise Exception("couldn't find class %s" % doc.get(TYPE_STR))

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

    def pre_save_new_cb(self):
        pass
    
    def post_save_new_cb(self):
        pass

    def pre_save_update_cb(self, old_properties):
        pass

    def post_save_update_cb(self):
        pass

    def pre_delete_cb(self):
        pass

    def post_delete_cb(self):
        pass

    @classmethod
    def _query_view(cls, db, view_name, key):
        rows =  db.view(view_name, key)
        return [GenericObject._from_doc(db, row.key, row.rev, row.value) for row in rows]

    def __getattr__(self, name):
        ref = self.__class__.fields.get(name)
        if isinstance(ref, ReferenceFrom):
            if self._db is None:
                raise Exception("no db")
            view_namespace = self.namespace.replace("/", "_")
            view_name = "%s/%s_%s" % (view_namespace, self.type, name)
            return self._query_view(self._db, view_name, self.key)

        if "%s_id" % name in self.properties.keys():
            id_name = "%s_id" % name
            ref = self.__class__.fields.get(id_name)
            if isinstance(ref, ReferenceTo):
                if self._db is None:
                    raise Exception("no db")
                return GenericObject.get(self._db, self._properties[id_name])
        if name in self._properties.keys():
            return self._properties[name]


    def _update_property(self, key, value):
        if value is None:
            if key in self._properties:
                del self._properties[key]
        else:
            self._properties[key] = value


    def __setattr__(self, name, value):

        if name in RESERVED_PROPERTY_NAMES:
            self.__dict__[name] = value
            return

        alias = "%s_id" % name
        if alias in self.fields.keys():
            self._update_property(alias, value.key)

        elif name in self.fields or name in ("type", "namespace") or self.additional_properties :
            field = self.fields.get(name)
            if field is not None:
                if field.immutable and name in self._properties:
                    raise FamValidationError("You cannot change the immutable property %s" % name)
            self._update_property(name, value)
        else:
            raise FamValidationError("""You cant use the property name %s on the class %s
            If you would like to set additional properties on this class that are not specified
            set the class attribute "additional_properties" to True.
            """ % (name, self.__class__.__name__))


    namespace = property(_get_namespace)
    type = property(_get_type)
    properties = property(_get_properties)
