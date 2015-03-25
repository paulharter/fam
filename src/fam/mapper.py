from fam.blud import GenericObject


class ClassMapper(object):

    def __init__(self, classes):
        self.namespaces = {}
        self.modules = {}
        self._add_classes(classes)

    def _add_classes(self, classes):

        for cls in classes:
            namespace_name = cls.namespace
            type_name = cls.type

            namespace = self.namespaces.get(namespace_name)
            if namespace is None:
                namespace = {}
                self.namespaces[namespace_name] = namespace

            if not issubclass(cls, GenericObject):
                raise Exception("Classes you add to a ClassMapper must inherit from fam.blud.GenericObject this one does not: %s" % cls)
            namespace[type_name] = cls


    def get_class(self, type_name, namespace_name):
        namespace = self.namespaces.get(namespace_name)
        if namespace is None:
            return None
        return namespace.get(type_name)






