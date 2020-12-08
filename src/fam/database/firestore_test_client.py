from google import auth as google_auth
import grpc
from firebase_admin import firestore


class FirestoreTestClient(firestore.Client):
    """
    This is monkey patched version of the firestore database client that allows you to use credentials over an insecure
    local grpc channel. This lets you use authenticaed users with limited capabilites in tests

    DO NOT USE THIS IN PRODUCTION!!! THERE IS A REASON THAT GOOGLE DON'T ALLOW CREDENTIALS TO BE SENT OVER HTTP
    """


    def _firestore_api_helper(self, transport, client_class, client_module):

        if self._firestore_api_internal is None:
            composite_credentials = self.create_local_composite_credentials()

            if self._emulator_host is not None:
                channel = grpc._channel.Channel(self._emulator_host, (), composite_credentials._credentials, None)
            else:
                channel = transport.create_channel(
                    self._target,
                    credentials=self._credentials,
                    options={"grpc.keepalive_time_ms": 30000}.items(),
                )

            self._transport = transport(host=self._target, channel=channel)
            self._firestore_api_internal = client_class(
                transport=self._transport, client_options=self._client_options
            )
            client_module._client_info = self._client_info
        return self._firestore_api_internal


    def create_local_composite_credentials(self):

        credentials = google_auth.credentials.with_scopes_if_required(self._credentials, None)
        request = google_auth.transport.requests.Request()

        # Create the metadata plugin for inserting the authorization header.
        metadata_plugin = google_auth.transport.grpc.AuthMetadataPlugin(
            credentials, request
        )

        # Create a set of grpc.CallCredentials using the metadata plugin.
        google_auth_credentials = grpc.metadata_call_credentials(metadata_plugin)

        local_credentials = grpc.local_channel_credentials()

        # Combine the ssl credentials and the authorization credentials.
        return grpc.composite_channel_credentials(local_credentials, google_auth_credentials)