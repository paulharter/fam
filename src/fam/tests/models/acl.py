from fam.blud import GenericObject, StringField, ReferenceFrom, ReferenceTo, BoolField, NumberField, DictField, ObjectField, ListField
from fam.acl import CreateRequirement, DeleteRequirement, UpdateRequirement, NO_ONE, ANYONE

NAMESPACE = "glowinthedark.co.uk/test"



class Bike(GenericObject):

    fields = {
        "wheels": NumberField(),
        }


class Car(GenericObject):

    fields = {
        "colour": StringField(),
        "stars": NumberField(),
        "owner_name": StringField(),
        "channels": ListField(),
        "access":  ListField()
        }

    grants_access = True

    acl = [
        CreateRequirement(role=None, owner=True),
        DeleteRequirement(role=None, owner=True),
        UpdateRequirement(role=[], fields=["access"]),
        UpdateRequirement(role=None, owner=True, fields=["colour"]),
    ]

class Boat(GenericObject):

    fields = {
        "name": StringField(),
        "is_sail": BoolField(),
        "owner_name": StringField(),
        "channels": ListField(),
        "access": ListField()
    }

    grants_access = True

    acl = [
        CreateRequirement(role=ANYONE, owner=True, access=False),
        UpdateRequirement(role=NO_ONE),
        DeleteRequirement(role=ANYONE, owner=True),
    ]


