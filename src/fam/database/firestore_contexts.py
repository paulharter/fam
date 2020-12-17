from google.api_core import gapic_v1
from .firestore import FirestoreWrapper
from fam.exceptions import FamTransactionError

class FirestoreBatchContext(FirestoreWrapper):

    def __init__(self, wrapper, retry=gapic_v1.method.DEFAULT, timeout=None):

        self.batch = self._get_batch(wrapper.db)
        self.wrapper = wrapper
        self.retry = retry
        self.timeout = timeout

        self.mapper = wrapper.mapper
        self.validator = wrapper.validator
        self.read_only = wrapper.read_only
        self.api_key = wrapper.api_key
        self.namespace = wrapper.namespace
        self.expires = wrapper.expires
        self.data_adapter = wrapper.data_adapter
        self.creds = wrapper.creds
        self.db = wrapper.db
        self.app = wrapper.app
        self.user = wrapper.user
        self.expires = wrapper.expires

    def _get_batch(self, client):
        return client.batch()

    def _set_doc_ref(self, doc_ref, value):
        self.batch.set(doc_ref, value)

    def _update_doc_ref(self, doc_ref, value):
        self.batch.update(doc_ref, value)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.results = self.batch.commit(self.retry, self.timeout)


# class FirestoreTransactionContext(FirestoreBatchContext):
#
#     def __init__(self, wrapper, retry=gapic_v1.method.DEFAULT, timeout=None, max_attempts=5, read_only=False):
#
#         self.max_attempts = max_attempts
#         self.firestore_read_only = read_only
#         super().__init__(wrapper, retry, timeout)
#         self.transaction = self.batch
#
#     def _get_batch(self, client):
#         return client.transaction(max_attempts=self.max_attempts,
#                                   read_only=self.firestore_read_only)
#
#     def _stream_doc_ref(self, doc_ref):
#         return doc_ref.stream(transaction=self.transaction)
#
#     def _get_doc_ref(self, doc_ref):
#         return doc_ref.get(transaction=self.transaction)
#
#     def _create_unique_field_docs(self, type_name, key, value, unique_field_names, transaction):
#         raise FamTransactionError(
#             "You can't set unique fields inside a batch or transaction because I haven't thought hard enough about nested transactions")
#
#     def _clear_uniqueness_typed(self, key, type_name, transaction):
#         raise FamTransactionError(
#             "You can't delete an object with unique fields inside a batch or transaction because I haven't thought hard enough about nested transactions")