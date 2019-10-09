
import unittest
import shutil
import time
import os
import datetime

from fam.mapper import ClassMapper
from fam.database import FirestoreWrapper
from fam.schema.validator import ModelValidator

from fam.schema.mutator import FamMutator

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(THIS_DIR, "data")
SCHEMATA_DIR = os.path.join(DATA_PATH, "schemata")

from fam.tests.test_mutation.models.test01 import Dog, Cat, JackRussell, Person, Monkey
from fam.tests.test_firestore.config import CREDS

class MutationTests(unittest.TestCase):


    def clear_db(self):
        self.db.delete_all("dog")
        self.db.delete_all("cat")
        self.db.delete_all("jackrussell")
        self.db.delete_all("person")
        self.db.delete_all("monkey")


    def setUp(self):

        if os.path.exists(SCHEMATA_DIR):
            shutil.rmtree(SCHEMATA_DIR)

        mapper = ClassMapper([Dog, Cat, JackRussell, Person, Monkey])
        self.mutator = FamMutator(mapper, DATA_PATH)
        self.db = FirestoreWrapper(mapper, CREDS, validator=self.mutator, namespace="http://glowinthedark.co.uk/test")

        if self.db.db.project != "orcast-test":
            raise Exception("wrong db: " % self.db.db.project)




    def _update_mutation(self, dst, schema_id):

        src_file = os.path.join(DATA_PATH, "dog_mutation.py")
        with open(src_file, "r") as f:
            txt = f.read()

        txt = txt.replace("TEMPLATE_SCHEMA_ID", schema_id)
        os.remove(dst)
        with open(dst, "w") as f:
            f.write(txt)

    def _add_changes(self):

        from fam.tests.test_mutation.models.test02 import Dog, Cat, JackRussell, Person, Monkey
        self.mapper = ClassMapper([Dog, Cat, JackRussell, Person, Monkey])
        self.db.mapper = self.mapper
        self.mutator = FamMutator(self.mapper, DATA_PATH)
        self.mutator.db = self.db


    def test_creates_schemata(self):

        self.mutator.update_ref_schemata()
        self.assertEqual(len(self.mutator.changes), 5)

        for namespace, type_name, timestamp in self.mutator.changes:
            schema_dir = self.mutator._schema_path(namespace, type_name, timestamp)
            schema_filepath = os.path.join(schema_dir, "schema.json")
            self.assertTrue(os.path.exists(schema_filepath))


    def test_creates_mutations(self):

        self.mutator.update_ref_schemata()
        self.assertEqual(len(self.mutator.changes), 5)

        self._add_changes()

        self.mutator.update_ref_schemata()
        self.assertEqual(len(self.mutator.changes), 2)


        for namespace, type_name, timestamp in self.mutator.changes:
            schema_dir = self.mutator._schema_path(namespace, type_name, timestamp)
            mutation_filepath = os.path.join(schema_dir, "mutation.py")
            self.assertTrue(os.path.exists(mutation_filepath))


    def test_index_mutations(self):

        self.mutator.update_ref_schemata()
        self.assertEqual(len(self.mutator.changes), 5)

        self._add_changes()
        self.mutator.update_ref_schemata()
        self.assertEqual(len(self.mutator.changes), 2)

        self.mutator._index_all_mutations()

        self.assertEqual(len(self.mutator.mutation_histories), 5)
        self.assertEqual(len(self.mutator.mutation_histories[("http://glowinthedark.co.uk/test", "dog")]), 1)
        self.assertEqual(len(self.mutator.mutation_histories[("http://glowinthedark.co.uk/test", "cat")]), 0)


    def test_find_not_implemented(self):
        self.mutator.update_ref_schemata()
        self._add_changes()
        self.mutator.update_ref_schemata()
        self.assertRaises(NotImplementedError, self.mutator.check_not_implemented_mutations)


    def test_update_mutations(self):

        self.mutator.update_ref_schemata()
        self._add_changes()
        self.mutator.update_ref_schemata()
        self.assertRaises(NotImplementedError, self.mutator.check_not_implemented_mutations)

        for namespace, type_name, timestamp in self.mutator.changes:
            schema_dir = self.mutator._schema_path(namespace, type_name, timestamp)
            mutation_filepath = os.path.join(schema_dir, "mutation.py")
            schema_id = self.mutator.ref_schemas[(namespace, type_name)]["id"]
            self._update_mutation(mutation_filepath, schema_id)

        self.mutator.all_mutations = {}
        self.mutator.check_not_implemented_mutations()


    def test_mutate(self):
        self.clear_db()

        self.mutator.update_ref_schemata()
        namespace = "http://glowinthedark.co.uk/test"

        first_dog_schema = self.mutator.ref_schemas[(namespace, "dog")]["id"]

        dog = Dog(name="fly")
        self.db.put(dog)


        got_dog = Dog.get(self.db, dog.key)

        self.assertEqual(first_dog_schema, got_dog.schema)

        self._add_changes()
        self.mutator.update_ref_schemata()
        self.assertRaises(NotImplementedError, self.mutator.check_not_implemented_mutations)

        # fix the mutations
        for namespace, type_name, timestamp in self.mutator.changes:
            schema_dir = self.mutator._schema_path(namespace, type_name, timestamp)
            mutation_filepath = os.path.join(schema_dir, "mutation.py")
            schema_id = self.mutator.ref_schemas[(namespace, type_name)]["id"]
            self._update_mutation(mutation_filepath, schema_id)

        self.mutator.all_mutations = {}
        self.mutator.check_not_implemented_mutations()

        second_dog_schema = self.mutator.ref_schemas[(namespace, "dog")]["id"]

        self.assertNotEqual(first_dog_schema, second_dog_schema)

        dog_key = dog.key
        time.sleep(1)

        gotDog = Dog.get(self.db, dog_key)

        self.assertEqual(first_dog_schema, gotDog.schema)
        self.mutator.mutate()
        gotDog = Dog.get(self.db, dog_key)


        self.assertEqual(second_dog_schema, gotDog.schema)
        self.assertEqual("red", gotDog.colour)

        # remove the schema to check lazy load
        del self.mutator.reference_store[second_dog_schema]

        gotDog.colour = "blue"
        self.db.put(gotDog)

        # some tests of the indexing

        namespace, type_name, timestamp = self.mutator._namespace_typename_timestamp_from_schema_id(second_dog_schema)

        dogs = list(self.mutator._iter_of_of_date_obj(namespace, type_name, timestamp))
        self.assertTrue(len(dogs) == 0)

        cats = list(self.mutator._iter_of_of_date_obj(namespace, "cats", timestamp))
        self.assertTrue(len(cats) == 0)

        zebra = list(self.mutator._iter_of_of_date_obj(namespace, "zebra", timestamp))
        self.assertTrue(len(zebra) == 0)

        # move timestamp later
        dt = self.mutator._datetime_from_timestamp(timestamp)
        later_dt = dt + datetime.timedelta(seconds=1)
        later_timestamp = self.mutator._timestamp_from_datetime(later_dt)
        dogs = list(self.mutator._iter_of_of_date_obj(namespace, type_name, later_timestamp))
        self.assertTrue(len(dogs) == 1)

        # move timestamp earlier
        dt = self.mutator._datetime_from_timestamp(timestamp)
        earlier_dt = dt + datetime.timedelta(seconds=-1)
        earlier_timestamp = self.mutator._timestamp_from_datetime(earlier_dt)

        dogs = list(self.mutator._iter_of_of_date_obj(namespace, type_name, earlier_timestamp))
        self.assertTrue(len(dogs) == 0)



    def test_mutate_typed(self):
        self.clear_db()

        self.mutator.update_ref_schemata()
        namespace = "http://glowinthedark.co.uk/test"

        first_dog_schema = self.mutator.ref_schemas[(namespace, "dog")]["id"]

        dog = Dog(name="fly")
        self.db.put(dog)

        got_dog = Dog.get(self.db, dog.key)

        self.assertEqual(first_dog_schema, got_dog.schema)

        self._add_changes()
        self.mutator.update_ref_schemata()
        self.assertRaises(NotImplementedError, self.mutator.check_not_implemented_mutations)

        # fix the mutations
        for namespace, type_name, timestamp in self.mutator.changes:
            schema_dir = self.mutator._schema_path(namespace, type_name, timestamp)
            mutation_filepath = os.path.join(schema_dir, "mutation.py")
            schema_id = self.mutator.ref_schemas[(namespace, type_name)]["id"]
            self._update_mutation(mutation_filepath, schema_id)

        self.mutator.all_mutations = {}
        self.mutator.check_not_implemented_mutations()

        second_dog_schema = self.mutator.ref_schemas[(namespace, "dog")]["id"]

        self.assertNotEqual(first_dog_schema, second_dog_schema)

        dog_key = dog.key
        time.sleep(1)

        gotDog = Dog.get(self.db, dog_key)

        self.assertEqual(first_dog_schema, gotDog.schema)
        self.mutator.mutate()
        gotDog = Dog.get(self.db, dog_key)


        self.assertEqual(second_dog_schema, gotDog.schema)
        self.assertEqual("red", gotDog.colour)

        # remove the schema to check lazy load
        del self.mutator.reference_store[second_dog_schema]

        gotDog.colour = "blue"
        self.db.put(gotDog)

        # some tests of the indexing

        namespace, type_name, timestamp = self.mutator._namespace_typename_timestamp_from_schema_id(second_dog_schema)

        dogs = list(self.mutator._iter_of_of_date_obj(namespace, type_name, timestamp))
        self.assertTrue(len(dogs) == 0)

        cats = list(self.mutator._iter_of_of_date_obj(namespace, "cats", timestamp))
        self.assertTrue(len(cats) == 0)

        zebra = list(self.mutator._iter_of_of_date_obj(namespace, "zebra", timestamp))
        self.assertTrue(len(zebra) == 0)

        # move timestamp later
        dt = self.mutator._datetime_from_timestamp(timestamp)
        later_dt = dt + datetime.timedelta(seconds=1)
        later_timestamp = self.mutator._timestamp_from_datetime(later_dt)
        dogs = list(self.mutator._iter_of_of_date_obj(namespace, type_name, later_timestamp))
        self.assertTrue(len(dogs) == 1)

        # move timestamp earlier
        dt = self.mutator._datetime_from_timestamp(timestamp)
        earlier_dt = dt + datetime.timedelta(seconds=-1)
        earlier_timestamp = self.mutator._timestamp_from_datetime(earlier_dt)

        dogs = list(self.mutator._iter_of_of_date_obj(namespace, type_name, earlier_timestamp))
        self.assertTrue(len(dogs) == 0)


