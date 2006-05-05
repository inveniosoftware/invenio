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

## import interesting modules:
import string
import os
import time
import types
import re
from mod_python import apache
import sys

from invenio.config import cdsname,cdslang
from invenio.access_control_engine import acc_authorize_action
from invenio.access_control_admin import acc_isRole
from invenio.webpage import page, create_error_box
from invenio.webuser import getUid, get_email, page_not_authorized
from invenio.websubmit_config import *
from invenio.file import *
from invenio.access_control_config import CFG_ACCESS_CONTROL_LEVEL_SITE

from invenio.messages import gettext_set_language
import invenio.template
websubmit_templates = invenio.template.load('websubmit')

def index(req,c=cdsname,ln=cdslang,recid="",docid="",version="",name="",format=""):
    # load the right message language
    _ = gettext_set_language(ln)

    # get user ID:
    try:
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../getfile.py/index")
        uid_email = get_email(uid)
    except MySQLdb.Error, e:
        return errorMsg(e.value,req)
    docfiles = []
    t=""
    filelist=""
    ip=str(req.get_remote_host(apache.REMOTE_NOLOOKUP))
    # if a precise file is requested, we stream it
    if name!="":
        if docid=="":
            return errorMsg(_("Parameter docid missing"), req, c, ln)
        else:
            doc = BibDoc(bibdocid=docid)
            docfile=doc.getFile(name,format,version)
            if docfile == None:
                return warningMsg(_("can't find file..."),req, c, ln)
            else:
                res = doc.registerDownload(ip, version, format, uid)
                return docfile.stream(req)
    # all files attached to a record
    elif recid!="":
        bibarchive = BibRecDocs(recid)
        filelist = bibarchive.display(docid, version, ln = ln)
    # a precise filename
    elif docid!="":
        bibdoc = BibDoc(bibdocid=docid)
        recid = bibdoc.getRecid()
        filelist = bibdoc.display(version, ln = ln)
    t = websubmit_templates.tmpl_filelist(
          ln = ln,
          recid = recid,
          docid = docid,
          version = version,
          filelist = filelist,
        )
    p_navtrail = _("Access to Fulltext")
    return page(title="",
                body=t,
                navtrail = p_navtrail,
                description="",
                keywords="keywords",
                uid=uid,
                language=ln,
                urlargs=req.args
               )

def errorMsg(title,req,c=cdsname,ln=cdslang):
    _ = gettext_set_language(ln)
    return page(title=_("Error"),
                    body = create_error_box(req, title=title,verbose=0, ln=ln),
                    description=_("%s - Internal Error") % c,
                    keywords="%s, CDS Invenio, Internal Error" % c,
                    language=ln,
                    urlargs=req.args)

def warningMsg(title,req,c=cdsname,ln=cdslang):
    _ = gettext_set_language(ln)
    return page(title=_("Warning"),
                    body = title,
                    description=_("%s - Internal Error") % c,
                    keywords="%s, CDS Invenio, Internal Error" % c,
                    language=ln,
                    urlargs=req.args)

