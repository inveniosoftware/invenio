## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
"""BibFormat element - Prints server info
"""
__revision__ = "$Id$"

from invenio.config import accessurl, CFG_SITE_ADMIN_EMAIL, CFG_SITE_LANG, CFG_SITE_NAME, weburl, CFG_VERSION, CFG_SITE_NAME_INTL, CFG_SITE_SUPPORT_EMAIL

# FIXME: new cfg variable names like CFG_VERSION

def format(bfo, var=''):
    '''
    Print several server specific variables.
    @param var the name of the desired variable. Can be one of: name, i18n_name, lang, CFG_VERSION, admin_email, support_email, weburl, searchurl, recurl
           name: the name of the server
           i18n_name: internationalized name
           lang: the default language of the server
           CFG_VERSION: the software version
           admin_email: the admin email
           support_email: the support email
           weburl: the base url for the server
           searchurl: the search url for the server
           recurl: the base url for the record
    '''
    recID = bfo.recID
    if var == '':
        out =  ''
    elif var == 'name':
        out = CFG_SITE_NAME
    elif var == 'i18n_name':
        out = CFG_SITE_NAME_INTL.get(bfo.lang, CFG_SITE_NAME)
    elif var == 'lang':
        out = CFG_SITE_LANG
    elif var == 'CFG_VERSION':
        out = 'CDS Invenio v' + str(CFG_VERSION)
    elif var in ['email', 'admin_email']:
        out = CFG_SITE_ADMIN_EMAIL
    elif var == 'support_email':
        out = CFG_SITE_SUPPORT_EMAIL
    elif var == 'weburl':
        out = weburl
        if not out.endswith('/'):
            out += '/'
    elif var == 'searchurl':
        out = accessurl
        if not out.endswith('/'):
            out += '/'
    elif var == 'recurl':
        out = weburl
        if not out.endswith('/'):
            out += '/'
        out += 'record/' + str(recID)
    else:
        out = 'Unknown variable: %s' % (var)
    return out
