from fam.blud import ReferenceFrom, GenericObject
import json

class FamDbAuthException(Exception):
    pass

class BaseDatabase(object):

    FOREIGN_KEY_MAP_STRING = '''function(doc) {
    var resources = %s;
    if (resources.indexOf(doc.type) != -1 && doc.namespace == \"%s\"){
        emit(doc.%s, null);
    }
}'''

    check_on_save = True

###################################

    #double dispatch accessors that return objects

    def put(self, thing):
        return thing.save(self)

    def delete(self, thing):
        return thing.delete(self)

    def get(self, key, class_name=None):
        return GenericObject.get(self, key, class_name=class_name)

    def delete_key(self, key):
        return GenericObject.delete_key(self, key)

    def query_view(self, view_name, **kwargs):
        return GenericObject.view(self, view_name, **kwargs)

    def changes(self, since=None, channels=None, limit=None, feed=None, timeout=None, filter=None):
        return GenericObject.changes(self, since=since, channels=channels, limit=limit, feed=feed, timeout=timeout, filter=filter)


#################################

    def class_for_type_name(self, type_name, namespace_name):
        return self.mapper.get_class(type_name, namespace_name)

