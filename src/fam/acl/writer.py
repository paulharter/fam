import os
import json

from .requirement import CreateRequirement, UpdateRequirement, DeleteRequirement

THIS_DIR = os.path.dirname(__file__)
PERMISSIONS_TEMPLATE_PATH = os.path.join(THIS_DIR, "sync_function.js")

def _access_from_mapper(mapper):

    types = []
    for ns_name, ns in mapper.namespaces.iteritems():
        for class_name, cls in ns.iteritems():
            if cls.grants_access:
                types.append(class_name)
    return types


def _requirements_from_mapper(mapper):

    create_reqs = {}
    update_reqs = {}
    delete_reqs = {}

    requirements = {"create": create_reqs,
                    "update": update_reqs,
                    "delete": delete_reqs}

    for ns_name, ns in mapper.namespaces.iteritems():
        for class_name, cls in ns.iteritems():
            if cls.acl is not None:
                class_create_req = [r for r in cls.acl if isinstance(r, CreateRequirement)]
                if len(class_create_req) == 0:
                    create_reqs[class_name] = CreateRequirement().as_json()
                elif len(class_create_req) == 1:
                    create_reqs[class_name] = class_create_req[0].as_json()
                else:
                    raise Exception("too many create requirements in %s" % class_name)

                class_update_req = [r for r in cls.acl if isinstance(r, UpdateRequirement)]
                if len(class_update_req) == 0:
                    update_reqs[class_name] = [UpdateRequirement().as_json()]
                else:
                    update_reqs[class_name] = [req.as_json() for req in class_update_req]

                class_delete_req = [r for r in cls.acl if isinstance(r, DeleteRequirement)]
                if len(class_delete_req) == 0:
                    delete_reqs[class_name] = DeleteRequirement().as_json()
                elif len(class_create_req) == 1:
                    delete_reqs[class_name] = class_delete_req[0].as_json()
                else:
                    raise Exception("too many delete requirements in %s" % class_name)

    return requirements


def write_sync_function(src, dst, mapper, extra=None):

    with open(src, "r") as f:
        config_src_str = f.read()

    config_src_str = config_src_str.replace("sync = ", "")

    with open(PERMISSIONS_TEMPLATE_PATH, "r") as f:
        permissions = f.read()

    requirements_str = json.dumps(_requirements_from_mapper(mapper))
    access_types_str = json.dumps(_access_from_mapper(mapper))

    permissions = permissions.replace("sync = ", "")
    permissions = permissions.replace('"REQUIREMENTS_LOOKUP"', requirements_str)
    permissions = permissions.replace('"ACCESS_TYPES"', access_types_str)

    config_str = config_src_str.replace("SYNC_FUNCTION", permissions)

    with open(dst, "w") as f:
        f.write(config_str)






