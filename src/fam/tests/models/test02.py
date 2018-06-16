from fam.blud import GenericObject, StringField, ReferenceFrom, ReferenceTo, BoolField, NumberField, DictField


NAMESPACE = "glowinthedark.co.uk/test/2"


class Dog(GenericObject):
    additional_properties = True
    fields = {
        "name": StringField(),
        "owner": ReferenceTo(NAMESPACE, "person", cascade_delete=True)
        }

    def talk(self):
        return "woof"


class Person(GenericObject):
    fields = {
        "name": StringField(),
        "dogs": ReferenceFrom(NAMESPACE, "dog", "owner_id")
        }

