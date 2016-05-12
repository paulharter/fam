from fam.blud import GenericObject, StringField, ReferenceFrom, ReferenceTo, BoolField, NumberField, DictField, ObjectField
from fam.string_formats import DateTimeField
from fam.string_formats import EmailField

NAMESPACE = "glowinthedark.co.uk/test"


class Dog(GenericObject):

    additional_properties = True
    sync_gateway_write = True
    fields = {
        "name": StringField(),
        "owner_id": ReferenceTo(NAMESPACE, "person", cascade_delete=True)
        }

    def talk(self):
        return "woof"


class JackRussell(Dog):
    fields = {
        "age": NumberField()
        }

    def talk(self):
        return "Yap"


class Cat(GenericObject):
    fields = {
        "name": StringField(),
        "colour": StringField(immutable=True),
        "tail": BoolField(immutable=True, default=True),
        "legs": NumberField(required=True),
        "owner_id": ReferenceTo(NAMESPACE, "person", required=True),
        "email": EmailField(default="cat@home.com")
        }


class Person(GenericObject):
    fields = {
        "name": StringField(),
        "cats": ReferenceFrom(NAMESPACE, "cat", "owner_id", cascade_delete=True),
        "dogs": ReferenceFrom(NAMESPACE, "dog", "owner_id"),
        "animals": ReferenceFrom(NAMESPACE, ["dog", "cat"], "owner_id")
        }


class Monarch(Person):
    fields = {
        "country": StringField(),
        }


class Monkey(GenericObject):
    use_rev = False
    fields = {
        "name": StringField(),
        "colour": StringField(immutable=True),
        }


class Weapons(object):

    def __init__(self, wings, fire, claws):

        self.fire = fire
        self.claws = claws
        self.wings = wings

    def to_json(self):

        return {
            "fire": self.fire,
            "claws": self.claws,
            "wings": self.wings,
        }

    @classmethod
    def from_json(cls, as_json):
        return cls(as_json["wings"], as_json["fire"], as_json["claws"])



class Monster(GenericObject):

    fields = {
        "name": StringField(),
        "weapons": ObjectField(cls=Weapons),
        }

class Event(GenericObject):

    fields = {
        "name": StringField(),
        "created": DateTimeField()
        }