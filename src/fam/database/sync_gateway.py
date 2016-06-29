

from base64 import b64encode


from fam.utils import requests_shim as requests

from .couchdb import CouchDBWrapper, ResultWrapper

class SyncGatewayWrapper(CouchDBWrapper):

    ## the option stale=false forces the view to be indexed on read. Sync_gateway does not index on write!!
    VIEW_URL = "%s/%s/_design/%s/_view/%s?stale=false&key=\"%s\""

    # this function is different from the base version in that it adds the rev from the meta into the doc
    FOREIGN_KEY_MAP_STRING = '''function(doc, meta) {
    var resources = %s;
    if (resources.indexOf(doc.type) != -1 && doc.namespace == \"%s\"){
        doc._rev = meta.rev;
        emit(doc.%s, doc);
    }
}'''


    def __init__(self, mapper, db_url, db_name, auth_url=None, username=None, password=None):

        self.mapper = mapper
        self.validator = mapper.validator

        self.db_name = db_name
        self.db_url = db_url
        self.username = username
        self.password = password
        self.auth_url = auth_url
        self.session = requests.Session()

        url = "%s/%s" % (db_url, db_name)
        rsp = self.session.get(url)

        self.cookies = {}

        if rsp.status_code == 404:
            raise Exception("Unknown database and you can't create them in the sync gateway")


    def authenticate(self):
        if self.username is None:
            raise Exception("failed to authenticate no username")

        userAndPass = b64encode(b"paul:bumbum").decode("ascii")
        headers = { 'Authorization' : 'Basic %s' %  userAndPass }

        rsp = self.session.get(self.auth_url, headers=headers)
        if rsp.status_code == 200:
            self.cookies = rsp.cookies
        else:
            raise Exception("failed to authenticate")


    def _wrapper_from_view_json(self, as_json):
        return ResultWrapper.from_gateway_view_json(as_json)


    # def changes(self, since=None, channels=None, limit=None):
    #     raise NotImplementedError("Haven't done changes for sync gateway yet")


    def sync_up(self):
        pass


    def sync_down(self):
        pass


    def update_designs(self):

        doc_id = "_design/raw"

        design_doc = {
            "_id": doc_id,
            "views": {
                "all": {
                    "map": """function(doc, meta) {
                        doc._rev = meta.rev;
                        emit(doc.type, doc);
                    }
                    """
                }
            }
        }

        self._set(doc_id, design_doc)

        for namespace_name, namespace in self.mapper.namespaces.iteritems():
            view_namespace = namespace_name.replace("/", "_")
            doc_id = "_design/%s" % view_namespace
            attrs = self._get_design(namespace)
            attrs["_id"] = doc_id
            self._set(doc_id, attrs)