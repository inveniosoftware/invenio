## $Id$
##
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

"""CDS Invenio BibEdit Administrator Interface."""

__lastupdated__ = """$Date$"""
__version__     = "$Id$"

from invenio.config import cdslang, weburl
from invenio.webpage import page
from invenio.webuser import getUid, page_not_authorized
from invenio.bibedit_engine import perform_request_index, perform_request_edit, perform_request_submit
from invenio.search_engine import wash_url_argument
from invenio.access_control_engine import acc_authorize_action

navtrail    = """ <a class=navtrail href=\"%s/admin/\">Admin Area</a> &gt;
                  <a class=navtrail href=\"%s/admin/bibedit/\">BibEdit Admin</a> """ % (weburl, weburl)

def index(req, ln=cdslang, recid=None, temp="false", format_tag='marc',
          edit_tag=None, delete_tag=None, num_field=None, add=0, cancel=0,
          delete=0 ,confirm_delete=0,  **args):    
    """ BibEdit Admin interface. """

    uid = getUid(req)
    
    recid          = wash_url_argument(recid,          "int")
    add            = wash_url_argument(add,            "int")
    cancel         = wash_url_argument(cancel,         "int")
    delete         = wash_url_argument(delete,         "int")
    confirm_delete = wash_url_argument(confirm_delete, "int")
    
    (auth_code, auth_message) = acc_authorize_action(uid,'runbibedit')
    if auth_code == 0:
        (body, errors, warnings) = perform_request_index(ln, recid, cancel, delete, confirm_delete, uid, temp, format_tag,
                                                         edit_tag, delete_tag, num_field, add, args)
    else:
        return page_not_authorized(req=req, text=auth_message, navtrail=navtrail)

    if recid != 0:
        title = "Record #%i" % recid
        if add == 3:
            title += " - Add Field"
    else:
        title = "BibEdit Admin Interface"
        
    return page(title       = title,
                body        = body,
                errors      = errors,
                warnings    = warnings,
                uid         = getUid(req),
                language    = ln,
                navtrail    = navtrail,               
                lastupdated = __lastupdated__,
                req         = req) 


def edit(req, recid, tag, num_field='0', format_tag='marc',
         del_subfield=None, temp="false", add=0, ln=cdslang, **args):    
    """ Edit Field page. """

    uid       = getUid(req)
    recid     = wash_url_argument(recid,     "int")
    num_field = wash_url_argument(num_field, "int")
    add       = wash_url_argument(add,       "int")
    
    (body, errors, warnings) = perform_request_edit(ln, recid, uid, tag, num_field,
                                                    format_tag, temp, del_subfield, add, args)

    title = "Edit Record #%i Field #%s" % (recid, str(tag[:3]))
    if add == 1:
        title += " - Add Subfield"
        
    return page(title       = title,
                body        = body,
                errors      = errors,
                warnings    = warnings,
                uid         = getUid(req),
                language    = ln,
                navtrail    = navtrail,
                lastupdated = __lastupdated__,
                req         = req)    


def submit(req, recid, ln=cdslang):
    """ Submit temp_record on database. """

    recid = wash_url_argument(recid, "int")
    
    (body, errors, warnings) = perform_request_submit(ln, recid)
    
    return page(title       = "Submit and save record #%i" % recid,
                body        = body,
                errors      = errors,
                warnings    = warnings,
                uid         = getUid(req),
                language    = ln,
                navtrail    = navtrail,
                lastupdated = __lastupdated__,
                req         = req) 
