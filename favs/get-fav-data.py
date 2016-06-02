#!/usr/bin/env python

import os, sys, getopt, re, time
from http import cookies as hc
from urllib import request as ur
from urllib import parse as up
from bs4 import BeautifulSoup as bs

G_PER_PAGE = 50
SLEEP = 6
URL = 'http://g.e-hentai.org/favorites.php'
FAV_CATS = { 'black'  : '0' , 'red'    : '1'
           , 'orange' : '2' , 'yellow' : '3'
           , 'green'  : '4' , 'lime'   : '5'
           , 'cyan'   : '6' , 'blue'   : '7'
           , 'purple' : '8' , 'pink'   : '9'
           , 'all'    : None
           }

# Testing
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_HTML = os.path.join(BASE_DIR, 'test-favs.html')
TESTMODE = False

def dprint(*args, **kwargs):
    '''debug print'''
    print(*args, file=sys.stderr, **kwargs)

def mkparams(params={}):
    url_params = ''
    keys = list(params.keys())
    for k in keys:
        if params[k] is None:
            del params[k]
    if params:
        url_params = '?' + up.urlencode(params)
    return url_params

def get_cookie_str():
    cookies = hc.SimpleCookie()
    cookies['ipb_member_id'] = os.environ.get('EHID')
    cookies['ipb_pass_hash'] = os.environ.get('EHHASH')
    cookies['s'] = os.environ.get('EHS')
    cookie_str = cookies.output(header='', sep=';').strip()
    dprint('Cookie string:', cookie_str)
    return cookie_str

def build_url(colour=None, page=None):
    params = { 'favcat' : FAV_CATS.get(colour)
             , 'page'   : page
             }
    return URL + mkparams(params)

def mkreq(url, cookies):
    dprint('Requesting:', url)
    if TESTMODE:
        html = open(TEST_HTML, 'r').read()
        return html
    req = ur.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0')
    req.add_header('Host', 'g.e-hentai.org')
    req.add_header('Accept', 'text/html,application/xhtml+xml')
    req.add_header('Cookie', cookies)
    page = ur.urlopen(req)
    return page.read().decode('utf-8')

def parse_favs(soup):
    trs = soup.select('tr[class="gtr0"],tr[class="gtr1"]')
    for tr in trs:
        tr_children = list(tr.children)
        published = re.sub('\s+', 'T', tr_children[2].get_text())
        gallery = tr_children[3]
        a = list(gallery.select_one('.it5').children)[0]
        href = a['href']
        gh = re.search('/g/(\d+)/([0-9a-f]+)/$', href)
        gid = gh.group(1)
        token = gh.group(2)
        note = 'None'
        children = list(gallery.children)
        if len(children) > 1 and children[1].get_text():
            full_note = children[1].get_text()
            note = re.sub('^Note:\s+', '', full_note)
        print(gid, token, published, href, note)

def get_data(colour=None):
    dprint('Filter applied to favourites:', colour)
    cookies = get_cookie_str()
    url = build_url(colour)
    html = mkreq(url, cookies)
    soup = bs(html, 'html.parser')
    p = soup.select_one('p[class="ip"]')
    showing = p.get_text()
    dprint('First page total:', showing)
    match = re.search('of ([,\d]+)$', showing)
    galleries = re.sub('[^\d]', '', match.group(1))
    dprint('Number of galleries:', galleries)
    pages = int(galleries) // G_PER_PAGE
    dprint('Number of extra pages:', pages)
    parse_favs(soup)
    for page in range(1, pages+1):
        if not TESTMODE:
            time.sleep(SLEEP)
        url = build_url(colour, page)
        html = mkreq(url, cookies)
        soup = bs(html, 'html.parser')
        parse_favs(soup)

def main():
    global TESTMODE
    usage = sys.argv[0] + ' [-h] [-t] [-c <colour>]'
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'htc:')
    except getopt.GetoptError as e:
        sys.exit(str(e) + "\n" + usage)
    colour = None
    for o,a in opts:
        if   o == '-c':
            if a in FAV_CATS.keys():
                colour = a
        elif o == '-t':
            TESTMODE = True
        elif o == '-h':
            sys.exit(usage)
        else:
            sys.exit(usage)
    get_data(colour)

if __name__ == '__main__':
    main()

