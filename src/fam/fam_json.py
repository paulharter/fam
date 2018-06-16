

def object_default(o):
    if hasattr(o, "to_json"):
        return o.to_json()
    raise TypeError(repr(o) + " is not JSON serializable")


# class PatchedJson(object):
#     import simplejson as json
#
#     def dumps(self, *args, **kwargs):
#         print args[0]
#         return self.json.dumps(*args, indent=4, sort_keys=True, default=object_default, **kwargs)
#
#     def __getattr__(self, name):
#         return getattr(self.json, name)
#
#
# sys.modules[__name__] = PatchedJson()






