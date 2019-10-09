import unittest
from fam.exceptions import *
from fam.tests.models.test01 import Cat, Person, Monkey


class FieldAttributeBaseTests:

    class FieldAttributeTests(unittest.TestCase):

        db = None

        def make_red(self, animal):
            animal.colour = "red"

        def cut_off_tail(self, animal):
            animal.tail = False

        def get_address(self, animal):
            return animal.address

        def test_immutability(self):
            paul = Person(name="paul")
            paul.save(self.db)
            cat = Cat(colour="tabby", legs=4, owner=paul)
            self.assertRaises(FamImmutableError, self.make_red, cat)

        def test_immutability_on_non_existant_value(self):
            paul = Person(name="paul")
            paul.save(self.db)
            cat = Cat(legs=4, owner=paul)
            self.make_red(cat)

        def test_getting_absent_no_defaults_returns_none(self):
            paul = Person(name="paul")
            paul.save(self.db)
            cat = Cat(legs=4, owner=paul)
            name = cat.name
            self.assertEqual(name, None)

        def test_getting_unknown_fails(self):
            paul = Person(name="paul")
            paul.save(self.db)
            cat = Cat(legs=4, owner=paul)
            self.assertRaises(AttributeError, self.get_address, cat)

        def test_immutable_defaults(self):
            paul = Person(name="paul")
            paul.save(self.db)
            cat = Cat(legs=4, owner=paul)
            self.assertTrue(cat.tail == True)
            self.assertRaises(FamImmutableError, self.cut_off_tail, cat)

        def test_immutable_saving(self):

            monkey = Monkey(key="red_monkey", colour="red")
            self.db.put(monkey)
            monkey = Monkey(key="red_monkey", colour="blue")
            self.assertRaises(FamImmutableError, self.db.put, monkey)

        #
        # def test_using_default_and_required_fails(self):
        #
        #     def duff_import():
        #         from fam.tests.models import test03
        #         print(test03)
        #
        #     self.assertRaises(FamError, duff_import)