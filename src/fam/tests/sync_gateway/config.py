import sys


# COUCHDB_SYNC_URL = "http://http://192.168.99.100/:4984"
# COUCHDB_SYNC_ADMIN_URL = "http://http://192.168.99.100/:4985"

# COUCHBASE_LOCAL_URL = "http://localhost:8091"
# COUCHBASE_HOST = "localhost"
# COUCHBASE_PORT = "8091"
# COUCHBASE_ADMIN = "paul"
# COUCHBASE_ADMIN_PASSWORD = "mouse99"

SYNC_GATEWAY_HOST = "192.168.99.100"
SYNC_GATEWAY_PORT = "4984"
SYNC_GATEWAY_ADMIN_PORT = "4985"
SYNC_GATEWAY_NAME = "sync_gateway"

if sys.platform.startswith('linux'):
    SYNC_GATEWAY_PATH = "/opt/couchbase-sync-gateway/bin/sync_gateway"
else:
    SYNC_GATEWAY_PATH = "sync_gateway"





