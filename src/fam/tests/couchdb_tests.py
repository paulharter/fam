import os
import unittest
from fam.database import CouchDBWrapper
from fam.mapper import ClassMapper
from config import *
from fam.exceptions import *

from fam.tests.models.test01 import GenericObject, Dog, Cat, Person, JackRussell, Monkey, NAMESPACE

class CouchDBModelTests(unittest.TestCase):

    def setUp(self):
        mapper = ClassMapper([Dog, Cat, Person, JackRussell, Monkey])
        self.db = CouchDBWrapper(mapper, COUCHDB_URL, COUCHDB_NAME, reset=True)
        self.db.update_designs()

    def tearDown(self):
        pass

   # Test the app
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


    def test_make_an_sub_object(self):
        jack = JackRussell()
        self.assertEqual(jack.talk(), "Yap")
        jack.name = "jack"
        jack.age = 12


    def test_make_an_object_saved(self):
        dog = Dog(name="woofer")
        dog.save(self.db)
        self.assertEqual(dog.namespace, NAMESPACE)
        self.assertEqual(dog.type, "dog")
        self.assertEqual(dog.name, "woofer")
        self.assertEqual(dog.__class__, Dog)
        self.assertNotEqual(dog.key, None)

    def test_make_an_object_double_dispatch_saved(self):
        dog = Dog(name="woofer")
        self.db.put(dog)
        self.assertEqual(dog.namespace, NAMESPACE)
        self.assertEqual(dog.type, "dog")
        self.assertEqual(dog.name, "woofer")
        self.assertEqual(dog.__class__, Dog)
        self.assertNotEqual(dog.key, None)

    def test_make_an_object_saved_cas(self):
        paul = Person(name="paul")
        paul.save(self.db)
        cat = Cat(name="whiskers", owner_id=paul.key, legs=2)
        cat.save(self.db)
        self.assertEqual(cat.namespace, NAMESPACE)
        self.assertEqual(cat.type, "cat")
        self.assertNotEqual(cat.rev, None)


    def test_get_cat(self):
        paul = Person(name="paul")
        paul.save(self.db)
        cat = Cat(name="whiskers", owner_id=paul.key, legs=2)
        cat.save(self.db)
        another = Cat.get(self.db, cat.key)
        self.assertEqual(cat, another)


    def test_ref_to(self):
        paul = Person(name="paul")
        paul.save(self.db)
        cat = Cat(name="whiskers", owner_id=paul.key, legs=2)
        cat.save(self.db)
        self.assertEqual(cat.owner, paul)
        self.assertEqual(cat.owner.name, "paul")


    def test_ref_to_with_object(self):
        paul = Person(name="paul")
        self.db.put(paul)
        cat = Cat(name="whiskers", owner=paul, legs=2)
        cat.save(self.db)
        self.assertEqual(cat.owner, paul)
        self.assertEqual(cat.owner.name, "paul")
        catback = self.db.get(cat.key)
        self.assertEqual(cat, catback)



    def test_ref_from(self):
        paul = Person(name="paul")
        paul.save(self.db)
        cat = Cat(name="whiskers", owner_id=paul.key, legs=2)
        cat.save(self.db)
        cat2 = Cat(name="puss", owner_id=paul.key, legs=2)
        cat2.save(self.db)
        self.assertEqual(len(paul.cats), 2)
        self.assertTrue(paul.cats[0] == cat or paul.cats[1] == cat)


    def test_delete_cat_dd(self):
        paul = Person(name="paul")
        self.db.put(paul)
        cat = Cat(name="whiskers", owner_id=paul.key, legs=2)
        self.db.put(cat)
        key = cat.key
        another = self.db.get(cat.key)
        self.assertEqual(cat, another)
        self.db.delete(cat)
        revivedcat = self.db.get(key)
        self.assertEqual(revivedcat, None)


    def test_delete_dog_to_refs(self):
        paul = Person(name="paul")
        paul.save(self.db)
        dog = Dog(name="rufus", owner_id=paul.key)
        dog.save(self.db)
        key = dog.key
        dog2 = Dog(name="fly", owner_id=paul.key)
        dog2.save(self.db)
        self.assertNotEqual(dog2.owner, None)
        key = paul.key
        dog.delete(self.db)
        revivedpaul = self.db.get(key)
        self.assertEqual(revivedpaul, None)
        refresheddog2 = Dog.get(self.db, dog2.key)
        self.assertEqual(refresheddog2.owner, None)


    def test_delete_cat_refs(self):
        paul = Person(name="paul")
        paul.save(self.db)
        cat = Cat(name="whiskers", owner_id=paul.key, legs=2)
        cat.save(self.db)
        key = cat.key
        cat2 = Cat(name="puss", owner_id=paul.key, legs=2)
        cat2.save(self.db)
        revivedcat1 = self.db.get(key)
        self.assertNotEqual(revivedcat1, None)
        paul.delete(self.db)
        revivedcat2 = self.db.get(key)
        self.assertEqual(revivedcat2, None)


    def test_delete_dog_refs(self):
        paul = Person(name="paul")
        paul.save(self.db)
        dog = Dog(name="rufus", owner_id=paul.key)
        dog.save(self.db)
        key = dog.key
        dog2 = Dog(name="fly", owner_id=paul.key)
        dog2.save(self.db)
        reviveddog1 = self.db.get(key)
        self.assertNotEqual(reviveddog1, None)
        paul.delete(self.db)
        reviveddog2 = self.db.get(key)
        self.assertNotEqual(reviveddog2, None)


    def test_update_cat(self):
        paul = Person(name="paul")
        paul.save(self.db)
        cat = Cat(name="whiskers", owner_id=paul.key, legs=2)
        cat.save(self.db)
        cat.name = "blackie"
        cat.save(self.db)
        self.assertEqual(cat.name, "blackie")
        self.assertEqual(cat._properties["name"], "blackie")
        self.assertFalse("name" in cat.__dict__.keys())


    def test_update_cat_fails(self):
        paul = Person(name="paul")
        paul.save(self.db)
        cat = Cat(name="whiskers", owner_id=paul.key, legs=2)
        cat.save(self.db)
        cat.colour = "black"
        cat.save(self.db)
        def change_colour():
            cat.colour = "white"
        self.assertRaises(FamValidationError, change_colour)


    def setcatfood(self):
        self.cat.food = "biscuits"


    def test_update_catfood(self):
        paul = Person(name="paul")
        paul.save(self.db)
        cat = Cat(name="whiskers", owner_id=paul.key, legs=2)
        cat.save(self.db)
        self.assertRaises(Exception, self.setcatfood)


    def test_update_dogfood(self):
        dog = Dog(name="fly")
        dog.food = "biscuits"
        dog.save(self.db)


    def test_all(self):
        dog = Dog(name="fly")
        dog.save(self.db)
        all = Dog.all(self.db)
        self.assertEqual(len(all), 1)


    def test_changes(self):
        dog = Dog(name="fly")
        dog.save(self.db)
        all = Dog.all(self.db)
        self.assertEqual(len(all), 1)
        last_seq, objects = GenericObject.changes(self.db)
        dog2 = Dog(name="shep")
        dog2.save(self.db)
        last_seq, objects = GenericObject.changes(self.db, since=last_seq)
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], dog2)


    def test_changes_limit(self):
        dog = Dog(name="fly")
        dog.save(self.db)
        all = Dog.all(self.db)
        self.assertEqual(len(all), 1)
        last_seq, objects = GenericObject.changes(self.db)
        dog2 = Dog(name="shep")
        dog2.save(self.db)
        dog3 = Dog(name="bob")
        dog3.save(self.db)
        last_seq, objects = GenericObject.changes(self.db, since=last_seq, limit=1)
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], dog2)
        last_seq, objects = GenericObject.changes(self.db, since=last_seq, limit=1)
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], dog3)


    def test_update_fails_without_rev(self):
        dog = Dog(name="fly")
        dog.save(self.db)
        dog.rev = None
        dog.name = "jess"
        self.assertRaises(FamResourceConflict, self.db.put, dog)


    def test_update_works_without_rev(self):
        monkey = Monkey(name="fly")
        monkey.save(self.db)
        monkey.rev = None
        monkey.name = "jess"
        self.db.put(monkey)


class CouchDBModelTests2(unittest.TestCase):

    # this test that refs whos name doesnt end with _id fail
    def test_misnamed_ref_to_fails(self):

        def duff_import():
            from fam.tests.models import test02
            print test02

        self.assertRaises(FamError, duff_import)