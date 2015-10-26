#!/usr/bin/env python

# Crawls the forums thread and calculater the average amount of credits
# recieived at the dawn of a new day event.

import urllib as url
import BeautifulSoup as bs
import time as t
import numpy as np
import pylab as plt
import re
find  = 'http://forums.e-hentai.org/index.php?s=&showtopic=12100&view=findpost&p='
base  = 'http://forums.e-hentai.org/index.php?showtopic=12100&pid=2975244&st='
ufrom = 300200
uto   = 319560
credits = []
for i in range(ufrom, uto, 20):
    print "Processing:", base+str(i)
    page = url.urlopen(base + str(i))
    html = bs.BeautifulSoup(page.read())
    posts = html.findAll('div', {'class':'postcolor'})
    for post in posts:
        try:
            if re.search('It is the dawn of a new day', str(post)):
                m = re.search('You gain (\d+) Credits', str(post))
                if m:
                    cs = int(m.groups()[0])
                    cs = (cs < 1000 and cs or 0)
                    if 0 != cs: credits.append(cs)
                    print ("%3i" % cs), "Cs", ("[%i]" % len(credits)), \
                          find+str(re.sub('post-', '', dict(post.attrs)['id']))
        except Exception as e:
            print "Bad post at:", i
            print str(e)
    t.sleep(12)
creds = np.array(credits)
print "Totals:"
print "min:",np.min(credits),"max:",np.max(credits)
print "mean:",np.mean(credits),"median:",np.median(credits)
print "std. deviation:",np.std(credits)
np.savetxt('ehdawn.dat', creds)
fig  = plt.figure()
plot = fig.add_subplot(1,1,1)
hist = plot.hist(creds, bins=40)
fig.savefig('ehdawn.png')

