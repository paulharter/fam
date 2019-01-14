
import requests
import json
import time
import subprocess

def make_a_bucket(couchbase_url, user_name, password, bucket_name, force=False, flush=False):

    params = {}
    params["authType"] = "none"
    params["proxyPort"] = "11224"
    params["bucketType"] = "couchbase"
    params["flushEnabled"] = "1"
    params["name"] = bucket_name
    params["ramQuotaMB"] = "128"
    params["replicaNumber"] = "0"

    if flush:
        params["flushEnabled"] = "1"

    headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}

    rsp = requests.post("%s/pools/default/buckets" % (couchbase_url), data=params, auth=(user_name, password))

    if rsp.status_code == 400:
        info = json.loads(rsp.text)
        errors = info["errors"]
        name_error = errors.get("name")
        if name_error == "Bucket with given name already exists":
            if force:
                delete_a_bucket(couchbase_url, user_name, password, bucket_name)
                return make_a_bucket(couchbase_url, user_name, password, bucket_name)
            else:
                raise Exception("failed to make new bucket %s : %s" % (rsp.status_code, rsp.text))

    if rsp.status_code != 202:
        raise Exception("failed to make new bucket %s : %s" % (rsp.status_code, rsp.text))


def delete_a_bucket(couchbase_url, user_name, password, bucket_name):

    time.sleep(1)

    rsp = requests.delete("%s/pools/default/buckets/%s" % (couchbase_url, bucket_name), auth=(user_name, password))

    if rsp.status_code != 200:
        raise Exception("failed to delete bucket %s : %s" % (rsp.status_code, rsp.text))


def number_of_buckets(couchbase_url, user_name, password):

    rsp = requests.get("%s/pools/default/buckets" % (couchbase_url), auth=(user_name, password))

    if rsp.status_code != 200:
        raise Exception("failed get bucket count %s : %s" % (rsp.status_code, rsp.text))

    buckets = rsp.json()
    return len(buckets)


def flush_a_bucket(couchbase_url, user_name, password, bucket_name):

    rsp = requests.post("%s/pools/default/buckets/%s/controller/doFlush" % (couchbase_url, bucket_name), auth=(user_name, password))

    # if rsp.status_code != 200:
    #     raise Exception("failed to flush bucket %s : %s" % (rsp.status_code, rsp.text))


def make_a_gateway(sync_admin_url, db_name, couchbase_url, bucket, sync_function, force=False):

    config = {db_name:{
         "server": couchbase_url,
         "bucket": bucket,
         "sync": sync_function}
        }


    rsp = requests.put("%s/%s/" % (sync_admin_url, db_name), data=json.dumps(config))

    if rsp.status_code == 412:
        info = json.loads(rsp.text)
        error = info.get("error")
        reason = info.get("reason")
        if reason and reason.startswith("Duplicate database name") and force:
            delete_a_gateway(sync_admin_url, db_name)
            return make_a_gateway(sync_admin_url, db_name, couchbase_url, bucket, sync_function)
        else:
            raise Exception("failed to make a new gateway %s : %s" % (rsp.status_code, rsp.text))

    if rsp.status_code != 201:
        raise Exception("failed to make a new gateway %s : %s" % (rsp.status_code, rsp.text))


def delete_a_gateway(sync_admin_url, db_name):

    rsp = requests.delete("%s/%s/" % (sync_admin_url, db_name))

    if rsp.status_code != 200:
        raise Exception("failed to make a new gateway %s : %s" % (rsp.status_code, rsp.text))



def does_person_exist(sync_admin_url, db_name, username):

    rsp = requests.get("%s/%s/_user/%s" % (sync_admin_url, db_name, username))

    if rsp.status_code == 200:
        return True
    elif rsp.status_code == 404:
        return False
    else:
        raise Exception("failed to add person %s : %s" % (rsp.status_code, rsp.text))



def add_person_to_gateway(sync_admin_url, db_name, user_id, username, password, domain_role=None, admin_channels=None):

    if sync_admin_url is None:
        return

    attrs = {
         "password": password,
         "admin_roles": [user_id]
        }

    if domain_role is not None:
        attrs["admin_roles"].append(domain_role)

    if admin_channels is not None:
        attrs["admin_channels"] = admin_channels

    rsp = requests.put("%s/%s/_user/%s" % (sync_admin_url, db_name, username), data=json.dumps(attrs))

    if rsp.status_code >= 300:
        raise Exception("failed to add person %s : %s" % (rsp.status_code, rsp.text))



def add_guest_to_gateway(sync_admin_url, db_name):

    rsp = requests.put("%s/%s/_user/GUEST" % (sync_admin_url, db_name), data='{"disabled":false, "admin_channels":["public"]}')

    if rsp.status_code != 200:
        pass
        #raise Exception("failed to add user %s : %s" % (rsp.status_code, rsp.text))



def make_bucket_and_gateway(couchbase_url,
                            couchbase_user_name,
                            couchbase_password,
                            bucket_name,
                            sync_admin_url,
                            sync_db_name,
                            sync_function,
                            guest=False,
                            force=False):

    make_a_bucket(couchbase_url, couchbase_user_name, couchbase_password, bucket_name, force=force)
    # make_a_gateway(sync_admin_url, sync_db_name, couchbase_url, bucket_name, sync_function, force=force)
    #if guest:
    #    add_guest_to_gateway(sync_admin_url, sync_db_name)


def delete_bucket_and_gateway(couchbase_url,
                            couchbase_user_name,
                            couchbase_password,
                            bucket_name,
                            sync_admin_url,
                            sync_db_name):


    # delete_a_gateway(sync_admin_url, sync_db_name)
    delete_a_bucket(couchbase_url, couchbase_user_name, couchbase_password, bucket_name)

