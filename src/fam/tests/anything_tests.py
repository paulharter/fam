import os
from copy import deepcopy
import unittest
from fam.database import CouchDBWrapper
from fam.mapper import ClassMapper
from config import *
from fam.exceptions import *
from mock import MagicMock, patch

from fam.tests.models.test01 import GenericObject, Monster, Weapons, NAMESPACE

class CouchDBCallbackTests(unittest.TestCase):


    def setUp(self):
        mapper = ClassMapper([Monster])
        self.db = CouchDBWrapper(mapper, COUCHDB_URL, COUCHDB_NAME, reset=True)
        self.db.update_designs()


    def test_Object_field(self):

        weapons = Weapons("large", "hot", ["2", "2"])
        key = "a_monster"
        monster = Monster(key=key, weapons=weapons, name="bill")

        print monster.as_json()

        self.db.put(monster)

        got_monster = self.db.get(key)

        print got_monster.weapons

        self.assertTrue(isinstance(got_monster.weapons, Weapons))

