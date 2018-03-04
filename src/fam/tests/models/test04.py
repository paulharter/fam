from fam.blud import GenericObject, StringField, ReferenceFrom, ReferenceTo, BoolField, NumberField, DictField, ObjectField, ListField
from fam.firestore_sync.fields import GeoPointField


NAMESPACE = "glowinthedark.co.uk/test"



class House(GenericObject):

    fields = {
        "name": StringField(),
        "location": GeoPointField(),
        }


class Fence(GenericObject):

    fields = {
        "name": StringField(),
        "boundary": ListField()
        }
