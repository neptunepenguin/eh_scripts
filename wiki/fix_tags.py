#!/usr/bin/env python

import sys
import time
import re
import logging
from itertools import dropwhile
import requests
from bs4 import BeautifulSoup


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)
usage = (
    ( '%s "eh login name" "eh password" ' +
      '"wiki username" "wiki password" ' +
      '"output file (for debug)"' ) % sys.argv[0] )
if len(sys.argv) < 6:
    log.critical(usage)
    sys.exit(1)
eh_username = sys.argv[1]
eh_password = sys.argv[2]
wiki_username = sys.argv[3]
wiki_password = sys.argv[4]
outfile = sys.argv[5]
eh_session = requests.Session()
wiki_session = requests.Session()
headers = { 'User-Agent' :
    'Mozilla/5.0 (X11; Linux x86_64; rv:54.0) Gecko/20100101 Firefox/54.0' }
eh_login_data = {
    'UserName' : eh_username,
    'PassWord' : eh_password,
    'x'        : 0,
    'y'        : 0
}
wiki_login_data = {
    'wpName'         : wiki_username,
    'wpPassword'     : wiki_password,
    'wploginattempt' : 'Log in',
    'wpEditToken'    : None,
    'authAction'     : 'login',
    'title'          : 'Special:UserLogin',
    'force'          : None,
    'wpLoginToken'   : None
}


class DeepDict(object):
    '''
    A dictionary of dictionaries that updates the keys of the deep dictionaries
    instead of its own keys.  In other words it more-or-less works as a
    dictionary but has a special update method.
    '''
    def __init__(self, *args, **kwargs):
        '''Keep the actual dictionary internally.'''
        self._dict = dict(*args, **kwargs)

    def __getattr__(self, key):
        '''
        Will raise the correct exception for a dictionary.  Note that
        retrieving `._dict` still works, not sure why.
        '''
        return self._dict[key]

    def __setattr__(self, key, value):
        '''
        Makes an exception for items starting with underscores, this is needed
        to actually maintain the internal dictionary without falling into and
        infinite loop during `self._dict`.
        '''
        if key.startswith('_'):
            super(DeepDict, self).__setattr__(key, value)
        else:
            self._dict[key] = value

    def __delattr__(self, key):
        '''Allow for deletion.'''
        del self._dict[key]

    def __iter__(self):
        '''Required to be able to go through the keys in a for loop.'''
        for k in self._dict:
            yield k

    def items(self):
        '''
        `.items` is used in python 3.x, `.iteritems` is for backward
        compatibility with python 2.x.
        '''
        for k,v in self._dict.items:
            yield k,v
    iteritems = items

    def update(self, deep_dict):
        '''
        Perform a deep update: if both the value in the current internal
        dictionary and the value in the item being placed over it are some kind
        of dictionary (i.e. have the `update` atribute, remember duck typing)
        then join them together instead of replaing one with another.
        '''
        for k,v in deep_dict.items():
            deep = self._dict.get(k)
            if deep and hasattr(deep, 'update') and hasattr(v, 'update'):
                deep.update(v)
            else:
                self._dict[k] = v

    def __str__(self):
        '''
        String representation similar to a dictionary.  Keep the `__repr__`
        the same, to print nicely inside other dictionaries.
        '''
        return 'deep%s' % self._dict
    __repr__ = __str__


def auth_forums(session):
    '''
    Performs the login procedure to the EH forums,
    this is needed for us to be able to retrieve the lists of tag groups.
    '''
    url = 'https://forums.e-hentai.org'
    log.info('GET %s', url)
    r = session.get(url, headers=headers)
    log.debug('HTTP %d', r.status_code)
    session_cookie = session.cookies.get('ipb_session_id')
    print( 'FORUM login with user %s, password ******, session %s' %
        (eh_username, session_cookie) )
    time.sleep(1)
    url = 'https://forums.e-hentai.org/index.php?act=Login&CODE=01&CookieDate=1'
    log.info('POST %s', url)
    rp = session.post(url, data=eh_login_data, headers=headers)
    log.debug('HTTP %d', rp.status_code)
    print( 'FORUM login with user %s, password ******, cookies %s' %
        (eh_username, rp.cookies) )
    #url = 'https://e-hentai.org/tools.php?act=taggroup'
    #r = session.get(url, headers=headers)
    #with open(outfile, 'wb') as f:
    #    f.write(r.content)
    #print(session.cookies)
    return session


def auth_wiki(session):
    '''
    Performs the login procedure to the EH wiki.
    We need the credentials to the wiki to update (POST)
    the revised tag templates.
    '''
    url = 'https://ehwiki.org/index.php?title=Special:UserLogin&returnto=Main+Page'
    r = session.get(url, headers=headers)
    session_cookie = session.cookies.get('ehwiki_session')
    soup = BeautifulSoup(r.content, 'html.parser')
    edit_input = soup.select('input[name="wpEditToken"]')[0]
    token_input = soup.select('input[name="wpLoginToken"]')[0]
    edit_token = edit_input.attrs.get('value')
    login_token = token_input.attrs.get('value')
    wiki_login_data['wpEditToken'] = edit_token
    wiki_login_data['wpLoginToken'] = login_token
    print( 'WIKI login with user %s, password ***, session %s, tokens %s|%s' %
        (wiki_username, session_cookie, edit_token, login_token) )
    time.sleep(1)
    rp = session.post(url, data=wiki_login_data, headers=headers)
    #with open(outfile, 'wb') as f:
    #    f.write(rp.content)
    print(session.cookies)
    return session


def retrieve_tag_groups(session, grouping):
    url = 'https://e-hentai.org/tools.php?act=taggroup&show=%d' % grouping
    log.info('GET %s', url)
    r = session.get(url, headers=headers)
    log.debug('HTTP %d', r.status_code)
    soup = BeautifulSoup(r.content, 'html.parser')
    links = soup.select('td a')
    for l in links:
        log.debug('Link: %s => %s', l.text, l.attrs.get('href'))
    group = {}
    return session, group


TAG_GROUP_MISC_MAP = { 'misc': 0, 'reclass': 1, 'language': 2,
                       'parody': 3, 'character': 4, 'group': 5, 'artist': 6 }
TAG_GROUP_MALE_MAP = { 'male': 7 }
TAG_GROUP_FEMALE_MAP = { 'female': 8 }
TAG_GROUP_MAP = { 'female': TAG_GROUP_FEMALE_MAP,
                  'male': TAG_GROUP_MALE_MAP,
                  'misc': TAG_GROUP_MISC_MAP }
def build_group_struct(session):
    groups = DeepDict()
    for tag_map, value in TAG_GROUP_MISC_MAP.items():
        this_group = retrieve_tag_groups(session, value)
        total = len(this_group.keys())
        log.info('Got %d tag groups for %s', total, tag_map)
        groups.update(this_group)
    return session, groups


def retrieve_wiki_tag(session, tag):
    '''
    Checks whether we do have a wiki page for a specific tag.
    Note that wiki pages use underscores instead of spaces or dashes for tag
    names which this function do not account for, you need to make the
    appropriate changes to the `tag` argument before passing it.  e.g.

        retrieve_wiki_tag(session, tag.replace(' ', '_').replace('-', '_'))

    Another option is to try every possible tag: with spaces, with underscores
    and with dashes.

    NOTE: We use both /wiki/ and /action/edit/ because the media wiki
    redirect does not perform HTTP 3xx, instead it reloads the redirected page
    directly from the redirected URL (and uses JS to change the URL later).
    Inside /adction/edit/ we can actually check the redirection markup
    (`#REDIRECT`) and act accordingly.
    '''
    url = 'https://ehwiki.org/wiki/%s' % tag
    log.info('GET %s', url)
    r = session.get(url, headers=headers, allow_redirects=False)
    log.debug('HTTP %d (%s)', r.status_code, r.ok)
    if r.ok:  # any 2xx is good enough for us
        url = 'https://ehwiki.org/action/edit/%s' % tag
        r = session.get(url, headers=headers, allow_redirects=False)
        log.debug('HTTP %d', r.status_code)
        soup = BeautifulSoup(r.content, 'html.parser')
        markup = soup.find('textarea').text
        if '#REDIRECT' in markup:
            log.debug('INTERNAL REDIRECT (True => False)')
            return session, False
    return session, r.ok


def edit_template(tag, tag_def, female=None, male=None, misc=None):
    '''
    Makes the required edits to the wiki template (tag definition).
    If we do have a tag group (which we retrieved from EH) but the wiki page do
    not account for it, we fix the wiki page by adding the correct argument to
    it.  On the other hand, if the wiki page already has the argument in place
    we take care to not change the argument placement so that we do not mess
    with the wiki version control.

    This entire function is three times the same code duplicated.  Not the most
    elegant solution but makes debuggin easy.
    '''
    info = 'tag:%s' % tag
    if female and re.search('\n\|taggroupid=', tag_def):
        info += ', taggroupid => %d' % female
        tag_def = re.sub( '\n\|taggroupid=\d+',
                          '\n|taggroupid=%d' % female,
                          tag_def )
    elif female:
        info += ', (NEW)taggroupid => %d' % female
        tag_def = re.sub( '\n}}',
                          '\n|taggroupid=%d\n}}' % female,
                          tag_def )
    if male and re.search('\n|maletaggroupid=', tag_def):
        info += ', maletaggroupid => %d' % male
        tag_def = re.sub( '\n\|maletaggroupid=\d+',
                          '\n|maletaggroupid=%d' % male,
                          tag_def )
    elif male:
        info += ', (NEW)maletaggroupid => %d' % male
        tag_def = re.sub( '\n}}',
                          '\n|maletaggroupid=%d\n}}' % male,
                          tag_def )
    if misc and re.search('\n|misctaggroupid=', tag_def):
        info += ', misctaggroupid => %d' % misc
        tag_def = re.sub( '\n\|misctaggroupid=\d+',
                          '\n|misctaggroupid=%d' % misc,
                          tag_def )
    elif misc:
        info += ', (NEW)misctaggroupid => %d' % misc
        tag_def = re.sub( '\n}}',
                          '\n|misctaggroupid=%d\n}}' % misc,
                          tag_def )
    log.info(info)
    return tag_def


domain = 'https?\:\/\/[g.e-]+hentai\.org'
m_body = re.escape('/tools.php?act=taggroup&mastertag=')
t_body = re.escape('/tools.php?act=taggroup&taggroup=')
group = '\d+'
RAW_MASTER_RE = re.compile(domain + m_body + group)
RAW_GROUP_RE = re.compile(domain + t_body + group)
def edit_raw_tag(tag, tag_def, group):
    '''
    If we have a tag which has a tag group but do not use the wiki template we
    can only guess the changes we need to do.  Without the tenplate the markup
    can be writen in may ways so we must attemp to edit the links directly.
    Either the old link using `taggroup=` directly or attempt to change a link
    with `mastertag=` in case someone may have attempted the change already.

    Attempt changing the `mastertag` link first otherwise we may chnage what we
    already placed in the definition by changing the `taggroup` parameter into
    the `mastertag` parameter.
    '''
    new_def = tag_def
    # dues to URL changes and redirects the domain may be tricky
    new_t = 'http://e-hentai.org/tools.php?act=taggroup&mastertag=%d' % group
    new_def = RAW_MASTER_RE.sub(new_t, new_def)
    new_def = RAW_GROUP_RE.sub(new_t, new_def)
    log.info('tag:%s, mastertag => %d', tag, group)
    return new_def


def change_tag(session, tag, female=None, male=None, misc=None):
    url = 'https://ehwiki.org/action/edit/%s' % tag
    log.info('GET %s', url)
    r = session.get(url, headers=headers)
    log.debug('HTTP %d', r.status_code)
    soup = BeautifulSoup(r.content, 'html.parser')
    definition = soup.find('textarea').text
    log.debug('FROM:\n%s', definition)
    if re.search('\n{{ContentTag', definition):
        new_def = edit_template(tag, definition, female, male, misc)
    else:
        group = list(dropwhile(lambda x: not x, [misc, female, male]))[0]
        new_def = edit_raw_tag(tag, definition, group)
    log.debug('TO:\n%s', new_def)
    if definition == new_def:
        log.info('tag:%s: No changes to be made, bail', tag)
        return session
    log.info('tag:%s: POSTing change')
    # TODO the actual POST
    return session

#eh_session = auth_forums(eh_session)
#time.sleep(1)
#eh_session = retrieve_tag_groups(eh_session, 2)
#wiki_session = auth_wiki(wiki_session)
#eh_session, s = retrieve_wiki_tag(eh_session, 'yaoi')
#eh_session, s = retrieve_wiki_tag(eh_session, 'yaoiu')
#eh_session, s = retrieve_wiki_tag(eh_session, 'cosplay')
#eh_session, s = retrieve_wiki_tag(eh_session, 'ah_my_goddess')
#eh_session = change_tag(eh_session, 'big_penis', 123, 456)
#eh_session = change_tag(eh_session, 'ah_my_goddess', 123, 456)
d = DeepDict(a={2:1},b={2:1},c={2:1})
print(d._dict)
d.update({1: DeepDict(a=3), 'b' : {1:2}})
print(d._dict)

