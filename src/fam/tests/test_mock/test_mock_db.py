import unittest
import json
import time
import os


import fam
from fam.exceptions import *
from fam.tests.models.test01 import GenericObject, Dog, Cat, Person, JackRussell, Monkey, Monarch, NAMESPACE

from fam.database.mock import MockDatabase
from fam.mapper import ClassMapper


class TestDB(unittest.TestCase):


    def setUp(self):
        mapper = ClassMapper([Dog, Cat, Person, JackRussell, Monkey, Monarch])
        self.db = MockDatabase(mapper)


    def test_app(self):
        self.assertNotEqual(self.db, None)

    def test_make_an_object(self):
        dog = Dog(name="woofer")
        self.assertEqual(dog.namespace, NAMESPACE)
        self.assertEqual(dog.type, "dog")
        self.assertEqual(dog.name, "woofer")
        self.assertEqual(dog.__class__, Dog)

    def test_make_an_object2(self):
        dog = Dog(name="woofer")
        self.assertEqual(dog.talk(), "woof")

    def test_make_a_sub_object(self):
        jack = JackRussell()
        self.assertEqual(jack.talk(), "Yap")
        jack.name = "jack"
        jack.age = 12
        self.db.put(jack)


    def test_make_an_object_saved(self):
        dog = Dog(name="woofer")
        self.db.put(dog)
        self.assertEqual(dog.namespace, NAMESPACE)
        self.assertEqual(dog.type, "dog")
        self.assertEqual(dog.name, "woofer")
        self.assertEqual(dog.__class__, Dog)
        self.assertNotEqual(dog.key, None)
        # self.assertTrue(dog.schema.startswith("http://glowinthedark.co.uk/test/dog"))


    def test_make_an_object_double_dispatch_saved(self):
        dog = Dog(name="woofer")
        self.db.put(dog)
        self.assertEqual(dog.namespace, NAMESPACE)
        self.assertEqual(dog.type, "dog")
        self.assertEqual(dog.name, "woofer")
        self.assertEqual(dog.__class__, Dog)
        self.assertNotEqual(dog.key, None)


    def test_make_an_object_with_additional_properties(self):
        dog = Dog(name="woofer", collar="leather")
        dog.home = "hackney"
        self.db.put(dog)
        self.assertEqual(dog.home, "hackney")

    def test_fail_with_additional_properties(self):

        def wrong_monkey():
            return Monkey(name="bonzo", collar="leather")

        def collar_monkey(monkey):
            monkey.collar = "leather"

        self.assertRaises(FamValidationError, wrong_monkey)
        monkey = Monkey(name="bonzo")
        self.assertRaises(FamValidationError, collar_monkey, monkey)


    def test_get_cat(self):
        paul = Person(name="paul")
        self.db.put(paul)
        cat = Cat(name="whiskers", owner_id=paul.key, legs=2)
        self.db.put(cat)
        another = Cat.get(self.db, cat.key)
        self.assertEqual(cat, another)

    def test_get_created_cat(self):
        paul = Person(name="paul")
        self.db.put(paul)
        cat = Cat.create(self.db, name="whiskers", owner_id=paul.key, legs=2)

        another = Cat.get(self.db, cat.key)
        self.assertEqual(cat, another)


    def test_ref_to(self):
        paul = Person(name="paul")
        self.db.put(paul)
        cat = Cat(name="whiskers", owner_id=paul.key, legs=2)
        self.db.put(cat)
        self.assertEqual(cat.owner, paul)
        self.assertEqual(cat.owner.name, "paul")


    def test_ref_to_with_object(self):
        paul = Person(name="paul")
        self.db.put(paul)
        cat = Cat(name="whiskers", owner=paul, legs=2)
        self.db.put(cat)
        self.assertEqual(cat.owner, paul)
        self.assertEqual(cat.owner.name, "paul")
        catback = Cat.get(self.db, cat.key)
        self.assertEqual(cat, catback)

    def test_ref_from(self):
        paul = Person(name="paul")
        self.db.put(paul)
        cat = Cat(name="whiskers", owner_id=paul.key, legs=2)
        self.db.put(cat)
        cat2 = Cat(name="puss", owner_id=paul.key, legs=2)
        self.db.put(cat2)
        cats = list(paul.cats)
        self.assertEqual(len(cats), 2)
        cats = list(paul.cats)
        self.assertTrue(cats[0] == cat or cats[1] == cat)

    def test_ref_from_multiple_index(self):
        paul = Person(name="paul")
        self.db.put(paul)
        cat = Cat(name="whiskers", owner_id=paul.key, legs=2)
        self.db.put(cat)
        dog = Dog(name="fly", owner=paul)
        self.db.put(dog)
        cats = list(paul.cats)
        self.assertEqual(len(cats), 1)
        dogs = list(paul.dogs)
        self.assertEqual(len(dogs), 1)
        animals = list(paul.animals)
        self.assertEqual(len(animals), 2)


    def test_refs_with_inheritance(self):
        paul = Person(name="paul")
        self.db.put(paul)
        jack = JackRussell()
        jack.owner_id = paul.key
        jack.name = "jack"
        jack.save(self.db)
        self.assertEqual(list(paul.dogs)[0], jack)


    def test_refs_with_other_inheritance(self):
        paul = Monarch(name="paul")
        self.db.put(paul)
        jack = Dog()
        jack.owner = paul
        jack.name = "jack"
        self.db.put(jack)
        dogs = list(paul.dogs)
        self.assertEqual(dogs[0], jack)

    def test_delete_cat_dd(self):
        paul = Person(name="paul")
        self.db.put(paul)
        cat = Cat(name="whiskers", owner_id=paul.key, legs=2)
        self.db.put(cat)
        key = cat.key
        another = Cat.get(self.db, cat.key)
        self.assertEqual(cat, another)
        self.db.delete(cat)
        revivedcat = self.db.get(key)
        self.assertEqual(revivedcat, None)


    def test_delete_dog_to_refs(self):
        paul = Person(name="paul")
        self.db.put(paul)
        dog = Dog(name="rufus", owner_id=paul.key)
        self.db.put(dog)
        key = dog.key
        dog2 = Dog(name="fly", owner_id=paul.key)
        self.db.put(dog2)
        self.assertTrue(dog2.owner is not None)
        key = paul.key
        self.db.delete(dog)
        revivedpaul = self.db.get(key)
        self.assertTrue(revivedpaul is None)
        refresheddog2 = Dog.get(self.db, dog2.key)
        self.assertTrue(refresheddog2.owner is None)


    def test_delete_cat_refs(self):
        paul = Person(name="paul")
        self.db.put(paul)
        cat = Cat(name="whiskers", owner_id=paul.key, legs=2)
        self.assertTrue("dogs" not in cat.__class__.fields.items())
        self.db.put(cat)
        key = cat.key
        cat2 = Cat(name="puss", owner_id=paul.key, legs=2)
        self.assertTrue("dogs" not in cat2.__class__.fields.items())
        self.db.put(cat2)
        revivedcat1 = Cat.get(self.db, key)
        self.assertTrue(revivedcat1 is not None)
        self.db.delete(paul)
        revivedcat2 = self.db.get(key)

        self.assertTrue(revivedcat2 is None)


    def test_delete_dog_refs(self):
        paul = Person(name="paul")
        self.db.put(paul)
        dog = Dog(name="rufus", owner_id=paul.key)
        self.db.put(dog)
        key = dog.key
        dog2 = Dog(name="fly", owner_id=paul.key)
        self.db.put(dog2)
        reviveddog1 = Dog.get(self.db, key)
        self.assertTrue(reviveddog1 is not None)
        self.db.delete(paul)
        reviveddog2 = Dog.get(self.db, key)
        self.assertTrue(reviveddog2 is not None)


    def test_update_cat(self):
        paul = Person(name="paul")
        self.db.put(paul)
        cat = Cat(name="whiskers", owner_id=paul.key, legs=2)
        self.db.put(cat)
        cat.name = "blackie"
        self.db.put(cat)

        self.assertEqual(cat.name, "blackie")
        self.assertEqual(cat._properties["name"], "blackie")
        self.assertFalse("name" in cat.__dict__.keys())

        got = Cat.get(self.db, cat.key)

        self.assertEqual(got.name, "blackie")


    def test_update_cat_fails(self):
        paul = Person(name="paul")
        self.db.put(paul)
        cat = Cat(name="whiskers", owner_id=paul.key, legs=2)
        self.db.put(cat)
        cat.colour = "black"
        self.db.put(cat)
        def change_colour():
            cat.colour = "white"
        self.assertRaises(FamImmutableError, change_colour)



    def setcatfood(self):
        self.cat.food = "biscuits"


    def test_update_catfood(self):
        paul = Person(name="paul")
        self.db.put(paul)
        cat = Cat(name="whiskers", owner_id=paul.key, legs=2)
        self.db.put(cat)
        self.assertRaises(Exception, self.setcatfood)

    def test_update_dogfood(self):
        dog = Dog(name="fly")
        dog.food = "biscuits"
        self.db.put(dog)


    def test_update_works_without_rev(self):
        monkey = Monkey(name="fly")
        monkey.save(self.db)
        monkey.rev = None
        monkey.name = "jess"
        self.db.put(monkey)


    def test_updates_from_dict(self):

        paul = Person.create(self.db, name="paul")
        dog1 = Dog.create(self.db, name="rufus", owner_id=paul.key, kennel_club_membership="123456")

        attrs = {
            "name":"joe",
            "kennel_club_membership": "9876543"
        }

        dog1.update(attrs)
        dog2 = Dog.get(self.db, dog1.key)
        self.assertTrue(dog2.kennel_club_membership == "9876543")



    # def test_uniqueness(self):
    #     self.clear_db()
    #     paul = Person(name="paul")
    #     self.db.put(paul)
    #     dog1 = Dog.create(self.db, name="rufus", owner_id=paul.key, kennel_club_membership="123456")
    #     dog2 = Dog.create(self.db, name="fly", owner_id=paul.key)
    #
    #     # raises if setting one value
    #     self.assertRaises(FamUniqueError, dog2.update, {"kennel_club_membership": "123456"})
    #     self.assertIsNone(dog2.kennel_club_membership)
    #
    #     # raises if creating a new one
    #     self.assertRaises(FamUniqueError, Dog.create, self.db, name="steve", owner_id=paul.key, kennel_club_membership="123456")
    #
    # def test_uniqueness_delete(self):
    #     self.clear_db()
    #     paul = Person(name="paul")
    #     self.db.put(paul)
    #     dog1 = Dog.create(self.db, name="rufus", owner_id=paul.key, kennel_club_membership="123456")
    #
    #     dog1.delete(self.db)
    #     dog2 = Dog.create(self.db, name="another", owner_id=paul.key, kennel_club_membership="123456")
    #
    #
    # def test_get_unique(self):
    #     self.clear_db()
    #     paul = Person(name="paul")
    #     self.db.put(paul)
    #     dog1 = Dog.create(self.db, name="rufus", owner_id=paul.key, kennel_club_membership="123456")
    #
    #     dog2 = Dog.get_unique_instance(self.db, "kennel_club_membership", "123456")
    #     self.assertIsNotNone(dog2)
    #     self.assertTrue(dog2.kennel_club_membership == "123456")
