#!/usr/bin/env python

import sys, os, re, getopt
from time import sleep
from urllib import urlopen, urlretrieve

def digits(n, base=10):
     c = 1
     while base <= n:
         c += 1
         n /= base
     return c

def del_query(url): return re.sub('\\?.*$',   '',  url)
def cln_query(url): return re.sub('&amp;',    '&', url)
def cln_html(page): return re.sub('\n|\t|\r', '',  page)

def links_from_page(page):
    img_a = re.findall('<a[^<>]+>[^<>]*<img[^<>]+>[^<>]*</a>', page)
    links = [l for l in img_a if re.search('photo', l)]
    hrefs = [re.search('href="(/photo[^"]+)', l).group(1) for l in links]
    print 'found a bunch of images here: ', hrefs
    return  ['http://www.imagefap.com' + cln_query(h) for h in hrefs]

def have_next_link(page, url):
    next_anchor = re.findall('<a[^<>]+>\s*::\s*next\s*::\s*</a>', page);
    if next_anchor:
        href     = re.search('href="([^"]+)"', next_anchor[0]).group(1)
        print "I'm going to the next page: " + href
        return del_query(url) + cln_query(href)
    return None

def all_links(url):
    page   = cln_html(urlopen(url).read())
    links  = links_from_page(page)
    nxt_pg = have_next_link(page, url)
    if nxt_pg:
        sleep(1)
        return links + all_links(nxt_pg)
    return links

def img_from_link(url):
    sleep(1)
    page = cln_html(urlopen(url).read())
    img  = re.findall('<img[^<>]*"mainPhoto"[^<>]*>', page);
    src  = re.search('src="([^"]+)"', img[0]).group(1)
    return cln_query(src)

def num_fext(num, fname):
    ext = re.search('\\.([^.]+)$', fname).group(1)
    return num + '.' + ext, fname

def dimg(file, url):
    sleep(1)
    print 'downloading: ' + url + ' as ' + file
    urlretrieve(url, file)

def dwnld_imgs(url):
    imgs = [img_from_link(lnk) for lnk in all_links(url)]
    #imgs  = file('data').read().split()
    imgn  = len(imgs)
    dgs   = digits(imgn)
    downl = zip(['%0*i' % (dgs, x) for x in range(1, imgn+1)], imgs)
    files = [num_fext(num, fname) for (num, fname) in downl]
    for f in files: dimg(f[0], f[1])
    return [i for (i,u) in files]

def build_cbz(name, imgs):
    cbz = '.cbz'
    if name.endswith('.cbz'): cbz = ''
    cmd = 'zip -6 ' + "'" + name + cbz + "'" + ' ' + ' '.join(imgs)
    print 'building cbz as: ' + cmd
    ret = os.system(cmd)
    ret = 0
    if 0!= ret:
        print "something went wrong with ziping, I'll not delete the images"
        return False
    return True

def remove_files(files):
    for f in files:
        print "rm " + f
        os.unlink(f)

def usage(): print '    imagefap_dowloader.py -u url [-f filename]'

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'u:f:k', [ 'url='
                                                          , 'file='
                                                          , 'keep'
                                                          ])
    except getopt.GetoptError as err:
        usage()
        print str(err)
        sys.exit(2)
    url   = None
    fname = None
    keep  = False
    for o, a in opts:
        if   o in ('-u', '--url' ): url   = a
        elif o in ('-f', '--file'): fname = a
        elif o in ('-k', '--keep'): keep  = True
        else: assert False, "sorry I do no understand: " + o
    if not url:   assert False, '-u is mandatory'
    if not fname: fname = re.search('/?([^/?]+)/?(\\?[^/?]*)?$', url).group(1)
    imgs = dwnld_imgs(url)
    if build_cbz(fname, imgs) and not keep: remove_files(imgs)

if __name__ == '__main__': main()

