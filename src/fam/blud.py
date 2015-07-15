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
    
    def __init__(self, unique=False, optional=False):
        self.unique = unique
        self.optional = optional


    def is_correct_type(self, value):
        return True

    
    def __str__(self):
        attr = []
        if self.optional:attr.append(FIELD_OPTIONAL)
        if self.unique:attr.append(FIELD_UNIQUE)
        return " ".join(attr)

    as_string = property(__str__)


class BoolField(Field):

    # typename = "Bool"

    def is_correct_type(self, value):
        return type(value) == types.BooleanType or type(value) == types.NoneType

class NumberField(Field):

    # typename = "Number"

    def is_correct_type(self, value):
        return type(value) == types.IntType or type(value) == types.LongType or type(value) == types.FloatType or type(value) == types.NoneType

class StringField(Field):

    # typename = "String"

    def is_correct_type(self, value):
        return type(value) == types.StringType or type(value) == types.UnicodeType or type(value) == types.NoneType

class ListField(Field):

    # typename = "List"

    def is_correct_type(self, value):
        return type(value) == types.ListType or type(value) == types.NoneType

class DictField(Field):

    # typename = "Object"

    def is_correct_type(self, value):
        return type(value) == types.DictType or type(value) == types.NoneType


class ReferenceTo(Field):

    # typename = "Reference To"

    def __init__(self, refns, refcls, unique=False, optional=False, delete="nothing"):
        self.refns = refns
        self.refcls = refcls
        self.delete = delete
        super(ReferenceTo, self).__init__(unique, optional)

    def is_correct_type(self, value):
        return type(value) == types.StringType or type(value) == types.UnicodeType or type(value) == types.NoneType


    def __str__(self):
        attr = []

        attr.append("ns:%s"  % self.refns)
        attr.append("resource:%s"  % self.refcls)

        if self.optional:attr.append(FIELD_OPTIONAL)
        if self.unique:attr.append(FIELD_UNIQUE)
        if self.detail:attr.append("detail")
        return " ".join(attr)

    as_string = property(__str__)

class ReferenceFrom(Field):

    # typename = "Reference From"

    def __init__(self, refns, refcls, fkey, unique=False, delete="nothing"):
        self.refns = refns
        self.refcls = refcls
        self.fkey = fkey
        self.delete = delete
        super(ReferenceFrom, self).__init__(unique, True)


    def __str__(self):
        attr = []
        attr.append("ns:%s"  % self.refns)
        attr.append("resource:%s"  % self.refcls)
        attr.append("key:%s"  % self.fkey)
        if self.optional:attr.append(FIELD_OPTIONAL)
        if self.unique:attr.append(FIELD_UNIQUE)
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
        attrs["type"] = name.lower()
        newcls = super(GenericMetaclass, cls).__new__(cls, name, bases, attrs)
        module = sys.modules[newcls.__module__]
        if hasattr(module, "NAMESPACE"):
            attrs[NAMESPACE_STR] = module.NAMESPACE
        else:
            attrs[NAMESPACE_STR] = "genericbase"
        newcls = super(GenericMetaclass, cls).__new__(cls, name, bases, attrs)
        return newcls


class GenericObject(object):
    use_cas = False
    __metaclass__ = GenericMetaclass
    fields = {}
    # views = {}


    def __init__(self, key=None, cas=None, **kwargs):

        type_name = self.__class__.__name__.lower()
        namespace = self.__class__.namespace.lower()

        self.key = key if key is not None else u"%s_%s" % (type_name, unicode(uuid.uuid4()))
        if cas is not None:
            self.cas = cas
        self._properties = kwargs
        self._db = None



        if kwargs.get("type") is None:
            self._properties["type"] = type_name

        #TODO fix this for super classes
        # else:
        #     if self._properties["type"] != type_name:
        #         raise Exception("dont match %s %s" % (self._properties["type"], type_name))

        if kwargs.get(NAMESPACE_STR) is None:
            self._properties[NAMESPACE_STR] = namespace
        else:
            if self._properties[NAMESPACE_STR] != namespace:
                raise

    @classmethod
    def all(cls, db):
        return cls._query_view(db, "raw/all", cls.type)

    @classmethod
    def changes(cls, db, since=None, channels=None, limit=None, feed="normal"):
        last_seq, rows  =  db.changes(since=since, channels=channels, limit=limit, feed=feed)
        objects = [GenericObject._from_doc(db, row.key, row.cas, row.value) for row in rows]
        return last_seq, objects

    def _get_namespace(self):
        return self._properties.get(NAMESPACE_STR)

    def _get_type(self):
        return self._properties.get("type")

    def _get_properties(self):
        prop = self._properties.copy()
        del prop["type"]
        del prop[NAMESPACE_STR]
        return prop


    def save(self, db):
        self._db = db
        result = db.get(self.key)
        if result:
            doc = result.value
            cas = result.cas
            if self.cas:# if it has a revision
                if cas != self.cas:
                    raise FamResourceConflict("bad rev id: %s, cas: %s db_cas: %s" % (self.key, self.cas, cas))
            else:
                if not self.use_cas:
                    self.cas = cas
                else:
                    raise FamResourceConflict("bad rev id: %s, cas: %s db_cas: %s" % (self.key, self.cas, cas))
            self.pre_save_update_cb(doc)
            if self.use_cas and self.cas:
                result = db.set(self.key, self._properties, cas=self.cas)
                self.cas = result.cas
            else:
                #TODO: remove for couchbase?
                result = db.set(self.key, self._properties, cas=self.cas)
                self.cas = result.cas
            self.post_save_update_cb()
            db.sync_up()
            return "updated"
        else:
            self.pre_save_new_cb()
            result = db.set(self.key, self._properties)
            self.post_save_new_cb()
            db.sync_up()

        if self.use_cas:
            self.cas = result.cas
        return "new"


    def delete(self, db):
        self.pre_delete_cb()
        db.delete(self.key, self.cas)
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
        d["properties"] = self.properties
        d[NAMESPACE_STR] = self.namespace
        d["type"] = self.type
        d["key"] = self.key
        if self.cas is not None:
            d["cas"] = self.cas
        return json.dumps(d, sort_keys=True, indent=4, separators=(',', ': '))


    def __eq__(self, other):
        equal = True

        if self.key != other.key:
            equal = False

        if self.type != other.type:
            equal = False

        for k in other.properties.keys():
            if other._properties[k] != self._properties[k]:
                equal = False
        return equal


    @classmethod
    def get(cls, db, key):
        result = db.get(key)
        if result is None:
            return None
        doc = result.value
        cas = result.cas
        return cls._from_doc(db, key, cas, doc)


    @classmethod
    def _from_doc(cls, db, key, cas, doc):

        if "_id" in doc.keys():
            del doc["_id"]

        if "_rev" in doc.keys():
            del doc["_rev"]

        correctCls = db.class_for_type_name(doc.get("type"), doc.get("namespace"))

        if correctCls is None:
            raise Exception("couldn't find class %s" % doc.get("type"))

        obj = correctCls(key=key, cas=cas, **doc)
        obj._db = db
        return obj


    @classmethod
    def from_json(cls, db, as_json):
        key = as_json["key"]
        cas = as_json.get("cas")
        doc = as_json["properties"].copy()
        doc[NAMESPACE_STR] = as_json[NAMESPACE_STR]
        doc["type"] = as_json["type"]

        return cls._from_doc(db, key, cas, doc)

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
        return [GenericObject._from_doc(db, row.key, row.cas, row.value) for row in rows]

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


    def __setattr__(self, name, value):

        if name in RESERVED_PROPERTY_NAMES:
            self.__dict__[name] = value
            return
        alias = "%s_id" % name
        if alias in self.fields.keys():
            self._properties[alias] = value.key
        elif name in self.fields.keys() or self.additional_fields:
            self._properties[name] = value
        else:
            raise Exception("you cant use this property name %s" % name)



#     def validate(self, db):
#
#         #decoration
#         if not self.additional_fields:
#             for propertyName in self.properties.keys():
#                 if not propertyName in self.fields.keys():
#                     raise ValidationException("You cannot add %s to a %s" % (propertyName, self.resource))
#
#         for name, field in self.fields.iteritems():
#             #optional
#             if not field.optional and not name in self.properties.keys():
#                 raise ValidationException("A %s must have a %s" % (self.resource, name))
#             #type
#             value = self.properties.get(name)
#             if value is not None:
#                 if not field.is_correct_type(value):
#                     raise ValidationException("Wrong type for %s field %s" % (self.resource, name))
#                 #unique TODO this should be moved into permanent views
# #                if field.unique:
# #                    map_fun = '''function(doc) {
# #                        if (doc.resource == "%s" && doc.namespace == "%s" && doc.properties.%s == %s){
# #                        emit(doc._id, doc);
# #                        }
# #                    }''' % (self.resource, self.namespace, name, repr(str(value)))
# #
# #                    results =  db.query(map_fun)
# #                    if results.total_rows != 0 :
# #                        raise ValidationException("Not Unique %s field %s" % (self.resource, name))
#


    namespace = property(_get_namespace)
    type = property(_get_type)
    properties = property(_get_properties)
