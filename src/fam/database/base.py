from fam.blud import ReferenceFrom

class FamDbAuthException(Exception):
    pass

class BaseDatabase(object):

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

            return '''function(doc) {
                var resources = %s;
                if (resources.indexOf(doc.type) != -1 && doc.namespace == \"%s\"){
                emit(doc.%s, doc);
                }
            }''' % (arrayStr, namespace, keyName)