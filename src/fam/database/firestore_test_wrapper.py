from firebase_admin import auth
from fam.database.firestore import FirestoreWrapper
from fam.database.firestore_test_client import FirestoreTestClient

class FirestoreTestWrapper(FirestoreWrapper):

    def __init__(self, mapper, app_name, uid, project_id, api_key, namespace, additional_claims=None):

        token = auth.create_custom_token(uid, additional_claims).decode("utf-8")

        super().__init__(mapper,
                         None,
                         project_id=project_id,
                         custom_token=token,
                         api_key=api_key,
                         name=app_name,
                         namespace=namespace
                         )

        credentials = self.app.credential.get_credential()
        test_client = FirestoreTestClient(credentials=credentials, project=project_id)
        self.db = test_client
