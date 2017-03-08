from fam.blud import ReferenceFrom, GenericObject
import json

class FamDbAuthException(Exception):
    pass

class BaseDatabase(object):

    FOREIGN_KEY_MAP_STRING = '''function(doc) {
    var resources = %s;
    if (resources.indexOf(doc.type) != -1 && doc.namespace == \"%s\"){
        emit(doc.%s, doc);
    }
}'''


###################################

    #double dispatch accessors that return objects

    def put(self, thing):
        return thing.save(self)

    def delete(self, thing):
        return thing.delete(self)

    def get(self, key):
        return GenericObject.get(self, key)

    def delete_key(self, key):
        return GenericObject.delete_key(self, key)

    def query_view(self, view_name, **kwargs):
        return GenericObject.view(self, view_name, **kwargs)

    def changes(self, since=None, channels=None, limit=None, feed=None, timeout=None, filter=None):
        return GenericObject.changes(self, since=since, channels=channels, limit=limit, feed=feed, timeout=timeout, filter=filter)

#################################

    def class_for_type_name(self, type_name, namespace_name):
        return self.mapper.get_class(type_name, namespace_name)

    # def _get_design(self, namespace, namespace_name):
    #
    #     views = {}
    #
    #
    #     for type_name, cls in namespace.iteritems():
    #         for field_name, field in cls.cls_fields.iteritems():
    #             if isinstance(field, ReferenceFrom):
    #                 view_key = "%s_%s" % (type_name, field_name)
    #                 # if view_key in ["person_dogs", "person_animals"]:
    #                 views[view_key] = {"map" : self._get_fk_map(field.refcls, field.refns, field.fkey)}
    #
    #             if field.unique:
    #                 view_key = "%s_%s" % (type_name, field_name)
    #                 # if view_key in ["person_dogs", "person_animals"]:
    #                 views[view_key] = {"map": self._get_fk_map(type_name, namespace_name, field_name)}
    #
    #
    #
    #     design = {
    #        "views": views
    #     }
    #
    #     return design
    #
    #
    # def _get_fk_map(self, class_name, namespace, ref_to_field_name):
    #
    #     if isinstance(class_name, list):
    #         class_names = class_name
    #     else:
    #         class_names = [class_name]
    #
    #     all_sub_class_names = set()
    #     for name in class_names:
    #         sub_classes = set(self.mapper.get_sub_class_names(namespace, name))
    #         all_sub_class_names = all_sub_class_names.union(sub_classes)
    #
    #     arrayStr = '["%s"]' % '", "'.join(all_sub_class_names)
    #     return self.FOREIGN_KEY_MAP_STRING % (arrayStr, namespace, ref_to_field_name)
