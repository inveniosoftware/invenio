## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

__revision__ = "$Id$"

from invenio.config import accessurl, adminemail, cdslang, cdsname, weburl, version

def format(bfo, var=''):
    '''
    Print several server specific variables.
    @param var the name of the desired variable. Can be one of: name, lang, version, email, weburl, searchurl, recurl
           name: the name of the server
           lang: the default language of the server
           version: the software version
           email: the admin email
           weburl: the base url for the server
           searchurl: the search url for the server
           recurl: the base url for the record
    '''
    recID = bfo.recID
    if var == '':
        out =  ''
    elif var == 'name':
        out = cdsname
    elif var == 'lang':
        out = cdslang
    elif var == 'version':
        out = 'CDS Invenio v' + str(version)
    elif var == 'email':
        out = adminemail
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
