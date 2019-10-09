import copy

FIELD_TYPE_LOOKUP = {
    "ObjectField": {},
    "BoolField": {
        "type": "boolean",
    },
    "NumberField": {
        "type": "number",
    },
    "StringField": {
        "type": "string",
    },
    "ListField": {
        "type": "array",
    },
    "DictField": {
        "type": "object",
    },
    "ReferenceTo": {
        "type": "string"
    },
    "EmailField": {
        "type": "string"
    },
    "DateTimeField": {
        "type": "string"
    },
    "FractionField": {
        "type": "string"
    },
    "DecimalField": {
        "type": "string"
    }
}


def createJsonSchema(fam_class):

    class_name = fam_class.__name__.lower()
    namespace = fam_class.namespace.lower()

    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": "A Fam object model for class %s:%s" % (fam_class.namespace, fam_class.__name__),
        "type": "object",
        "properties": {
            "type":{
                "type": "string",
                "pattern": class_name
            },
            "namespace": {
                "type": "string",
                "pattern": namespace
            },
            "schema": {
                "type": "string"
            },
            "_deleted": {
                "type": "boolean"
            },
            "_id": {
                "type": "string"
            },
            "_rev": {
                "type": "string"
            }
        },
        "additionalProperties": fam_class.additional_properties,
    }

    required_fields = ["namespace", "type"]

    for name, field in fam_class.fields.items():
        field_class_name = field.__class__.__name__
        if field_class_name != "ReferenceFrom":
            field_dict = copy.deepcopy(FIELD_TYPE_LOOKUP[field_class_name])
            schema["properties"][name] = field_dict
            if hasattr(field, "pattern"):
                field_dict["pattern"] = field.pattern
            if field.required:
                required_fields.append(name)

    if len(required_fields) > 0:
        schema["required"] = sorted(required_fields)

    return schema