import inspect
import os
from slimit import ast
from slimit.parser import Parser

from fam.blud import GenericObject
from fam.schema.validator import ModelValidator

VIEW_FUNCTION_NAMES = ["map", "reduce"]


class ClassMapper(object):

    def __init__(self, classes, modules=None, schema_dir=None, designs=None):

        input_modules = modules if modules else []

        self.allow_public_write_types = []
        self.immutable_fields = {}
        self.validator = ModelValidator(classes=classes, modules=input_modules, schema_dir=schema_dir)
        self.namespaces = {}
        self.modules = {}
        self._add_classes(classes)
        self._add_modules(input_modules)
        self.sub_class_lookup = {}
        self._work_out_sub_classes()
        self.design_js_paths = designs if designs is not None else []


    def extra_design_docs(self):

        docs = []
        for filepath in self.design_js_paths:
            design_doc = self._js_design_as_doc(filepath)
            docs.append(design_doc)

        return docs


    def _add_immutable_field(self, type_name, field_name):

        # print "immutable", type_name, field_name
        field_names = self.immutable_fields.get(type_name)
        if field_names is None:
            field_names = []
            self.immutable_fields[type_name] = field_names
        field_names.append(field_name)


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


    def __iter__(self):
        for name_space_name, name_space_classes in self.namespaces.iteritems():
            for cls_name, cls in name_space_classes.iteritems():
                yield cls


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
            # gathers up information that gets added to the sync_gateway function
            if cls.sg_allow_public_write:
                self.allow_public_write_types.append(type_name)
            for field_name, field in cls.fields.iteritems():
                if field.immutable:
                    self._add_immutable_field(type_name, field_name)
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


    def _js_design_as_doc(self, filepath):

        dir, filename = os.path.split(filepath)
        name, ext = os.path.splitext(filename)

        with open(filepath) as f:
            js = f.read()

        parser = Parser()
        tree = parser.parse(js)

        views = {}

        for node in tree:
            if isinstance(node, ast.VarStatement):
                for child in node.children():
                    for grandchild in child.children():
                        if isinstance(grandchild, ast.Identifier):
                            view = {}
                            view_name = grandchild.value
                            views[view_name] = view
                        if isinstance(grandchild, ast.Object):
                            for named in grandchild.children():
                                function_name = None
                                function_body = None
                                for kv in named.children():
                                    if isinstance(kv, ast.Identifier) and kv.value in VIEW_FUNCTION_NAMES:
                                        function_name = kv.value
                                    if isinstance(kv, ast.FuncExpr):
                                        function_body = kv.to_ecma()
                                if function_name and function_body:
                                    view[function_name] = function_body


        return {"_id": "_design/%s" % name,
                "views": views}






