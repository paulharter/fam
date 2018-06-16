from fam.blud import (GenericObject,
                      StringField,
                      ReferenceFrom,
                      ReferenceTo,
                      BoolField,
                      NumberField,
                      DictField,
                      ObjectField,
                      ListField,
                      LatLongField,
                      DateTimeField,
                      FractionField,
                      DecimalField,
                      BytesField)


NAMESPACE = "glowinthedark.co.uk/test"



class House(GenericObject):

    fields = {
        "name": StringField(),
        "location": LatLongField(),
        }


class Fence(GenericObject):

    fields = {
        "name": StringField(),
        "boundary": ListField()
        }


class Fish(GenericObject):

    fields = {
        "name": StringField(),
        "location": LatLongField(),
        "born": DateTimeField(),
        "length": DecimalField(),
        "edible_fraction": FractionField(),
        "image": BytesField()
        }