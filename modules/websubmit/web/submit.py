## $Id$
##
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
import types
import re
from mod_python import apache

from cdsware.config import cdsname,cdslang
from cdsware.access_control_engine import acc_authorize_action
from cdsware.access_control_admin import acc_isRole
from cdsware.webpage import page, create_error_box
from cdsware.webuser import getUid, get_email, page_not_authorized
from cdsware.messages import *
from cdsware.websubmit_config import *
from cdsware.websubmit_engine import *
from cdsware.access_control_config import CFG_ACCESS_CONTROL_LEVEL_SITE

def index(req,c=cdsname,ln=cdslang, doctype="", act="", startPg=1, indir="", access="",mainmenu="",fromdir="",file="",nextPg="",nbPg="",curpage=1,step=0,mode="U"):

    uid = getUid(req)
    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
        return page_not_authorized(req, "../submit.py/index")

    if doctype=="":
        return home(req,c,ln)
    elif act=="":
        return action(req,c,ln,doctype)
    elif int(step)==0:
        return interface(req,c,ln, doctype, act, startPg, indir, access,mainmenu,fromdir,file,nextPg,nbPg,curpage)
    else:
        return endaction(req,c,ln, doctype, act, startPg, indir, access,mainmenu,fromdir,file,nextPg,nbPg,curpage,step,mode)
        

