#!/usr/bin/env python
__doc__ = '''
    fix_tags - One time wiki tag fixer, for new master tag database

After [new changes introduced to EH on 20170807][1] the old tag groups were
retired and the [EH wiki][2] now has its slave tag links leading to the wrong
places.  The tag groups on EH were converted to links to a master tag which is
also reflected in the URL parameters of the `act=taggroup` tool on EH.  The
numbers of old tag groups and new master tags do not correspond to each other.

[1]: https://forums.e-hentai.org/index.php?showtopic=208335
[2]: https://ehwiki.org

At the time of this writing there are more than 13k grouped master tags and
more than 7k wiki pages which previously linked to some of these.  The task of
manually changing the links to point to the correct master tags is, in the most
optimistic estimates, daunting.  Therefore this script exists to automate the
changes.

The general working of the script is to authenticate against the EH domain and
build a data structure that will hold all 13k+ master tags in a grouping that
can be checked against the EH wiki pages.  The authenticate against the EH wiki
and read the definition of every tag that may be a master tag (not all are on
the wiki) and check whether it needs to be updated.  If updates are needed
perform a POST with a corrected definition.

NOTES & FAQ:
------------

*   The script can be re-run as many times as needed, it will not perform
changes where these are not needed.  There is a log of code that makes sure we
do not change things in a wrong way.

*   Authentication parameters come from environment variables instead of
command line arguments.  This is intended because on most operating systems the
environment in which a process runs is protected from the view of all other
processes whilst the command line arguments are not.  This way no one can see
the password you are using to authenticate (unless he is shoulder surfing you,
that is).

*   No, there are no authentication tokens written directly into the script.
You can't hijack any account by reading this code.  All authentication is
generated on the fly.

*   The authenticated accounts must have the permissions to perform the
changes.  For example, it is unlikely that you will be able to change the
definition of protected tags.

*   Don't be an idiot.  This script *can* be used to bot HV (wtih some changes)
but don't do it.  I have hidden a couple of easy to spot (server side) details
that will give you away.  Seriously, don't get banned by your own stupidity.

USAGE
-----

        EH_USERNAME="eh login name" EH_PASSWORD="eh password" \\
        WIKI_USERNAME="wiki username" WIKI_PASSWORD="wiki password" \\
    fix_tags.py [-g GET_SLEEP] [-p POST_SLEEP] \\
        <silent|verbose|very-verbose> [male] [female] \\
        [misc] [reclass] [language] [parody] [character] [group] [artist]

Where the first command line argument provides for the log level, the letter
based arguments (-g, -p) must be (float point) numbers as they are used as the
number of seconds to sleep between GET and POST requests.  All remaining
arguments are the namespaces the script will process.  For example:

    export EH_USERNAME="eh login name"
    export EH_PASSWORD="eh password"
    export WIKI_USERNAME="wiki username"
    export WIKI_PASSWORD="wiki password"
    ./fix_tags.py verbose language female

Will only attempt to change the tags for the language and female namespaces.
Leaving all other wiki pages untouched.  It is completely fine to run the scrit
without any namespace parameters, in which case the script will perform a
simple self check (e.g. whether it can authenticate itself with the credentials
given).
'''
__author__ = 'Neptune Penguin'
__copyright__ = 'Copyright (C) 2017 Aquamarine Penguin'
__license__ = 'GNU GPLv3 or later'
__date__ = '2017-08-13'
__version__ = '0.5'


import os, sys, time, re, logging, getopt
from itertools import dropwhile
import requests
from bs4 import BeautifulSoup


log = logging.getLogger(__name__)  # don't reuse this name, seriously, don't
log_levels = { 'silent'       : logging.WARNING,
               'verbose'      : logging.INFO,
               'very-verbose' : logging.DEBUG }
EH_USERNAME = None
EH_PASSWORD = None
WIKI_USERNAME = None
WIKI_PASSWORD = None
# It is polite to wait a moment between several requests to the same
# webserver, this function exists to ensure that we can change the wait time
# depending on whether we are testing things (and running a handful of
# requests) or working with hundreds or thousands of requests.
# We sleep different times for GET and for POST because most webservers have
# different counters for those, and consider POST much more dangerous.
GET_SLEEP = 0.1
POST_SLEEP = 1
NAMESPACE_LIST = []
SUMMARY = 'Automated Tag Group Fixes'
HEADERS = { 'User-Agent' :
    'Mozilla/5.0 (X11; Linux; rv:13) Gecko/20100101 Firefox/54.0' }
EH_LOGIN_DATA = {
    'UserName' : None,
    'PassWord' : None,
    'x'        : 0,
    'y'        : 0
}
WIKI_LOGIN_DATA = {
    'wpName'         : None,
    'wpPassword'     : None,
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
    __getitem__ = __getattr__

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

    def __setitem__(self, key, value):
        '''Just pass to the dictionary, do not need to use __setattr__.'''
        self._dict[key] = value

    def __delattr__(self, key):
        '''Allow for deletion. As attributes and as keys.'''
        del self._dict[key]
    __delitem__ = __delattr__

    def __iter__(self):
        '''Required to be able to go through the keys in a for loop.'''
        for k in self._dict:
            yield k

    def items(self):
        '''
        `.items` is used in python 3.x, `.iteritems` is for backward
        compatibility with python 2.x.
        '''
        for k,v in self._dict.items():
            yield k,v
    iteritems = items

    def keys(self):
        '''Just pass the keys of the internal dict, hide `._dict`.'''
        return self._dict.keys()

    def update(self, deep_dict):
        '''
        Perform a deep update: if both the value in the current internal
        dictionary and the value in the item being placed over it are some kind
        of dictionary (i.e. have the `update` attribute, remember duck typing)
        then join them together instead of replaying one with another.
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


def build_post_data(dictionary, soup, *args):
    '''
    A trivial POST data builder: searches for the correct input in a beautiful
    soup parsed web page and updates the dictionary to be sent by `requests`.
    This works well when there is a single `<form>` on a page but may fail if
    there is more than one.

    NOTE: the dictionary is passed by reference so it is modified directly.
    '''
    for field in args:
        input = soup.select('input[name="%s"]' % field)
        if input:
            token = input[0].attrs.get('value')
            log.debug('POST Found %s => %s', field, token)
            dictionary[field] = token
        else:
            log.debug('POST NOT Found %s', field)
            dictionary[field] = None


def log_extra(change_p, code, tag, female=None, male=None, misc=None):
    '''
    A default format to print to standard output, i.e. this is the only place
    where print() is used.  This format allows us to grep the generated log for
    records that were updated (:True:200:), records that do not exist on the
    wiki (:False:404:), records that are already in the correct format and need
    not be updated (:False:200:), and records which failed to be updated
    (anything else).
    '''
    format = 'CHANGE:%s:%s:%s:female:%s,male:%s,misc:%s'
    print( format % (change_p, code, tag, female, male, misc) )


def auth_forums(session):
    '''
    Performs the login procedure to the EH forums,
    this is needed for us to be able to retrieve the lists of tag groups.
    '''
    url = 'https://forums.e-hentai.org'
    log.info('GET %s', url)
    r = session.get(url, headers=HEADERS)
    log.debug('HTTP %d', r.status_code)
    session_cookie = session.cookies.get('ipb_session_id')
    soup = BeautifulSoup(r.content, 'html.parser')
    form = soup.find('form')  # login is the first form
    log.info( 'FORUM login with user %s, password ******, session %s',
              EH_USERNAME, session_cookie )
    time.sleep(GET_SLEEP)
    # old login url
    #url = ( 'https://forums.e-hentai.org/index.php'
    #        '?act=Login&CODE=01&CookieDate=1' )
    url = form.attrs.get('action')
    log.info('POST %s', url)
    rp = session.post(url, data=EH_LOGIN_DATA, headers=HEADERS)
    log.debug('HTTP %d', rp.status_code)
    if not rp.ok:
        raise RuntimeError("Can't continue without FORUM auth")
    log.info( 'FORUM login DONE with user %s, password ******, cookies %s',
              EH_USERNAME, session.cookies )
    return session


def auth_wiki(session):
    '''
    Performs the login procedure to the EH wiki.
    We need the credentials to the wiki to update (POST)
    the revised tag templates.
    '''
    url = ( 'https://ehwiki.org/index.php'
            '?title=Special:UserLogin&returnto=Main+Page' )
    r = session.get(url, headers=HEADERS)
    session_cookie = session.cookies.get('ehwiki_session')
    soup = BeautifulSoup(r.content, 'html.parser')
    edit_input = soup.select('input[name="wpEditToken"]')[0]
    token_input = soup.select('input[name="wpLoginToken"]')[0]
    edit_token = edit_input.attrs.get('value')
    login_token = token_input.attrs.get('value')
    WIKI_LOGIN_DATA['wpEditToken'] = edit_token
    WIKI_LOGIN_DATA['wpLoginToken'] = login_token
    log.info( 'WIKI login: user %s, password ***, session %s, tokens %s|%s',
              WIKI_USERNAME, session_cookie, edit_token, login_token )
    time.sleep(GET_SLEEP)
    log.info('POST %s', url)
    rp = session.post(url, data=WIKI_LOGIN_DATA, headers=HEADERS)
    log.debug('HTTP %d', rp.status_code)
    if not rp.ok:
        raise RuntimeError("Can't continue without WIKI auth")
    log.info( 'WIKI login DONE with: %s', session.cookies)
    return session


tag_link = 'https://e-hentai.org/tools.php?act=taggroup&mastertag='
RE_TAG_NAMESPACE = re.compile('^[^:]+\:')
RE_GROUP_LINK = re.compile('^' + re.escape(tag_link))
def retrieve_tag_groups(session, map_name, grouping):
    '''
    Constructs a deep dictionary (`DeepDict`) from a single page of tag groups.
    It assigns the keys in the dictionary based on `map_name`.  The HTML parser
    assumes that the page in question uses a table for content styling, this
    may change in the future and the filter will need to be revisited.
    '''
    url = 'https://e-hentai.org/tools.php?act=taggroup&show=%d' % grouping
    log.info('GET %s', url)
    r = session.get(url, headers=HEADERS)
    log.debug('HTTP %d', r.status_code)
    soup = BeautifulSoup(r.content, 'html.parser')
    links = soup.select('td a')
    group = DeepDict()
    for l in links:
        tag_name = RE_TAG_NAMESPACE.sub('', l.text)
        group_number = int(RE_GROUP_LINK.sub('', l.attrs.get('href')))
        group[tag_name] = { map_name: group_number }
    log.debug(group)
    return session, group


TAG_GROUP_MISC_MAP = { 'misc': 0, 'reclass': 1, 'language': 2,
                       'parody': 3, 'character': 4,
                       'group': 5, 'artist': 6 }
TAG_GROUP_MALE_MAP = { 'male': 7 }
TAG_GROUP_FEMALE_MAP = { 'female': 8 }
TAG_GROUP_MAP = { 'female': TAG_GROUP_FEMALE_MAP,
                  'male': TAG_GROUP_MALE_MAP,
                  'misc': TAG_GROUP_MISC_MAP }
def build_group_struct(session):
    '''
    Walk through the maps of tag groups and build a `DeepDict` for each.  The
    deep dictionary will be a dictionary of dictionaries, which will have its
    internal dictionaries updated with more keys when two maps have the same
    tag name.  For example:

        { 'pantyhose': { 'male': 123 } }
        { 'pantyhose': { 'female': 456 } }

    Will result into:

        { 'pantyhose': { 'female': 456, 'male': 123 } }

    The keys in the internal dictionaries are then passed as parameters
    directly into `change_tag`.  This is why female and male tags are separated
    and all other groups are bundled together into misc.
    '''
    groups = DeepDict()
    for map_name, tag_map in TAG_GROUP_MAP.items():
        log.debug('Working on groups for %s map', map_name)
        for group_type, value in tag_map.items():
            if group_type not in NAMESPACE_LIST:
                log.debug('IGNORING %s', group_type)
                continue
            session, this_group = retrieve_tag_groups(session, map_name, value)
            total = len(this_group.keys())
            log.info('Got %d tag groups for %s', total, group_type)
            groups.update(this_group)
            time.sleep(GET_SLEEP)
    log.debug('All groups:\n%s', groups)
    log.info('Total of %d groups', len(groups.keys()))
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
    Inside /action/edit/ we can actually check the redirection markup
    (`#REDIRECT`) and act accordingly.
    '''
    url = 'https://ehwiki.org/wiki/%s' % tag
    log.info('GET %s', url)
    r = session.get(url, headers=HEADERS, allow_redirects=False)
    # any HTTP 2xx is good enough for us
    # but we can't use `r.ok` because it is True for HTTP 3xx
    success = 2 == r.status_code // 100
    log.debug('HTTP %d (%s)', r.status_code, success)
    time.sleep(GET_SLEEP)
    if success:
        url = 'https://ehwiki.org/action/edit/%s' % tag
        r = session.get(url, headers=HEADERS, allow_redirects=False)
        log.debug('HTTP %d', r.status_code)
        time.sleep(GET_SLEEP)
        soup = BeautifulSoup(r.content, 'html.parser')
        markup = soup.find('textarea').text
        if '#REDIRECT' in markup:
            log.debug('INTERNAL REDIRECT (True => False)')
            return session, False, r.status_code
    return session, success, r.status_code


def edit_template(tag, tag_def, female=None, male=None, misc=None):
    '''
    Makes the required edits to the wiki template (tag definition).
    If we do have a tag group (which we retrieved from EH) but the wiki page do
    not account for it, we fix the wiki page by adding the correct argument to
    it.  On the other hand, if the wiki page already has the argument in place
    we take care to not change the argument placement so that we do not mess
    with the wiki version control.

    This entire function is three times the same code duplicated.  Not the most
    elegant solution but makes debugging easy.
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
    can only guess the changes we need to do.  Without the template the markup
    can be written in may ways so we must attempt to edit the links directly.
    Either the old link using `taggroup=` directly or attempt to change a link
    with `mastertag=` in case someone may have attempted the change already.

    Attempt changing the `mastertag` link first otherwise we may change what we
    already placed in the definition by changing the `taggroup` parameter into
    the `mastertag` parameter.
    '''
    new_def = tag_def
    # due to URL changes and redirects the domain may be tricky
    new_t = 'https://e-hentai.org/tools.php?act=taggroup&mastertag=%d' % group
    new_def = RAW_MASTER_RE.sub(new_t, new_def)
    new_def = RAW_GROUP_RE.sub(new_t, new_def)
    log.info('tag:%s, mastertag => %d', tag, group)
    return new_def


WIKI_POST_DATA = {
    'wpStarttime'     : None,
    'wpEdittime'      : None,
    'wpAutoSummary'   : None,
    'oldid'           : None,
    'parentRevId'     : None,
    'format'          : 'text/x-wiki',
    'model'           : 'wikitext',
    'wpTextbox1'      : None,
    'wpSummary'       : SUMMARY,
    'wpWatchthis'     : 1,
    'wpSave'          : 'Save page',
    'wpEditToken'     : None,
    'wpUltimateParam' : 1
}
def change_tag(session, tag, female=None, male=None, misc=None):
    '''
    Gets the tag definition from the wiki page, change the tag groups and POST
    a new definition.  In other words, perform the actual work of this script,
    the remainder of the script is to setup the environment for this function
    and ensure that it is called correctly.

    We make several assumptions when calling this function.

    1.  The `session` is authenticated with enough permissions to perform the
    change.
    2.  The tag points to an existing page, not all tag groups have a wiki page
    therefore we need to verify this beforehand.
    3.  We pass the correct tag groups.

    A tag definition may use the `{{ContentTag` template or it may simply use
    raw wiki markup.  We are clever enough to distinguish that and perform the
    correct changes to the definition.  This should work well for at least 90%
    of all tag definitions on the wiki.
    '''
    url = 'https://ehwiki.org/action/edit/%s' % tag
    log.info('GET %s', url)
    r = session.get(url, headers=HEADERS)
    log.debug('HTTP %d', r.status_code)
    time.sleep(GET_SLEEP)
    soup = BeautifulSoup(r.content, 'html.parser')
    definition = soup.find('textarea').text
    log.debug('FROM:\n%s', definition)
    if re.search('{{ContentTag', definition):
        new_def = edit_template(tag, definition, female, male, misc)
    else:
        group = list(dropwhile(lambda x: not x, [misc, female, male]))[0]
        new_def = edit_raw_tag(tag, definition, group)
    log.debug('TO:\n%s', new_def)
    change_p = definition != new_def
    if not change_p:
        log.info('tag:%s: No changes to be made, bail', tag)
        # output to sdtout
        log_extra(change_p, r.status_code, tag, female, male, misc)
        return session
    log.info('tag:%s: POSTing change', tag)
    WIKI_POST_DATA['wpTextbox1'] = new_def
    # only now we want to invoke BeautifulSoup, since it is resource intensive
    soup = BeautifulSoup(r.content, 'html.parser')
    inputs = [ 'wpStarttime', 'wpEdittime', 'wpAutoSummary',
               'oldid', 'parentRevId', 'wpEditToken', 'wpUltimateParam' ]
    build_post_data(WIKI_POST_DATA, soup, *inputs)
    log.debug(WIKI_POST_DATA)
    log.info('POST %s', url)
    rp = session.post(url, data=WIKI_POST_DATA, headers=HEADERS)
    log.debug('HTTP %d', rp.status_code)
    time.sleep(POST_SLEEP)
    if not rp.ok:
        log.warning('Update for %s FAILED', tag)
    # output to sdtout
    log_extra(change_p, rp.status_code, tag, female, male, misc)
    return session


def drive_groups(session, groups):
    '''
    Checks if the master tag of a tag group exists on the wiki, it performs
    some fuzzy matching because we do not necessarily use the same names on the
    wiki and in the tag groups.
    '''
    for tag, gr in groups.items():
        log.debug('Search WIKI for tag %s -> %s', tag, gr)
        page_tag = None
        tries = [ tag.replace(' ', '_'),
                  tag.replace(' ', '_').replace('-', '_'),
                  tag,
                  tag.replace('-', '_'),
                  tag.replace('-', ' ') ]
        tried = []
        code = 404  # assume does not exist (HTTP 404)
        for tr in tries:
            if tr in tried:
                continue
            session, exists, code = retrieve_wiki_tag(session, tr)
            time.sleep(GET_SLEEP)
            if exists:
                page_tag = tr
                break
            tried.append(tr)
        if page_tag:
            log.debug('Found %s, changing', page_tag)
            change_tag(session, page_tag, **gr)
        else:
            log.info('No WIKI page for %s', tag)
            # output to sdtout
            log_extra(False, code, tag, **gr)
    return session


def serial_execution( eh_username=None, eh_password=None,
                      wiki_username=None, wiki_password=None ):
    '''
    Serially run each step in the order it needs to be executed.  This allows
    the script to be used as a module, although still needs the globals to be
    properly setup beforehand.  As a convenience (in case you are reading this
    directly in the documentation here are the required globals (module level
    variables):

        EH_USERNAME, EH_PASSWORD, WIKI_USERNAME and WIKI_PASSWORD

    Another option is to pass named options when calling this function.

    The logger settings are left to the caller, the script/module do not
    overwrite log settings and respect global logger settings.
    '''
    global EH_USERNAME, EH_PASSWORD, WIKI_USERNAME, WIKI_PASSWORD
    log.info('Start tag fixes')
    if eh_username:
        EH_USERNAME = eh_username
    if eh_password:
        EH_PASSWORD = eh_password
    if wiki_username:
        WIKI_USERNAME = wiki_username
    if wiki_password:
        WIKI_PASSWORD = wiki_password
    EH_LOGIN_DATA['UserName'] = EH_USERNAME
    EH_LOGIN_DATA['PassWord'] = EH_PASSWORD
    WIKI_LOGIN_DATA['wpName'] = WIKI_USERNAME
    WIKI_LOGIN_DATA['wpPassword'] = WIKI_PASSWORD
    eh_session = requests.Session()
    wiki_session = requests.Session()
    eh_session = auth_forums(eh_session)
    wiki_session = auth_wiki(wiki_session)
    time.sleep(POST_SLEEP)
    eh_session, groups = build_group_struct(eh_session)
    wiki_session = drive_groups(wiki_session, groups)
    log.info('Aaand we are done')


if '__main__' == __name__:
    EH_USERNAME = os.environ.get('EH_USERNAME')
    EH_PASSWORD = os.environ.get('EH_PASSWORD')
    WIKI_USERNAME = os.environ.get('WIKI_USERNAME')
    WIKI_PASSWORD = os.environ.get('WIKI_PASSWORD')
    if ( EH_USERNAME and EH_PASSWORD and
        WIKI_USERNAME and WIKI_PASSWORD and
        len(sys.argv) < 2 ):
        log.critical(__doc__)
        sys.exit(1)
    opts, args = getopt.getopt(sys.argv[1:], 'g:p:')
    try:
        for o, a in opts:
            if '-g' == o:
                GET_SLEEP = float(a)
            elif '-p' == o:
                POST_SLEEP = float(a)
            else:
                raise ValueError('Unknown argument %s' % o)
    except ValueError:
        log.critical(__doc__)
        sys.exit(1)
    # it is fine to reconfigure the logger at a later time
    format = '[%(asctime)s:%(levelname)8s:%(lineno)4s] %(message)s'
    try:
        logging.basicConfig(format=format, level=log_levels[args[0]])
    except (KeyError, IndexError):
        log.critical(__doc__)
        sys.exit(1)
    NAMESPACE_LIST = args[1:]
    log.info('NAMESPACE LIST: %s', NAMESPACE_LIST)
    log.info('GET SLEEP: %f', GET_SLEEP)
    log.info('POST SLEEP: %f', POST_SLEEP)
    serial_execution()

