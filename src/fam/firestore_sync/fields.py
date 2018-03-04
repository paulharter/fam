
from fam.blud import Field
from google.cloud.firestore_v1beta1 import GeoPoint


class GeoPointField(Field):

    def is_correct_type(self, value):
        return type(value) == GeoPoint or value == None

