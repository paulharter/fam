import inspect

from fam.blud import GenericObject
from fam.schema.validator import ModelValidator


class ClassMapper(object):

    def __init__(self, classes, modules=[]):
        self.validator = ModelValidator(classes=classes, modules=modules)
        self.namespaces = {}
        self.modules = {}
        self._add_classes(classes)
        self._add_modules(modules)
        self.sub_class_lookup = {}
        self._work_out_sub_classes()


    def _add_modules(self, modules):
        for module in modules:
            classes = []
            for k, obj in module.__dict__.iteritems():
                if inspect.isclass(obj):
                    if issubclass(obj, GenericObject):
                        if obj != GenericObject:
                            if not k.startswith("_"):
                                classes.append(obj)
            self._add_classes(classes)


    def get_sub_class_names(self, namespace, class_name):
        return self.sub_class_lookup[(namespace, class_name)]

    def _work_out_sub_classes(self):

        # for each class add their subclasses type names to a lookup table keyed by namespace and classname
        # only works within a given namespace
        for namespace_name, namespace in self.namespaces.iteritems():
            for class_name_super, cls_super in namespace.iteritems():
                subclasses = []
                self.sub_class_lookup[(namespace_name, class_name_super)] = subclasses
                for class_name_sub, cls_sub in namespace.iteritems():
                    if issubclass(cls_sub, cls_super):
                        subclasses.append(class_name_sub)




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






