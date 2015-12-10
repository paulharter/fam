import os
from copy import deepcopy
import unittest
from fam.database import CouchDBWrapper
from fam.mapper import ClassMapper
from config import *
from fam.exceptions import *
from mock import MagicMock, patch

from fam.tests.models.test01 import GenericObject, Dog, Cat, Person, JackRussell, Monkey, Monarch, NAMESPACE

class CouchDBCallbackTests(unittest.TestCase):


    def setUp(self):
        mapper = ClassMapper([Dog, Cat, Person, JackRussell, Monkey, Monarch])
        self.db = CouchDBWrapper(mapper, COUCHDB_URL, COUCHDB_NAME, reset=True)
        self.db.update_designs()


    def tearDown(self):
        pass


    def test_new_callbacks(self):

        with patch.object(Dog, 'pre_save_new_cb', return_value=None) as mock_pre_new:
            dog = Dog(name="woofer")
            self.db.put(dog)
            mock_pre_new.assert_called_once_with()

        with patch.object(Dog, 'post_save_new_cb', return_value=None) as mock_post_new:
            dog = Dog(name="woofer")
            self.db.put(dog)
            mock_post_new.assert_called_once_with()


    def test_update_callbacks(self):

        with patch.object(Dog, 'pre_save_update_cb', return_value=None) as mock_pre_update:
            dog = Dog(name="woofer")
            old_properties = deepcopy(dog._properties)
            self.db.put(dog)
            mock_pre_update.assert_not_called()
            dog.name = "fly"
            self.db.put(dog)
            mock_pre_update.assert_called_once_with(old_properties)

        with patch.object(Dog, 'post_save_update_cb', return_value=None) as mock_post_update:
            dog = Dog(name="woofer")
            self.db.put(dog)
            mock_post_update.assert_not_called()
            dog.name = "fly"
            self.db.put(dog)
            mock_post_update.assert_called_once()


    def test_delete_callbacks(self):

        with patch.object(Dog, 'pre_delete_cb', return_value=None) as mock_pre_delete:
            dog = Dog(name="woofer")
            self.db.put(dog)
            mock_pre_delete.assert_not_called()
            dog.name = "fly"
            self.db.delete(dog)
            mock_pre_delete.assert_called_once()


        with patch.object(Dog, 'post_delete_cb', return_value=None) as mock_post_delete:
            dog = Dog(name="woofer")
            self.db.put(dog)
            mock_post_delete.assert_not_called()
            dog.name = "fly"
            self.db.delete(dog)
            mock_post_delete.assert_called_once()