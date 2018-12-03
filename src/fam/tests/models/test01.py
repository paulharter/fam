from fam.blud import GenericObject
from fam.fields import *


NAMESPACE = "glowinthedark.co.uk/test"

class Dog(GenericObject):

    additional_properties = True
    sync_gateway_write = True
    fields = {
        "name": StringField(),
        "owner_id": ReferenceTo(NAMESPACE, "person", cascade_delete=True),
        "kennel_club_membership": StringField(unique=True),
        "channels": ListField(default=["callbacks"])
        }

    def talk(self):
        return "woof"

    def pre_save_new_cb(self, db):
        pass

    def post_save_new_cb(self, db):
        pass

    def pre_save_update_cb(self, db, old_properties):
        pass

    def post_save_update_cb(self, db):
        pass

    def pre_delete_cb(self, db):
        pass

    def post_delete_cb(self, db):
        pass

    def changes_new_cb(self, db):
        if self.owner:
            self.owner.add_callback(db, "changes_new_cb")

    def changes_update_cb(self, db):
        if self.owner:
            self.owner.add_callback(db, "changes_update_cb")




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
        "email": EmailField()
        }


    @classmethod
    def all_with_n_legs(cls, db, legs):
        return db.view("animal_views/cat_legs", key=legs)


class Person(GenericObject):
    fields = {
        "name": StringField(),
        "cats": ReferenceFrom(NAMESPACE, "cat", "owner_id", cascade_delete=True),
        "dogs": ReferenceFrom(NAMESPACE, "dog", "owner_id"),
        "animals": ReferenceFrom(NAMESPACE, ["dog", "cat"], "owner_id"),
        "callbacks": ListField()
        }

    def add_callback(self, db, name):

        if self.callbacks is None:
            self.callbacks = []

        self.callbacks.append(name)
        self.save(db)


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
        "created": DateTimeField(),
        "chance": FractionField()
        }