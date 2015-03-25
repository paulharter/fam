
from fam.utils import requests_shim as requests

from .couchdb import CouchDBWrapper, ResultWrapper

class SyncGatewayWrapper(CouchDBWrapper):

    ## the option stale=false forces the view to be indexed on read. Sync_gateway does not index on write!!
    VIEW_URL = "%s/%s/_design/%s/_view/%s?stale=false&key=\"%s\""

    def __init__(self, mapper, db_url, db_name):

        self.mapper = mapper

        self.db_name = db_name
        self.db_url = db_url

        url = "%s/%s" % (db_url, db_name)

        rsp = requests.get(url)


        if rsp.status_code == 404:
            raise Exception("Unknown database and you can't create them in the sync gateway")

    def _wrapper_from_view_json(self, as_json):
        return ResultWrapper.from_gateway_view_json(as_json)

    def changes(self, since=None, channels=None, limit=None):
        raise NotImplementedError("Haven't done changes for sync gateway yet")

    def sync_up(self):
        pass

    def sync_down(self):
        pass