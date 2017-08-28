#!/usr/bin/env python
__doc__ = '''
    tricky_tags - print a list of double namespaced tags

This is a hack on top of `fix_tags`.  Works only if executed in the same
directory as `fix_tags`.

What we call tricky tags are the ones which have the same name across several
namespaces.  Whilst fetish tags spread across the female: and the male:
namespaces, all other namespaces should not have a tag with the same name.
Sometimes though the same names are used across different namespaces and we are
trying to find such cases since it is likely that they will need manual
adjustments every time we perform any automatic tag fixes.

The general logic is that any tag that exists in either female: or male:
namespace and also in any misc: based namespace is a tricky tag to deal with.
The exact logic is:

    tricky_tag <- (female: or male:) and misc:

These are parsed from dictionary keys in a `DeepDict`.
'''
__author__ = 'Neptune Penguin'
__copyright__ = 'Copyright (C) 2017 Aquamarine Penguin'
__license__ = 'GNU GPLv3 or later'
__date__ = '2017-08-21'
__version__ = '0.1'


import os, time, logging, requests
import fix_tags as ft


log = logging.getLogger(__name__)
format = '[%(asctime)s:%(levelname)8s:%(lineno)4s] %(message)s'
logging.basicConfig(format=format, level=logging.DEBUG)
ft.EH_USERNAME = os.environ.get('EH_USERNAME')
ft.EH_PASSWORD = os.environ.get('EH_PASSWORD')
ft.EH_LOGIN_DATA['UserName'] = ft.EH_USERNAME
ft.EH_LOGIN_DATA['PassWord'] = ft.EH_PASSWORD
ft.NAMESPACE_LIST = [ 'female', 'male', 'misc',
                      'reclass', 'language', 'parody',
                      'character', 'group', 'artist' ]
session = requests.Session()
session = ft.auth_forums(session)
time.sleep(1)
session, groups = ft.build_group_struct(session)
for tag, spaces in groups.items():
    if not ('misc' in spaces and ('female' in spaces or 'male' in spaces)):
        continue
    print(tag, '->', spaces)
    print('https://ehwiki.org/wiki/%s' % tag.replace(' ', '_'))
    for key, value in spaces.items():
        print(key, ':',
              'https://e-hentai.org/tools.php?act=taggroup&mastertag=%d' %
              value)

