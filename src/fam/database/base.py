from fam.blud import ReferenceFrom, GenericObject

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

    #double dispatch accessors
    def put(self, thing):
        return thing.save(self)

    def delete(self, thing):
        return thing.delete(self)

    def get(self, key):
        return GenericObject.get(self, key)

    def delete_key(self, key):
        return GenericObject.delete_key(self, key)

#################################



    def class_for_type_name(self, type_name, namespace_name):
        return self.mapper.get_class(type_name, namespace_name)

    def _get_design(self, namespace):

        views = {}

        for type_name, cls in namespace.iteritems():
            for field_name, field in cls.fields.iteritems():
                if isinstance(field, ReferenceFrom):
                    views["%s_%s" % (type_name, field_name)] = {"map" : self._get_fk_map(field.refcls, field.refns, field.fkey)}
        design = {
           "views": views
        }

        return design


    def _get_fk_map(self, resource, namespace, keyName):
            if type(resource) == type("hello"):
                resources = [resource]
            else:
                resources = resource

            arrayStr = "['%s']" % "', '".join(resources)

            return self.FOREIGN_KEY_MAP_STRING % (arrayStr, namespace, keyName)