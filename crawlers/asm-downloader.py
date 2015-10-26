#!/usr/bin/env python

# crawler and downloader of images from ASM

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
def cln_html(page): return re.sub('\n|\t|\r', '',  page)

def links_from_page(page):
    imga  = re.findall('<a[^<>]+>[^<>]*<img[^<>]+>[^<>]*</a>', page)
    links = [l for l in imga if re.search('href="[^"]*\d+\.(jpg|gif|png)"', l)]
    return [re.search('href="([^"]+)"', l).group(1) for l in links]

def all_links(url):
    page = cln_html(urlopen(url).read())
    url  = re.sub('/index.[^/]+$', '/', url)
    if not url.endswith('/'): url += '/'
    links  = links_from_page(page)
    return [l if l.startswith('http') else url + l for l in links]

def num_fext(num, fname):
    ext = re.search('\\.([^.]+)$', fname).group(1)
    return num + '.' + ext, fname

def dimg(file, url):
    sleep(1)
    print 'downloading: ' + url + ' as ' + file
    urlretrieve(url, file)

def dwnld_imgs(url):
    imgs = [lnk for lnk in all_links(del_query(url))]
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

def usage(): print '    asm_dowloader.py -u url [-f filename]'

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

