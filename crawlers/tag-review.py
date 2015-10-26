#!/usr/bin/env python

# statistics over the EH taglist

import BeautifulSoup as bs
import urllib2 as ul

URL     = 'http://g.e-hentai.org/tools.php?act=taglist&uid=ffffff'
COOKIES = ( "ipb_member_id=ffffff"
          , "ipb_pass_hash=ffffffffffffffffffffffffffffffff"
          )
RESULTS = 100
opener = ul.build_opener()
opener.addheaders.append(('Cookie', ';'.join(COOKIES)))
tool = opener.open(URL)
soup = bs.BeautifulSoup(tool.read())
tags = soup.findAll('tr')
gtags = {}
btags  = {}
for t in tags[1:]:
    tag = t.find('td', style='font-weight:bold').string
    if t.find('td', style='font-weight:bold; color:red'):
        btags[tag] = btags.get(tag, 0) + 1
    else:
        gtags[tag] = gtags.get(tag, 0) + 1
print
print 'GOOD TAGS:'
for t in sorted(gtags, key=gtags.get)[-RESULTS:]: print t, gtags[t]
print
print 'BAD TAGS:'
for t in sorted(btags, key=btags.get)[-RESULTS:]: print t, btags[t]

