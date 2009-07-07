# -*- coding: utf-8 -*-
## $Id: bfe_webjournal_widget_forTheEyes.py,v 1.4 2008/01/08 15:45:45 ghase Exp $
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

from invenio.bibformat_engine import BibFormatObject
from invenio.config import weburl, etcdir
from invenio.webjournal_utils import parse_url_string


def format(bfo):
    """
    """
    args = parse_url_string(bfo.req)
    try:
        journal_name = args["name"]
    except KeyError:
        # todo: ERROR, no journal name provided
        return "ERROR, no name provided"
    #journal_name = "CERNBulletin"
    try:
        feature_file = open('%s/webjournal/%s/featured_record' % (etcdir, journal_name))
    except:
        return ""
    recid = feature_file.readline()
    url = feature_file.readline()
    feature_file.close()
    featured_record = BibFormatObject(recid)
    #featured_record.field('8564_x')
    
    if bfo.lang == 'fr':
        title = featured_record.field('246_1a')
    else:
        title = featured_record.field('245__a')
        
    html_out = '''
        <a href="%s/record/%s">
            <img src="%s" alt="#" width="100" class="phr" />
            %s
        </a>
    ''' % (weburl, recid, url, title)
    
    return html_out
    
def escape_values(bfo):
    """
    """
    return 0 
        
if __name__ == "__main__":
    myrec = BibFormatObject(16)
    format(myrec)