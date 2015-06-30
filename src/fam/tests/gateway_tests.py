import os
import unittest
import time

from fam.database import SyncGatewayWrapper
from fam.blud import UpdateException
from config import *
from fam.tests.models.test01 import GenericObject, Dog, Cat, Person, JackRussell, NAMESPACE
from fam.mapper import ClassMapper

class CouchDBModelTests(unittest.TestCase):

    def setUp(self):

        mapper = ClassMapper([Dog, Cat, Person, JackRussell])
        url = "http://%s:%s" % (SYNC_GATEWAY_HOST, SYNC_GATEWAY_ADMIN_PORT)
        self.db = SyncGatewayWrapper(mapper, url, SYNC_GATEWAY_NAME)
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


    def test_make_an_object_saved_cas(self):
        cat = Cat(name="whiskers")
        cat.save(self.db)
        self.assertEqual(cat.namespace, NAMESPACE)
        self.assertEqual(cat.type, "cat")
        self.assertNotEqual(cat.cas, None)


    def test_get_cat(self):
        cat = Cat(name="whiskers")
        cat.save(self.db)
        another = Cat.get(self.db, cat.key)
        self.assertEqual(cat, another)


    def test_ref_to(self):
        paul = Person(name="paul")
        paul.save(self.db)
        cat = Cat(name="whiskers", owner_id=paul.key)
        cat.save(self.db)
        self.assertEqual(cat.owner, paul)
        self.assertEqual(cat.owner.name, "paul")



    def test_ref_from(self):
        paul = Person(name="paul")
        paul.save(self.db)
        cat = Cat(name="whiskers", owner_id=paul.key)
        cat.save(self.db)
        cat2 = Cat(name="puss", owner_id=paul.key)
        cat2.save(self.db)
        self.assertEqual(len(paul.cats), 2)
        self.assertTrue(paul.cats[0] == cat or paul.cats[1] == cat)


    def test_delete_cat(self):
        cat = Cat(name="whiskers")
        cat.save(self.db)
        key = cat.key
        another = Cat.get(self.db, cat.key)
        self.assertEqual(cat, another)
        cat.delete(self.db)
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
        cat = Cat(name="whiskers", owner_id=paul.key)
        cat.save(self.db)
        key = cat.key
        cat2 = Cat(name="puss", owner_id=paul.key)
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
        cat = Cat(name="whiskers")
        cat.save(self.db)
        cat.name = "blackie"
        cat.save(self.db)
        self.assertEqual(cat.name, "blackie")
        self.assertEqual(cat._properties["name"], "blackie")
        self.assertFalse("name" in cat.__dict__.keys())


    def setcatfood(self):
        self.cat.food = "biscuits"


    def test_update_catfood(self):
        self.cat = Cat(name="whiskers")
        self.cat.save(self.db)
        self.assertRaises(Exception, self.setcatfood)


    def test_update_dogfood(self):
        dog = Dog(name="fly")
        dog.food = "biscuits"
        dog.save(self.db)

    # def test_all(self):
    #     dog = Dog(name="fly")
    #     dog.save(self.db)
    #     all = Dog.all(self.db)
    #     self.assertEqual(len(all), 1)


    def test_update_fails(self):
        dog = Dog(key="dog::fly", name="fly")
        dog.save(self.db)
        dog = Dog(key="dog::fly", name="jim")
        self.assertRaises(UpdateException, dog.save, self.db)


    def test_update_and_changes(self):
        dog = Dog(key="dog::fly", name="fly")
        print dog
        dog.save(self.db)
        dog.delete(self.db)
        dog = Dog(key="dog::fly", name="fly")
        dog.save(self.db)

        dog2 = Dog(key="dog::jim", name="jim")
        dog2.save(self.db)

        all = Dog.all(self.db)

        self.assertEqual(len(all), 2)



        #
        #
        # all = Dog.all(self.db)
        # self.assertEqual(len(all), 2)
        #
        # last_seq, objects = GenericObject.changes(self.db)
        #
        # self.assertEqual(len(objects), 2)




    #
    # def test_changes_limit(self):
    #     dog = Dog(name="fly")
    #     dog.save(self.db)
    #     all = Dog.all(self.db)
    #     self.assertEqual(len(all), 1)
    #     last_seq, objects = GenericObject.changes(self.db)
    #     dog2 = Dog(name="shep")
    #     dog2.save(self.db)
    #     dog3 = Dog(name="bob")
    #     dog3.save(self.db)
    #     last_seq, objects = GenericObject.changes(self.db, since=last_seq, limit=1)
    #     self.assertEqual(len(objects), 1)
    #     self.assertEqual(objects[0], dog2)
    #     last_seq, objects = GenericObject.changes(self.db, since=last_seq, limit=1)
    #     self.assertEqual(len(objects), 1)
    #     self.assertEqual(objects[0], dog3)