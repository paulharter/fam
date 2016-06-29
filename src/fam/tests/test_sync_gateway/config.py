import sys

SYNC_GATEWAY_HOST = "localhost"
SYNC_GATEWAY_ADMIN_HOST = "localhost"
SYNC_GATEWAY_PORT = "4984"
SYNC_GATEWAY_ADMIN_PORT = "4985"
SYNC_GATEWAY_NAME = "sync_gateway"

if sys.platform.startswith('linux'):
    SYNC_GATEWAY_PATH = "/opt/couchbase-sync-gateway/bin/sync_gateway"
else:
    SYNC_GATEWAY_PATH = "sync_gateway"





