"""
This either imports all of requests or wraps google app engine's urlfetch with requests like syntax

It is far from complete and just does the things I needed at the time
"""


try:
    from requests import *
except ImportError as e:
    import urllib
    import json
    from google.appengine.api import urlfetch
    
    class ResponseWrapper(object):
        
        def __init__(self, response):
            self.response = response
            
        @property
        def status_code(self):
            return int(self.response.status_code)
        
        @property
        def headers(self):
            return self.response.headers
        
        @property
        def content(self):
            return self.response.content

        def json(self):
            return json.loads(self.response.content)
        
        
    def get(url, **kwargs):
        return request("GET", url, **kwargs)

    def put(url, **kwargs):
        return request("PUT", url, **kwargs)
    
    def post(url, **kwargs):
        return request("POST", url, **kwargs)
    
    
    def request(method, url, **kwargs):
        
        if "params" in kwargs.keys():
            querystring = urllib.urlencode(kwargs["params"])
            url = "%s?%s" % (url, querystring)
        
        if "data" in kwargs.keys():
            data = kwargs["data"]
            if type(data) == type({}):
                payload = urllib.urlencode(data)
            elif type(data) == type(""):
                payload = data
            elif hasattr(data, "read"):
                payload = data.read()
            else:
                payload = None
        else:
            payload = None
        
        if "headers" in kwargs.keys():
            headers = kwargs["headers"]
        else:
            headers = {}
            
        if "allow_redirects" in kwargs.keys():
            follow_redirects = kwargs["allow_redirects"]
        else:
            follow_redirects = True

        if "timeout" in kwargs.keys():
            deadline = kwargs["timeout"]
        else:
            deadline = 5
            
        if "verify" in kwargs.keys():
            validate_certificate = kwargs["validate_certificate"]
        else:
            validate_certificate = False
        
        resp = urlfetch.fetch(url, 
                              payload=payload, 
                              method=method, 
                              headers=headers, 
                              allow_truncated=False, 
                              follow_redirects=follow_redirects, 
                              deadline=deadline, 
                              validate_certificate=validate_certificate)
        
        return ResponseWrapper(resp)
