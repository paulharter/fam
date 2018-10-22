import unittest
import json
import time
import os

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

import fam
from fam.exceptions import *
from fam.tests.models.test01 import GenericObject, Dog, Cat, Person, JackRussell, Monkey, Monarch, NAMESPACE

from fam.database import FirestoreWrapper
from fam.mapper import ClassMapper

SECRETS_DIR = os.path.join(os.path.dirname(fam.__file__), "tests", "secrets")


class TestDB(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        creds_path = os.path.join(SECRETS_DIR, "earth-rover-test-d241bce5266d.json")
        mapper = ClassMapper([Dog, Cat, Person, JackRussell, Monkey, Monarch])
        cls.db = FirestoreWrapper(mapper, creds_path, namespace=NAMESPACE)
        cls.clear_db()


    @classmethod
    def clear_db(cls):
        cls.db.delete_all("dog")
        cls.db.delete_all("cat")
        cls.db.delete_all("person")
        cls.db.delete_all("jackrussell")
        cls.db.delete_all("monkey")
        cls.db.delete_all("dog__kennel_club_membership")


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

        got = Cat.get(self.db, cat.key)

        self.assertEqual(got.name, "blackie")


