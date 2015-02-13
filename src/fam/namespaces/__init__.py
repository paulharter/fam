import inspect
import couchdb
from couchbase import Couchbase
from couchbase.exceptions import NotFoundError, HTTPError
import os
import requests
import json
from fam.blud import GenericObject, ReferenceFrom, ReferenceTo

SPACES = {}
CLASSES = {}
ALL_CLASSES = {}


def add_namespace(module, name=None):
    ns = module.NAMESPACE
    ALL_CLASSES.update(module.routes)
    SPACES[ns] = module
    classes = {}
    CLASSES[ns] = classes
    for k, obj in module.__dict__.iteritems():
        if inspect.isclass(obj):
            if issubclass(obj, GenericObject):
                if obj != GenericObject:
                    if not k.startswith("_"):
                        validate_class(obj)
                        classes[k.lower()] = obj

    if name is not None:
        gd = globals()
        gd[name] = module


def validate_class(cls):
    for name, field in cls.fields.iteritems():
        if isinstance(field, ReferenceTo):
            if not name.endswith("_id"):
                raise Exception("ReferenceTo fields must have names ending with _id")
        
def add_models(modulename, modelsfolder):


    for filename in os.listdir(modelsfolder):

        filepath = os.path.join(modelsfolder, filename)
        if os.path.isdir(filepath):
            return
        filename = os.path.split(filepath)[1]
        base, ext = os.path.splitext(filename)
        module = None
        if ext == ".py":
            if base != "__init__":
                exec("import %s.models.%s as module" % (modulename, base))
                if module is not None:
                    add_namespace(module)



def add_namespace_file(filepath):
    if os.path.isdir(filepath):
        return
    filename = os.path.split(filepath)[1]
    base, ext = os.path.splitext(filename)
    module = None
    if ext == ".py":
        if base != "__init__":
            exec("import %s as module" % base)
            if module is not None:
                add_namespace(module)


def get_namespace(namespace):
    return SPACES.get(namespace)

def get_class_from_route(route):
    cls = ALL_CLASSES.get(route.lower())
    return cls

def get_class(namespace, resource):
    
    space = CLASSES.get(namespace)
    if space is None: 
        print 'failed to find class', namespace, resource
        return None
    cls = space.get(resource.lower())
    return cls


dirpath = os.path.dirname(__file__)

for filename in os.listdir(dirpath):
    add_namespace_file(os.path.join(dirpath,filename))

    
def _get_fk_map(resource, namespace, keyName):
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



def update_designs_couchbase(db_name, host):

    db = Couchbase.connect(bucket=db_name, host=host)

    views = {"all":
            {"map" : '''function(doc) {
            emit(doc.type, doc);
        }'''}
        }

    newalldesign = {"views": views}

    try:
        old_design = db.design_get("raw")
        newalldesign["cas"] = old_design["cas"]
    except HTTPError:
        pass

    db.design_create("raw", newalldesign, use_devmode=False)

    for ns in SPACES:
        new_design = _get_design(ns, None)
        design_name = ns.replace("/", "_")

        try:
            old_design = db.design_get(design_name)
            new_design["cas"] = old_design["cas"]
        except HTTPError:
            pass

        db.design_create(design_name, new_design, use_devmode=False)



def update_cblite_designs(db_name, db_url):

        allid = "_design/raw"

        views = {"all":
                {"map" : '''function(doc) {
                emit(doc.type, doc);
            }'''}
            }

        for ns in SPACES:
            space = CLASSES.get(ns)
            for _classname, cls in space.iteritems():

                views.update(cls.views)

        newalldesign = {"views": views}
        newalldesign["_id"] = allid

        rsp = requests.get("%s/%s/%s" % (db_url, db_name, allid))

        if rsp.status_code == 200:
            alldesign = rsp.json()
            newalldesign["_rev"] = alldesign["_rev"]

        if not(rsp.status_code == 404 or rsp.status_code == 200):
            raise Exception("Unknown Error update_cblite_designs: %s %s" % (rsp.status_code, rsp.text))


        rsp = requests.post("%s/%s" % (db_url, db_name), data=json.dumps(newalldesign), headers={"Content-Type": "application/json"})

        if not(rsp.status_code == 200 or rsp.status_code == 201):
            raise Exception("Unknown Error update_cblite_designs: %s %s" % (rsp.status_code, rsp.text))


        for ns in SPACES:
            viewnamespace = ns.replace("/", "_")
            id = "_design/%s" % viewnamespace
            rsp = requests.get("%s/%s/%s" % (db_url, db_name, id))

            if rsp.status_code == 200:
                design = rsp.json()
                rev = design["_rev"]
            else:
                rev = None

            attrs = _get_design(ns, rev)
            attrs["_id"] = id

            rsp = requests.post("%s/%s" % (db_url, db_name), data=json.dumps(attrs), headers={"Content-Type": "application/json"})

            if not(rsp.status_code == 200 or rsp.status_code == 201):
                raise Exception("Unknown Error update_cblite_designs: %s %s" % (rsp.status_code, rsp.text))



#
# def update_designs(dburl):
#     """
#     This writes into the given database a view for each of the ReferenceFrom fields in each namespace. Each namespace gets its own _design doc to hold these views
#     this doc COULD potentially hold couchdb validation too
#     these views are then used by model.add_collection
#     """
#
#     server = couchdb.Server(dburl)
#
#     for dbname in server:
#         if not dbname.startswith("_"):
#             db = server[dbname]
#             allid = "_design/raw"
#
#             views = {"all":
#                     {"map" : '''function(doc) {
#                     emit(doc.type, doc);
#                 }'''}
#                 }
#
#
#             for ns in SPACES:
#                 space = CLASSES.get(ns)
#                 for _classname, cls in space.iteritems():
#
#                     views.update(cls.views)
#
#
#             newalldesign = {"views": views}
#
#
#             alldesign = db.get(allid)
#             if alldesign:
#                 newalldesign["_rev"] = alldesign["_rev"]
#             db[allid] = newalldesign
#
#             for ns in SPACES:
#                 viewnamespace = ns.replace("/", "_")
#                 id = "_design/%s" % viewnamespace
#                 design = db.get(id)
#                 if design:
#                     rev = design["_rev"]
#                 else:
#                     rev = None
#                 db[id] = _get_design(ns, rev)



def _get_design(namespace, rev):

    space = CLASSES.get(namespace)
    views = {}

    for classname, cls in space.iteritems():
        for fieldname, field in cls.fields.iteritems():
            if isinstance(field, ReferenceFrom):
                views["%s_%s" % (classname, fieldname)] = {"map" : _get_fk_map(field.refcls, field.refns, field.fkey)}

        views.update(cls.views)
    design = {
       "views": views
    }

    if rev is not None:
        design["_rev"] = rev

    return design

