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
import sys
import time

from invenio.config import cdsname,cdslang
from invenio.dbquery import run_sql
from invenio.access_control_engine import acc_authorize_action
from invenio.websubmit_config import *
from invenio.webpage import page, create_error_box
from invenio.webuser import getUid,get_email, page_not_authorized
from invenio.access_control_config import CFG_ACCESS_CONTROL_LEVEL_SITE

from invenio.messages import gettext_set_language
import invenio.template
websubmit_templates = invenio.template.load('websubmit')

def index(req,doctype="",act="",access="",indir="", ln=cdslang):
    uid = getUid(req)
    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
        return page_not_authorized(req, "../summary.py/index")

    t=""
    curdir = "%s/%s/%s/%s" % (storage,indir,doctype,access)
    subname = "%s%s" % (act,doctype)
    res = run_sql("select sdesc,fidesc,pagenb,level from sbmFIELD where subname=%s order by pagenb,fieldnb", (subname,))
    nbFields = 0

    values = []
    for arr in res:
        if arr[0] != "":
            val = {
                   'mandatory' : (arr[3] == 'M'),
                   'value' : '',
                   'page' : arr[2],
                   'name' : arr[0],
                  }
            if os.path.exists("%s/%s" % (curdir,arr[1])):
                fd = open("%s/%s" % (curdir,arr[1]),"r")
                value = fd.read()
                fd.close()
                value = value.replace("\n"," ")
                value = value.replace("Select:","")
            else:
                value = ""
            val['value'] = value
            values.append(val)

    return websubmit_templates.tmpl_submit_summary(
             ln = ln,
             values = values,
             images = images,
           )

