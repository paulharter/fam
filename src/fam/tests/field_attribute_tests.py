import os
from copy import deepcopy
import unittest
from fam.database import CouchDBWrapper
from fam.mapper import ClassMapper
from config import *
from fam.exceptions import *
from mock import MagicMock, patch

from fam.tests.models.test01 import GenericObject, Dog, Cat, Person, JackRussell, Monkey, Monarch, NAMESPACE

class FieldAttributeTests(unittest.TestCase):


    def setUp(self):
        mapper = ClassMapper([Dog, Cat, Person, JackRussell, Monkey, Monarch])
        self.db = CouchDBWrapper(mapper, COUCHDB_URL, COUCHDB_NAME, reset=True)
        self.db.update_designs()


    def tearDown(self):
        pass

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

    def test_defaults(self):
        paul = Person(name="paul")
        paul.save(self.db)
        cat = Cat(legs=4, owner=paul)
        self.assertTrue(cat.email == "cat@home.com")

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



    def test_using_default_and_required_fails(self):

        def duff_import():
            from fam.tests.models import test03
            print test03

        self.assertRaises(FamError, duff_import)