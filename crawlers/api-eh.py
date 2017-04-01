#!/usr/bin/env python

# simple EH api test

import json, urllib, sys

# python 2 vs. python 3 compatibility
try:
    from http import client as httpclient
except ImportError:
    import httplib as httpclient

reqpy = { "method"  : "gdata"
        , "gidlist" : [ [ 639967 , "e2be237948" ]
                      ]
        }
headers = { "Accept"       : "application/jsonrequest"
          , "Content-type" : "text/json"
          }
if 1 < len(sys.argv):
    gidlist = []
    for arg in sys.argv[1:]:
        if '/' in arg:
            left, right = arg.split('/')
            left = int(left)
            gidlist.append([left, right])
        else:
            print('Bad arg:', arg)
    print(gidlist)
    reqpy['gidlist'] = gidlist
req   = json.dumps(reqpy)
conn  = httpclient.HTTPConnection("e-hentai.org")
conn.request("POST", "/api.php", req, headers);
reply = conn.getresponse()
data  = reply.read()
print(reply.status, reply.reason)
print(data)
response = json.loads(data)
print(response)
conn.close()

