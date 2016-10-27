from copy import deepcopy
import unittest
from mock import patch

from fam.tests.models.test01 import GenericObject, Dog, Cat, Person, JackRussell, Monkey, Monarch, NAMESPACE

class CallbackBaseTests:

    class CallbackTests(unittest.TestCase):

        db = None

        def test_new_callbacks(self):

            with patch.object(Dog, 'pre_save_new_cb', return_value=None) as mock_pre_new:
                dog = Dog(name="woofer")
                self.db.put(dog)
                mock_pre_new.assert_called_once_with(self.db)

            with patch.object(Dog, 'post_save_new_cb', return_value=None) as mock_post_new:
                dog = Dog(name="woofer")
                self.db.put(dog)
                mock_post_new.assert_called_once_with(self.db)


        def test_update_callbacks(self):

            with patch.object(Dog, 'pre_save_update_cb', return_value=None) as mock_pre_update:
                dog = Dog(name="woofer")
                self.db.put(dog)
                old_properties = deepcopy(dog._properties)
                mock_pre_update.assert_not_called()
                dog.name = "fly"
                self.db.put(dog)
                mock_pre_update.assert_called_once_with(self.db, old_properties)

            with patch.object(Dog, 'post_save_update_cb', return_value=None) as mock_post_update:
                dog = Dog(name="woofer")
                self.db.put(dog)
                mock_post_update.assert_not_called()
                dog.name = "fly"
                self.db.put(dog)
                mock_post_update.assert_called_once_with(self.db)


        def test_delete_callbacks(self):

            with patch.object(Dog, 'pre_delete_cb', return_value=None) as mock_pre_delete:
                dog = Dog(name="woofer")
                self.db.put(dog)
                mock_pre_delete.assert_not_called()
                dog.name = "fly"
                self.db.delete(dog)
                mock_pre_delete.assert_called_once_with(self.db)


            with patch.object(Dog, 'post_delete_cb', return_value=None) as mock_post_delete:
                dog = Dog(name="woofer")
                self.db.put(dog)
                mock_post_delete.assert_not_called()
                dog.name = "fly"
                self.db.delete(dog)
                mock_post_delete.assert_called_once_with(self.db)