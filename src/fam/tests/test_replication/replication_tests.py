import unittest
import time
import sys
import subprocess
import requests
import json
from fam.utils import couchbase_utils

from fam.tests.models.test01 import Dog, Cat, Person, JackRussell, Monarch, NAMESPACE
from fam.mapper import ClassMapper

from fam.database import CouchDBWrapper, SyncGatewayWrapper




class ReplicationTests(unittest.TestCase):

        def setUp(self):

            mapper = ClassMapper([Dog, Cat, Person, JackRussell, Monarch])
            self.db_a = SyncGatewayWrapper(mapper,  "http://localhost:5985" , "sync_gateway")
            # self.db_b = SyncGatewayWrapper(mapper, "http://localhost:4985", "sync_gateway")


        # def test_put_some_dogs(self):
        #     dog_b1 = Dog(key="dog_b1", name="b1", channels=["shared_docs"])
        #     self.db_b.put(dog_b1)
        #     dog_b2 = Dog(key="dog_b2", name="b2", channels=["shared_docs"])
        #     self.db_b.put(dog_b2)
        #     dog_b3 = Dog(key="dog_b3", name="b3", channels=[])
        #     self.db_b.put(dog_b3)
        #
        #
        #     dog_a1 = Dog(key="dog_a1", name="a1", channels=["shared_docs"])
        #     self.db_a.put(dog_a1)
        #     dog_a2 = Dog(key="dog_a2", name="a2", channels=["shared_docs"])
        #     self.db_a.put(dog_a2)
        #     dog_a3 = Dog(key="dog_a3", name="a3", channels=[])
        #     self.db_a.put(dog_a3)
        #     dog_a4 = Dog(key="dog_a4", name="a4", channels=[])
        #     self.db_a.put(dog_a4)
        #     dog_a5 = Dog(key="dog_a5", name="a5", channels=[])
        #     self.db_a.put(dog_a5)
        #     dog_a6 = Dog(key="dog_a6", name="a6", channels=[])
        #     self.db_a.put(dog_a6)
        #
        #
        #     """
        #     a has a1-6 b1-2 seq 9
        #     b has a1-2 b1-3 seq 6 8556f2328ad7a3e626a5d4498a122ab7f33824e3 last 5
        #
        #
        #
        #     --- flush
        #
        #     a has a1-2 b1-2 seq 5
        #
        #
        #
        #
        #     """




        #
        #
        def test_put_some_more_dogs(self):

            dog_a7 = Dog(key="dog_a7", name="a7", channels=["shared_docs"])
            self.db_a.put(dog_a7)

        #
        #     """
        #
        #     do this offline
        #
        #     a a7 seq 2
        #
        #     turn online
        #
        #     a a1 a2 a7 b1 b2 seq 6
        #     b has a1-2 b1-3 seq 6 81ab002d844950713c06b88d404ef4571cefb04e last 6
        #
        #     """



        # #
        # def test_put_some_more_dogs(self):
        #
        #     dog_a8 = Dog(key="dog_a8", name="a8", channels=["shared_docs"])
        #     self.db_a.put(dog_a8)
