import unittest


from fam.tests.models.test01 import Dog, Cat, Person, JackRussell, Monarch
from fam.mapper import ClassMapper

class MapperTests(unittest.TestCase):


    def setUp(self):
        self.mapper = ClassMapper([Dog, Cat, Person, JackRussell, Monarch])


    def tearDown(self):
        pass


    def test_sub_class_refs(self):

        self.assertEqual(set(Monarch.fields.keys()), set(["name", "country", "cats", "dogs", "animals", "callbacks"]))

        self.assertEqual(set(Monarch.cls_fields.keys()), {"country"})


