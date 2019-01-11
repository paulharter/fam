import unittest
import json
import time
import os

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore, auth

from fam.exceptions import *
from fam.tests.models.test01 import GenericObject, Dog, Cat, Person, JackRussell, Monkey, Monarch, NAMESPACE

from fam.database import FirestoreWrapper
from fam.mapper import ClassMapper

from.config_local import *


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))


class TestDB(unittest.TestCase):


    def setUp(self):

        creds_path = os.path.join(ROOT_DIR, "secrets", "earth-rover-test-d241bce5266d.json")
        mapper = ClassMapper([Dog, Cat, Person, JackRussell, Monkey, Monarch])
        # self.db = FirestoreWrapper(mapper, creds_path)


        cred = credentials.Certificate(creds_path)
        app = firebase_admin.initialize_app(cred)
        uid = 'some-uid'

        additional_claims = {
            'premiumAccount': True
        }

        custom_token = auth.create_custom_token(uid, additional_claims)
        print(custom_token)
        print(PROJECT_NAME)
        print(API_KEY)
        firebase_admin.delete_app(app)

        self.db = FirestoreWrapper(mapper,
                                   None,
                                   project_id=PROJECT_NAME,
                                   custom_token=custom_token.decode("utf-8"),
                                   api_key=API_KEY,
                                   namespace=NAMESPACE

                                   )


    def test_make_an_object_and_refresh(self):
        dog = Dog.create(self.db, name="woofer")
        dog2 = Dog.get(self.db, dog.key)
        self.assertIsNotNone(dog2)
        time.sleep(1)

        self.db.refresh()
        dog3 = Dog.create(self.db, name="another")
        dog4 = Dog.get(self.db, dog3.key)
        self.assertIsNotNone(dog4)

