
import unittest
from fam.tests.models.test01 import Monster, Weapons

class AnythingBaseTests:

    class AnythingTests(unittest.TestCase):

        db = None

        def test_Object_field(self):

            weapons = Weapons("large", "hot", ["2", "2"])
            key = "a_monster"
            monster = Monster(key=key, weapons=weapons, name="bill")

            print monster.as_json()

            self.db.put(monster)

            got_monster = self.db.get(key)

            print got_monster.weapons

            self.assertTrue(isinstance(got_monster.weapons, Weapons))

