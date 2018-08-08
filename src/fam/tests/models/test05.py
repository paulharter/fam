from fam.blud import GenericObject
from fam.fields import *


NAMESPACE = "glowinthedark.co.uk/test05"


class Cat(GenericObject):
    fields = {
        "name": StringField(),
        "colour": StringField(immutable=True),
        "tail": BoolField(immutable=True, default=True),
        "legs": NumberField(required=True),
        "owner_id": ReferenceTo(NAMESPACE, "person", required=True)
        }



class Person(GenericObject):
    fields = {
        "name": StringField(),
        "cats": ReferenceFrom(NAMESPACE, "cat", "owner_id", cascade_delete=True),
        }
