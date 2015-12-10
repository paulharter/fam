from fam.blud import GenericObject, StringField, ReferenceFrom, ReferenceTo, BoolField, NumberField, DictField
from fam.string_formats import EmailField

NAMESPACE = "glowinthedark.co.uk/test/3"


class Dog(GenericObject):
    additional_properties = True
    fields = {
        "name": StringField(default="fly", required=True),
        "owner_id": ReferenceTo(NAMESPACE, "person", delete="cascade")
        }

    def talk(self):
        return "woof"

