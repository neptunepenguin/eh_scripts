#!/usr/bin/env python

# simple EH api test

import json, urllib, httplib

reqpy = { "method"  : "gdata"
        , "gidlist" : [ [ 639967 , "e2be237948" ]
                      ]
        }
headers = { "Accept"       : "application/jsonrequest"
          , "Content-type" : "text/json"
          }
req   = json.dumps(reqpy)
conn  = httplib.HTTPConnection("g.e-hentai.org")
conn.request("POST", "/api.php", req, headers);
reply = conn.getresponse()
data  = reply.read()
print reply.status, reply.reason
print data
response = json.loads(data)
conn.close()

