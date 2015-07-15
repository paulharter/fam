
# removed until I fix this wrapper
# try:
#     from .couchbase_server import CouchbaseWrapper
# except ImportError, e:
#    print "Couldnt import CouchbaseWrapper: %s" % e

from .couchdb import CouchDBWrapper
from .sync_gateway import SyncGatewayWrapper