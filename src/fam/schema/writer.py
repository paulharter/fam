import copy

FIELD_TYPE_LOOKUP = {
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
}


def writeJsonSchema(fam_class):

    schema = {
        "id": "https://roughcutpro.com/schemata/%s.json" % fam_class.__name__.lower(),
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": "A Fam object model for class %s" % fam_class.__name__,
        "type": "object",
        "properties": {},
        "additionalProperties": fam_class.additional_properties,
    }

    properties = {}
    required_fields = []

    for name, field in fam_class.fields.iteritems():
        field_dict = copy.deepcopy(FIELD_TYPE_LOOKUP[field.__class__.__name__])
        schema["properties"][name] = field_dict
        if hasattr(field, "pattern"):
            field_dict["pattern"] = field.pattern
        if field.required:
            required_fields.append(name)


