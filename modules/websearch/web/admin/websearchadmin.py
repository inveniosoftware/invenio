## $Id$
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

"""CDS Invenio WebSearch Administrator Interface."""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

import sys

import invenio.websearchadminlib as wsc
from invenio.bibrankadminlib import check_user
from invenio.webpage import page, create_error_box, adderrorbox
from invenio.config import weburl, sweburl, cdslang, cdsname
from invenio.dbquery import Error
from invenio.webuser import getUid, page_not_authorized
from invenio.messages import gettext_set_language
from invenio.urlutils import wash_url_argument

def switchfmtscore(req, colID, type, id_1, id_2, ln=cdslang):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_switchfmtscore(colID=colID,
                                                ln=ln,
                                                type=type,
                                                id_1=id_1,
                                                id_2=id_2),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def switchfldscore(req, colID, id_1, id_2, fmeth, ln=cdslang):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_switchfldscore(colID=colID,
                                                ln=ln,
                                                id_1=id_1,
                                                id_2=id_2,
                                                fmeth=fmeth),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def switchfldvaluescore(req, colID, id_1, id_fldvalue_1, id_fldvalue_2, ln=cdslang):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_switchfldvaluescore(colID=colID,
                                                ln=ln,
                                                id_1=id_1,
                                                id_fldvalue_1=id_fldvalue_1,
                                                id_fldvalue_2=id_fldvalue_2),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def runwebcoll(req, colID, ln=cdslang, confirm=0):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="WebSearch Admin",
                    body=wsc.perform_checkwebcollstatus(colID=colID,
                                                        ln=ln,
                                                        confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def switchpbxscore(req, colID, id_1, id_2, sel_ln,ln=cdslang):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_switchpbxscore(colID=colID,
                                                ln=ln,
                                                id_1=id_1,
                                                id_2=id_2,
                                                sel_ln=sel_ln),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def modifydbquery(req, colID, ln=cdslang, dbquery='', confirm=-1):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_modifydbquery(colID=colID,
                                               ln=ln,
                                               dbquery=dbquery,
                                               confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def showtree(req, colID, ln=cdslang):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Collection tree",
                    body=wsc.perform_showtree(colID=colID,
                                              ln=ln),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def modifytranslations(req, colID, ln=cdslang, sel_type='', trans = [], confirm=-1):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_modifytranslations(colID=colID,
                                             ln=ln,
                                             sel_type=sel_type,
                                             trans=trans,
                                             confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def addcollectiontotree(req, colID, ln=cdslang, add_dad='', add_son='', rtype='', mtype='', callback='yes', confirm=-1):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="WebSearch Admin",
                body=wsc.perform_addcollectiontotree(colID=colID,
                                               ln=cdslang,
                                               add_dad=add_dad,
                                               add_son=add_son,
                                               rtype=rtype,
                                               callback=callback,
                                               confirm=confirm),
                uid=uid,
                language=ln,
                navtrail = navtrail_previous_links,
                req=req,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def addcollection(req, colID, ln=cdslang, colNAME='', dbquery='', callback="yes", confirm=-1):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="WebSearch Admin",
                body=wsc.perform_addcollection(colID=colID,
                                               ln=cdslang,
                                               colNAME=colNAME,
                                               dbquery=dbquery,
                                               callback=callback,
                                               confirm=confirm),
                uid=uid,
                language=ln,
                navtrail = navtrail_previous_links,
                req=req,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def modifyrankmethods(req, colID, ln=cdslang, func='', rnkID='', confirm=0):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_modifyrankmethods(colID=colID,
                                                 ln=ln,
                                                 func=func,
                                                 rnkID=rnkID,
                                                 confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def deletecollection(req, colID, ln=cdslang, confirm=-1):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_deletecollection(colID=colID,
                                                 ln=ln,
                                                 confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def editcollection(req, colID=1, ln=cdslang, mtype=''):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_editcollection(colID=colID,
                                                ln=ln,
                                                mtype=mtype),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def addoutputformat(req, colID, ln=cdslang, code='', name='', callback='yes', confirm=-1):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)


    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_addoutputformat(colID=colID,
                                                 ln=ln,
                                                 code=code,
                                                 name=name,
                                                 callback=callback,
                                                 confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def showoutputformats(req, colID, ln=cdslang, callback='yes', confirm=0):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_showoutputformats(colID=colID,
                                                 ln=ln,
                                                 callback=callback,
                                                 confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def addexistingoutputformat(req, colID, ln=cdslang, fmtID=-1, callback='yes', confirm=-1):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_addexistingoutputformat(colID=colID,
                                                         ln=ln,
                                                         fmtID=fmtID,
                                                         callback=callback,
                                                         confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def deleteoutputformat(req, colID, ln=cdslang, fmtID=-1, callback='yes', confirm=-1):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_deleteoutputformat(colID=colID,
                                                 ln=ln,
                                                 fmtID=fmtID,
                                                 callback=callback,
                                                 confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def removeoutputformat(req, colID, ln=cdslang, fmtID='', callback='yes', confirm=0):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_removeoutputformat(colID=colID,
                                                    ln=ln,
                                                    fmtID=fmtID,
                                                    callback=callback,
                                                    confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def update_external_collections(req, colID, ln=cdslang, state=None, recurse=None):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body = wsc.perform_update_external_collections(colID, ln, state, recurse),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def update_detailed_record_options(req, colID, ln=cdslang, tabs=[], recurse=0):
    """Update the preferences for the tab to show/hide in the detailed record page. """

    _tabs = wash_url_argument(tabs, 'list')
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                    body = wsc.perform_update_detailed_record_options(colID, ln, _tabs, recurse),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def removefieldvalue(req, colID, ln=cdslang, fldID='', fldvID='', fmeth='', callback='yes', confirm=0):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_removefieldvalue(colID=colID,
                                             ln=ln,
                                             fldID=fldID,
                                             fldvID=fldvID,
                                             fmeth=fmeth,
                                             callback=callback,
                                             confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


def removefield(req, colID, ln=cdslang, fldID='', fldvID='', fmeth='', callback='yes', confirm=0):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_removefield(colID=colID,
                                             ln=ln,
                                             fldID=fldID,
                                             fldvID=fldvID,
                                             fmeth=fmeth,
                                             callback=callback,
                                             confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def modifyfield(req, colID, fldID, fldvID='', ln=cdslang, callback='yes', confirm=0):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
        	body=wsc.perform_modifyfield(colID=colID,
                                             fldID=fldID,
                                             fldvID=fldvID,
                                             ln=ln,
                                             callback=callback,
                                             confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def modifyoutputformat(req, colID, ln=cdslang, fmtID=-1, sel_type='', trans=[], confirm=-1):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_modifyoutputformat(colID=colID,
                                                    ln=ln,
                                                    fmtID=fmtID,
                                                    sel_type=sel_type,
                                                    trans=trans,
                                                    confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def showsearchoptions(req, colID, ln=cdslang, callback='yes', confirm=0):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_showsearchoptions(colID=colID,
                                                   ln=ln,
                                                   callback=callback,
                                                   confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def addexistingfield(req, colID, ln=cdslang, fldID=-1, fldvID=-1, fmeth='', callback='yes', confirm=-1):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_addexistingfield(colID=colID,
                                                  ln=ln,
                                                  fldID=fldID,
                                                  fldvID=fldvID,
                                                  fmeth=fmeth,
                                                  callback=callback,
                                                  confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page(title='Authorization failure',
                uid=uid,
                body=adderrorbox('try to login first',
                                     datalist=["""You are not a user authorized to perform admin tasks, try to
                                     <a href="%s/youraccount/login?referer=%s/admin/websearch/websearchadmin.py/">login</a> with another account.""" % (sweburl, weburl)]),
                navtrail= navtrail_previous_links,
                lastupdated=__lastupdated__)

def rearrangefield(req, colID, ln=cdslang, fmeth='', callback='yes', confirm=-1):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_rearrangefield(colID=colID,
                                                  ln=ln,
                                                  fmeth=fmeth,
                                                  callback=callback,
                                                  confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page(title='Authorization failure',
                uid=uid,
                body=adderrorbox('try to login first',
                                     datalist=["""You are not a user authorized to perform admin tasks, try to
                                     <a href="%s/youraccount/login?referer=%s/admin/websearch/websearchadmin.py/">login</a> with another account.""" % (sweburl, weburl)]),
                navtrail= navtrail_previous_links,
                lastupdated=__lastupdated__)

def addexistingfieldvalue(req, colID, fldID, ln=cdslang, callback='yes', confirm=-1):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_addexistingfieldvalue(colID=colID,
                                                  ln=ln,
                                                  fldID=fldID,
                                                  callback=callback,
                                                  confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page(title='Authorization failure',
                uid=uid,
                body=adderrorbox('try to login first',
                                     datalist=["""You are not a user authorized to perform admin tasks, try to
                                     <a href="%s/youraccount/login?referer=%s/admin/websearch/websearchadmin.py/">login</a> with another account.""" % (sweburl, weburl)]),
                navtrail= navtrail_previous_links,
                lastupdated=__lastupdated__)

def rearrangefieldvalue(req, colID, fldID, ln=cdslang, callback='yes', confirm=-1):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_rearrangefieldvalue(colID=colID,
                                                  ln=ln,
                                                  fldID=fldID,
                                                  callback=callback,
                                                  confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page(title='Authorization failure',
                uid=uid,
                body=adderrorbox('try to login first',
                                     datalist=["""You are not a user authorized to perform admin tasks, try to
                                     <a href="%s/youraccount/login?referer=%s/admin/websearch/websearchadmin.py/">login</a> with another account.""" % (sweburl, weburl)]),
                navtrail= navtrail_previous_links,
                lastupdated=__lastupdated__)

def addnewfieldvalue(req, colID, fldID, ln=cdslang, name='', value='', callback="yes", confirm=-1):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                    body=wsc.perform_addnewfieldvalue(colID=colID,
  					      fldID=fldID,
                                              ln=cdslang,
                                              name=name,
                                              value=value,
                                              callback=callback,
                                              confirm=confirm),
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    req=req,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def modifyfieldvalue(req, colID, fldID, fldvID, ln=cdslang, name='', value='', callback="yes", confirm=-1):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                    body=wsc.perform_modifyfieldvalue(colID=colID,
  					      fldID=fldID,
                                              fldvID=fldvID,
                                              ln=cdslang,
                                              name=name,
                                              value=value,
                                              callback=callback,
                                              confirm=confirm),
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    req=req,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def showsearchfields(req, colID, ln=cdslang, callback='yes', confirm=0):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_showsearchfields(colID=colID,
                                                  ln=ln,
                                                  callback=callback,
                                                  confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def showsortoptions(req, colID, ln=cdslang, callback='yes', confirm=0):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_showsortoptions(colID=colID,
                                                 ln=ln,
                                                 callback=callback,
                                                 confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def modifyportalbox(req, colID, ln=cdslang, pbxID=-1, score='', position='', sel_ln='', title='', body='', callback='yes', confirm=-1):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_modifyportalbox(colID=colID,
                                                 ln=ln,
                                                 pbxID=pbxID,
                                                 score=score,
                                                 position=position,
                                                 sel_ln=sel_ln,
                                                 title=title,
                                                 body=body,
                                                 callback=callback,
                                                 confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def removeportalbox(req, colID, ln=cdslang, pbxID='', sel_ln='', callback='yes', confirm=0):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_removeportalbox(colID=colID,
                                                 ln=ln,
                                                 pbxID=pbxID,
                                                 sel_ln=sel_ln,
                                                 callback=callback,
                                                 confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def addexistingportalbox(req, colID, ln=cdslang, pbxID=-1, score=0, position='', sel_ln='', callback='yes', confirm=0):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_addexistingportalbox(colID=colID,
                                                      ln=ln,
                                                      pbxID=pbxID,
                                                      score=score,
                                                      position=position,
                                                      sel_ln=sel_ln,
                                                      callback=callback,
                                                      confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page(title='Authorization failure',
                uid=uid,
                body=adderrorbox('try to login first',
                                     datalist=["""You are not a user authorized to perform admin tasks, try to
                                     <a href="%s/youraccount/login?referer=%s/admin/websearch/websearchadmin.py/">login</a> with another account.""" % (sweburl, weburl)]),
                navtrail= navtrail_previous_links,
                lastupdated=__lastupdated__)

def deleteportalbox(req, colID, ln=cdslang, pbxID=-1, callback='yes', confirm=-1):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)


    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_deleteportalbox(colID=colID,
                                                 ln=ln,
                                                 pbxID=pbxID,
                                                 callback=callback,
                                                 confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def showportalboxes(req, colID, ln=cdslang, callback='yes', confirm=0):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)


    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)


    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_showportalboxes(colID=colID,
                                                 ln=ln,
                                                 callback=callback,
                                                 confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def addportalbox(req, colID, ln=cdslang, title='', body='', callback='yes', confirm=-1):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="Edit Collection",
                body=wsc.perform_addportalbox(colID=colID,
                                              ln=ln,
                                              title=title,
                                              body=body,
                                              callback=callback,
                                              confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def modifycollectiontree(req, colID, ln=cdslang, move_up='', move_down='', move_from='', move_to='', delete='', rtype='', callback='yes', confirm=0):
    navtrail_previous_links = wsc.getnavtrail() + """&gt; <a class=navtrail href="%s/admin/websearch/websearchadmin.py/">WebSearch Admin</a> """ % (weburl)

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="WebSearch Admin",
                body=wsc.perform_modifycollectiontree(colID=colID,
                                       ln=ln,
                                       move_up=move_up,
                                       move_down=move_down,
                                       move_from=move_from,
                                       move_to=move_to,
                                       delete=delete,
                                       rtype=rtype,
                                       callback=callback,
                                       confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def index(req, colID=1, ln=cdslang, mtype='', content='', confirm=0):
    navtrail_previous_links = wsc.getnavtrail()

    try:
        uid = getUid(req)
    except Error, e:
        return error_page(req)

    auth = check_user(req,'cfgwebsearch')
    if not auth[0]:
        return page(title="WebSearch Admin",
                body=wsc.perform_index(colID=colID,
                                       ln=ln,
                                       mtype=mtype,
                                       content=content,
                                       confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def error_page(req, ln=cdslang, verbose=1):
    _ = gettext_set_language(ln)

    return page(title=_("Internal Error"),
                body = create_error_box(req, verbose=verbose, ln=ln),
                description="%s - Internal Error" % cdsname,
                keywords="%s, Internal Error" % cdsname,
                language=ln,
                req=req)
