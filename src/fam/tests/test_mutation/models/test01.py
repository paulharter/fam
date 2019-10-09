from fam.blud import GenericObject, StringField, ReferenceTo, BoolField, NumberField, ListField, ReferenceFrom


NAMESPACE = "http://glowinthedark.co.uk/test"


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


    def changes_cb(self, db, queue, new=False):
        if self.owner:
            self.owner.add_callback(db, "changes_cb")




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

class Monkey(GenericObject):
    use_rev = False
    fields = {
        "name": StringField(),
        "colour": StringField(immutable=True),
        }