## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
"""BibFormat element - Prints server info
"""

from invenio.config import CFG_SITE_URL, CFG_BASE_URL, CFG_SITE_ADMIN_EMAIL, CFG_SITE_LANG, \
        CFG_SITE_NAME, CFG_VERSION, CFG_SITE_NAME_INTL, CFG_SITE_SUPPORT_EMAIL, \
        CFG_SITE_RECORD


def format_element(bfo, var=''):
    '''
    Print several server specific variables.
    @param var: the name of the desired variable. Can be one of: CFG_SITE_NAME, CFG_SITE_NAME_INTL, CFG_SITE_LANG, CFG_VERSION, CFG_SITE_ADMIN_EMAIL, CFG_SITE_SUPPORT_EMAIL, CFG_SITE_URL, searchurl, recurl
           CFG_SITE_NAME: the name of the server
           CFG_SITE_NAME_INTL: internationalized name
           CFG_SITE_LANG: the default language of the server
           CFG_VERSION: the software version
           CFG_SITE_ADMIN_EMAIL: the admin email
           CFG_SITE_SUPPORT_EMAIL: the support email
           CFG_SITE_URL: the base url for the server
           searchurl: the search url for the server
           recurl: the base url for the record
    '''
    recID = bfo.recID
    if var == '':
        out = ''
    elif var in ['name', 'CFG_SITE_NAME']:
        out = CFG_SITE_NAME
    elif var in ['i18n_name', 'CFG_SITE_NAME_INTL']:
        out = CFG_SITE_NAME_INTL.get(bfo.lang, CFG_SITE_NAME)
    elif var in ['lang', 'CFG_SITE_LANG']:
        out = CFG_SITE_LANG
    elif var == 'CFG_VERSION':
        out = 'Invenio v' + str(CFG_VERSION)
    elif var in ['email', 'admin_email', 'CFG_SITE_ADMIN_EMAIL']:
        out = CFG_SITE_ADMIN_EMAIL
    elif var in ['support_email', 'CFG_SITE_SUPPORT_EMAIL']:
        out = CFG_SITE_SUPPORT_EMAIL
    elif var in ['CFG_SITE_RECORD']:
        out = CFG_SITE_RECORD
    elif var in ['weburl', 'CFG_SITE_URL']:
        out = CFG_SITE_URL
        if not out.endswith('/'):
            out += '/'
    elif var in ['CFG_BASE_URL']:
        out = CFG_BASE_URL
        if not out.endswith('/'):
            out += '/'
    elif var == 'searchurl':
        out = CFG_BASE_URL + '/search'
        if not out.endswith('/'):
            out += '/'
    elif var == 'absolutesearchurl':
        out = CFG_SITE_URL + '/search'
        if not out.endswith('/'):
            out += '/'
    elif var == 'recurl':
        out = CFG_BASE_URL
        if not out.endswith('/'):
            out += '/'
        out += CFG_SITE_RECORD + '/' + str(recID)
    elif var == 'absoluterecurl':
        out = CFG_SITE_URL
        if not out.endswith('/'):
            out += '/'
        out += CFG_SITE_RECORD + '/' + str(recID)
    else:
        out = 'Unknown variable: %s' % (var)
    return out
