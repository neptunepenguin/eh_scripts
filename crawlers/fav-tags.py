#!/usr/bin/env python

# crawls EH favourites and return tags in these galleries.

import json, sys, os, re, getopt, datetime
import urllib2
from time import sleep
from urllib import urlopen
from BeautifulSoup import BeautifulSoup

MAND_CONFIG  = { "favsurl":str , "cookies":str
               , "apihost":str , "api":str
               , "tagslog":str
               }
MAND_COOKIES = { "ipb_member_id":str , "ipb_pass_hash":str }

# for future use
FAV_CATS = { "black"  : "?favcat=0" , "red"    : "?favcat=1"
           , "orange" : "?favcat=2" , "yellow" : "?favcat=3"
           , "green"  : "?favcat=4" , "lime"   : "?favcat=5"
           , "cyan"   : "?favcat=6" , "blue"   : "?favcat=7"
           , "purple" : "?favcat=8" , "pink"   : "?favcat=9"
           , "all"    : ""
           }

def json_min(lines=[], acc=[]):
    for l in lines: acc.append(re.sub('^\s*//.*$|^\s*#.*$', '', l.rstrip()))
    return "\n".join(acc)

def json_config(cfile="./conf.json", mandatory={}):
    try: fh = open(cfile, 'rb')
    except IOError as e: sys.exit(e)
    js = json_min(fh)
    print js
    try: dict = json.loads(js)
    except ValueError as e: sys.exit(cfile + " - " + str(e))
    fh.close()
    for k in mandatory:
        if not k in dict:
            sys.exit(cfile + " - parameter [" + k + "] is mandatory")
        if not isinstance(dict[k], mandatory[k]):
            sys.exit(cfile + " - bad format for parameter [" + k + "]")
    return dict


#json.loads(json_min(file('./cookies.json')))
cj = '; '.join(["1","2"])

def getlinks(url="http://g.e-hentai.org/favorites.php", cookies={}):
    opener = urllib2.build_opener()
    opener.addheaders.append(('Cookie', cj))
    #doc = opener.open(u'http://g.e-hentai.org/favorites.php')
    doc = file(u'./test_page.html').read()
    soup = BeautifulSoup(doc)
    nfav = soup.find('p', {"class" : "ip"})
    gals = soup.findAll('div', {"class" : "it5"})
    next = soup.find('table', {"class" : "ptb"}).findAll('td')[-1]
    print "nfav:", nfav
    print "next:", next
    for g in gals: print g

# Another option:
#import urllib2
#import urllib
#from cookielib import CookieJar
#
#cj = CookieJar()
#opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
#formdata = { "username" : username, "password": password, "form-id" : "1234" }
#data_encoded = urllib.urlencode(formdata)
#response = opener.open("https://page.com/login.php", data_encoded)
#content = response.read()

datetime.datetime.now()
def genlogger(conf, verbose=0, outputs=[]):
    if   1 == verbose: outputs.append(sys.stdout)
    elif 1 <  verbose: outputs.append(sys.stderr)
#    if "msglog" in conf:
#        try: log = open()
#    return lambda level, msg

#def optparse(args)

def main():
    usage     = sys.argv[0] + " [-h] -c <conf.json> [-s|-v]"
    long_opts = ["conf=", "help", "silent", "verbose"]
    try: opts, args = getopt.getopt(sys.argv[1:], "c:hsv", long_opts)
    except getopt.GetoptError as e: sys.exit(str(e) + "\n" + usage)
    verbose, conf_file, help = False, None, None
    for o,a in opts:
        if   o in ("-c", "--conf")    : conf_file = a
        elif o in ("-h", "--help")    : help = True
        elif o in ("-v", "--verbose") : verbose += 1
        elif o in ("-s", "--silent")  : verbose -= 1
        else : sys.exit(usage)
    if help: sys.exit(usage)
    if not conf_file: sys.exit(usage)
    conf = json_config(conf_file, MAND_CONFIG)
#   print nfav.contents[0]
#   for g in gals: print g.a['href']

if __name__ == '__main__': main()

