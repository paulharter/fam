from .couchdb import CouchDBWrapper
from .sync_gateway import SyncGatewayWrapper
from .firestore import FirestoreWrapper
try:
    from fam.database.couchbase_server import CouchbaseWrapper
except Exception as e:
    pass
    # print("failed to import couchbase wrapper", e)

from fam.utils.backoff import http_backoff

@http_backoff
def get_db(db_type,
           mapper,
           host,
           port=None,
           db_name="sync_gateway",
           https=False,
           username=None,
           password=None,
           backoff=False,
           **kwargs):

    if db_type == "sync_gateway":
        url = _get_url(host, 4984 if port is None else port, https, username, password)
        ## kwargs may inc auth_url
        return SyncGatewayWrapper(mapper, url, db_name, username=username, password=password, **kwargs)
    elif db_type == "couchdb":
        url = _get_url(host, 5984 if port is None else port, https, username, password)
        ## kwargs may inc reset, remote_url, continuous
        return CouchDBWrapper(mapper, url, db_name, **kwargs)
    # elif db_type == "couchbase":
    #     ## kwargs may inc read_only
    #     return CouchbaseWrapper(mapper, host, db_name, **kwargs)
    else:
        raise NotImplementedError("Can't make a database of type %s" % db_type)


def _get_url(host, port, https, username, password):
    if username is None:
        return "%s://%s:%s" % ("https" if https else "http", host, port)
    else:
        return "%s://%s:%s@%s:%s" % ("https" if https else "http", username, password, host, port)