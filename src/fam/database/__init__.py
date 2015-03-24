try:
    from .couchbase_server import CouchbaseWrapper
except ImportError:
    print "Couldnt import CouchbaseWrapper"

from .couchdb import CouchDBWrapper
from .sync_gateway import SyncGatewayWrapper