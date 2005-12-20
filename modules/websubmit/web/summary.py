## $Id$

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

## import interesting modules:
import string
import os
import sys
import time

from cdsware.config import cdsname,cdslang
from cdsware.dbquery import run_sql
from cdsware.access_control_engine import acc_authorize_action
from cdsware.websubmit_config import *
from cdsware.webpage import page, create_error_box
from cdsware.webuser import getUid,get_email, page_not_authorized
from cdsware.messages import *
from cdsware.access_control_config import CFG_ACCESS_CONTROL_LEVEL_SITE

from cdsware.messages import gettext_set_language
import cdsware.template
websubmit_templates = cdsware.template.load('websubmit')

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

