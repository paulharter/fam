import simplejson as json
import uuid
import datetime
import types
import sys
from copy import deepcopy

from fam.fam_json import object_default

from .constants import *
from .exceptions import *

__all__ = [
    "BoolField",
    "NumberField",
    "StringField",
    "ListField",
    "DictField",
    "ObjectField",
    "ReferenceTo",
    "ReferenceFrom",
    "GenericObject"
]

class Field(object):
    
    object = "base"
    
    def __init__(self, required=False, immutable=False, default=None):
        self.required = required
        self.immutable = immutable
        self.default = default

        if self.default is not None and self.required is True:
            raise FamError("It doesnt really make sense to use both required and default together. Just use default")


    def is_correct_type(self, value):
        return True

    def get_default(self):
        return self.default

    
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

    def __init__(self, item_cls=None, required=False, immutable=False, default=None):
        self.item_cls = item_cls
        if not hasattr(item_cls, "to_json") and hasattr(item_cls, "from_json"):
            raise Exception("the class used for a lists items must have to_json and from_json methods")

        super(ListField, self).__init__(required=required, immutable=immutable, default=default)

    def get_default(self):
        return deepcopy(self.default)

    def is_correct_type(self, value):
        return type(value) == types.ListType or type(value) == types.NoneType

class DictField(Field):

    def get_default(self):
        return deepcopy(self.default)

    def is_correct_type(self, value):
        return type(value) == types.DictType or type(value) == types.NoneType

class ObjectField(Field):

    def get_default(self):
        return self.cls()

    def __init__(self, cls, default=None, required=False):
        self.cls = cls
        if not hasattr(cls, "to_json") and hasattr(cls, "from_json"):
            raise Exception("the class used for a n ObjectField must have to_json and from_json methods")

        super(ObjectField, self).__init__(default=default, required=required)

    def is_correct_type(self, value):
        return value.__class__ == self.cls


class ReferenceTo(Field):

    def __init__(self, refns, refcls, required=False, immutable=False, default=None, cascade_delete=False):
        self.refns = refns
        self.refcls = refcls
        self.cascade_delete = cascade_delete
        super(ReferenceTo, self).__init__(required, immutable, default)

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

    def __init__(self, refns, refcls, fkey, required=False, immutable=False, default=None, cascade_delete=False):
        self.refns = refns
        self.refcls = refcls
        self.fkey = fkey
        self.cascade_delete = cascade_delete
        super(ReferenceFrom, self).__init__(required, immutable, default)

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
        # take a copy of this classes own fields
        attrs["cls_fields"] = {} if attrs["fields"] is None else attrs["fields"].copy()

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


class FamObject(object):
    use_rev = True
    additional_properties = False
    # extra sync gateway keywords that are used by sync function
    sg_allow_public_write = False
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
        return cls._query_view(db, "raw/all", cls.type)

    @classmethod
    def changes(cls, db, since=None, channels=None, limit=None, feed="normal", timeout=None):
        last_seq, rows  =  db.changes(since=since, channels=channels, limit=limit, feed=feed, timeout=timeout)
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


    def _check_defaults(self):
        for field_name, field in self.__class__.fields.iteritems():
            if field.default is not None and not field_name in self._properties:
                self._properties[field_name] = field.get_default()

    def _check_immutable(self, existing_doc):
        for field_name, field in self.__class__.fields.iteritems():
            if field.immutable:
                if field_name in existing_doc and getattr(self, field_name) != existing_doc[field_name]:
                    raise FamImmutableError("You can't change the value of {} on a {} it has been made immutable".format(field_name, self.__class__.__name__))


    def save(self, db):
        self._db = db
        result = db._get(self.key)
        if result:
            doc = result.value
            rev = result.rev

            self._check_immutable(doc)

            # raise a conflict if revs different
            if self.use_rev and rev != self.rev:
                raise FamResourceConflict("bad rev id: %s, rev: %s db_rev: %s" % (self.key, self.rev, rev))

            self.pre_save_update_cb(doc)
            # just force the rev if not using it
            result = db._set(self.key, self._properties, rev=self.rev if self.use_rev else rev)

            if self.use_rev:
                self.rev = result.rev

            self.post_save_update_cb()
            updated = True
        else:
            self.pre_save_new_cb()
            result = db._set(self.key, self._properties)
            self.post_save_new_cb()
            updated = False

        # db.sync_up()
        if self.use_rev:
            self.rev = result.rev

        return updated


    def delete(self, db):
        self.pre_delete_cb()
        db._delete(self.key, self.rev)
        self.post_delete_cb()
        self.delete_references(db)
        # db.sync_up()


    @classmethod
    def delete_key(cls, db, key):
        obj = cls.get(db, key)
        obj.delete(db)


    def delete_references(self, db):
        for field_name, field in self.__class__.fields.iteritems():
            if isinstance(field, ReferenceTo):
                if field.cascade_delete:
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

                if field.cascade_delete:
                    for obj in objs:
                        obj.delete(db)
                else:
                    for obj in objs:
                        del obj._properties[field.fkey]
                        obj.save(db)

    def __str__(self):
        return self.as_json()

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
    def get(cls, db, key):
        # ugly thing to get around cache double dispatch

        if not hasattr(db, "_get"):
            #this will call back here but using the correct db
            return db.get(key)

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
                raise Exception("no db")
            view_namespace = self.namespace.replace("/", "_")
            # look at super class gypes to find clas with ref

            type_name = self.__class__._type_with_ref(name)

            view_name = "%s/%s_%s" % (view_namespace, type_name, name)
            return self._query_view(self._db, view_name, self.key)

        if "%s_id" % name in self.properties.keys():
            id_name = "%s_id" % name
            ref = self.__class__.fields.get(id_name)
            if isinstance(ref, ReferenceTo):
                if self._db is None:
                    raise Exception("no db")
                return GenericObject.get(self._db, self._properties[id_name])
        if name in self._properties.keys():
            # if it is a subclass of stringfield for string formats
            if isinstance(field, StringField) and not field.__class__ == StringField:
                if hasattr(field, "from_json"):
                    return field.from_json(self._properties[name])
            return self._properties[name]
        if name in self.__class__.fields:
            return None
        elif "%s_id" % name in self.__class__.fields:
            return None
        elif name == "rev":
            return None
        else:
            raise AttributeError("Not found %s" % name)


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

        elif name in self.fields or name in ("type", "namespace", "schema") or self.additional_properties :
            field = self.fields.get(name)
            if field is not None:
                if field.immutable and name in self._properties:
                    raise FamImmutableError("You cannot change the immutable property %s" % name)
                if isinstance(field, ObjectField) and not isinstance(value, field.cls):
                    value = field.cls.from_json(value)

                if isinstance(field, ListField) and field.item_cls is not None:

                    #cast the items in the list into a certain class
                    value = [field.item_cls.from_json(i) for i in value]

                if issubclass(field.__class__, StringField) and not (isinstance(value, basestring) or value is None):
                    value = field.to_json(value)
            self._update_property(name, value)
        else:
            raise FamValidationError("""You cant use the property name %s on the class %s
            If you would like to set additional properties on this class that are not specified
            set the class attribute "additional_properties" to True.
            """ % (name, self.__class__.__name__))


    namespace = property(_get_namespace)
    type = property(_get_type)
    properties = property(_get_properties)


GenericObject = FamObject
