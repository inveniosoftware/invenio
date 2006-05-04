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

## import interesting modules:
import string
import os
import sys
import time
import types
import re
from mod_python import apache

from invenio.config import cdsname,cdslang
from invenio.access_control_engine import acc_authorize_action
from invenio.access_control_admin import acc_isRole
from invenio.websubmit_config import *
from invenio.webpage import page, create_error_box
from invenio.webuser import getUid, get_email, page_not_authorized
from invenio.access_control_config import CFG_ACCESS_CONTROL_LEVEL_SITE

def index(req,c=cdsname,ln=cdslang):
    uid = getUid(req)
    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
        return page_not_authorized(req, "../sub.py/index")

    myQuery = req.args
    if myQuery:
        if re.search("@",myQuery):
            param = re.sub("@.*","",myQuery)
            IN = re.sub(".*@","",myQuery)
        else:
            IN = myQuery
        url = "%s/direct.py?sub=%s&%s" % (urlpath,IN,param)
        req.err_headers_out.add("Location", url)
        raise apache.SERVER_RETURN, apache.HTTP_MOVED_PERMANENTLY
        return ""
    else:
        return "<html>Illegal page access</html>"

