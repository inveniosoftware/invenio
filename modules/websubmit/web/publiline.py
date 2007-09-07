## $Id$

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

"""
publiline_complex.py --  implementes ...

  actors in this process are:

        1. author -- subilmts ...
        2. edi
        3; ref

Il ne faut pas oublier de definir les roles...
"""

__revision__ = "$Id$"

## import interesting modules:
import string
import os
import sys
import time
import types
import re
import shutil

from invenio.config import \
     CFG_ACCESS_CONTROL_LEVEL_SITE, \
     accessurl, \
     adminemail, \
     cdslang, \
     cdsname, \
     images, \
     pylibdir, \
     storage, \
     supportemail, \
     sweburl, \
     urlpath, \
     version
from invenio.dbquery import run_sql, Error
from invenio.access_control_engine import acc_authorize_action
from invenio.access_control_admin import *
from invenio.webpage import page, create_error_box
from invenio.webuser import getUid, get_email, list_registered_users, page_not_authorized
from invenio.messages import gettext_set_language, wash_language
from invenio.websubmit_config import *
from invenio.search_engine import search_pattern
from invenio.websubmit_functions.Retrieve_Data import Get_Field
from invenio.mailutils import send_email
from invenio.urlutils import wash_url_argument
from invenio.webgroup_dblayer import get_group_infos, insert_new_group, insert_new_member, delete_member
from invenio.webaccessadmin_lib import cleanstring_email
from invenio.access_control_config import MAXSELECTUSERS
from invenio.access_control_admin import acc_get_user_email
from invenio.webmessage import perform_request_send, perform_request_write_with_search
import invenio.webbasket_dblayer as basketdb
from invenio.webbasket_config import CFG_WEBBASKET_SHARE_LEVELS, CFG_WEBBASKET_CATEGORIES, CFG_WEBBASKET_SHARE_LEVELS_ORDERED
from invenio.webbasket import perform_request_display_item, perform_request_save_comment
from invenio.websubmit_functions.Retrieve_Data import Get_Field

execfile("%s/invenio/websubmit_functions/Retrieve_Data.py" % pylibdir)

import invenio.template
websubmit_templates = invenio.template.load('websubmit')

def index(req,c=cdsname,ln=cdslang,doctype="",categ="",RN="",send="",flow="",apptype="", action="", email_user_pattern="", id_user="", id_user_remove="", validate="", id_user_val="", msg_subject="", msg_body=""):
    global uid

    ln = wash_language(ln)
    categ = wash_url_argument(categ, 'str')
    RN = wash_url_argument(RN, 'str')
    send = wash_url_argument(send, 'str')
    flow = wash_url_argument(flow, 'str')
    apptype = wash_url_argument(apptype, 'str')
    action = wash_url_argument(action, 'str')
    email_user_pattern = wash_url_argument(email_user_pattern, 'str')
    id_user = wash_url_argument(id_user, 'int')
    id_user_remove = wash_url_argument(id_user_remove, 'int')
    validate = wash_url_argument(validate, 'str')
    id_user_val = wash_url_argument(id_user_val, 'int')
    msg_subject = wash_url_argument(msg_subject, 'str')
    msg_body = wash_url_argument(msg_body, 'str')

    # load the right message language
    _ = gettext_set_language(ln)

    t=""
    # get user ID:
    try:
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../publiline.py/index",
                                       navmenuid='yourapprovals')
        uid_email = get_email(uid)
    except Error, e:
        return errorMsg(e.value,req, ln = ln)
    if flow == "cplx":
        if doctype == "":
            t = selectCplxDoctype(ln)
        elif (categ == "") or (apptype == ""):
            t = selectCplxCateg(doctype, ln)
        elif RN == "":
            t = selectCplxDocument(doctype, categ, apptype, ln)
        elif action == "":
            t = displayCplxDocument(req, doctype, categ, RN, apptype, ln)
        else:
            t = doCplxAction(req, doctype, categ, RN, apptype, action, email_user_pattern, id_user, id_user_remove, validate, id_user_val, msg_subject, msg_body, ln)
        return page(title="specific publication line",
                    navtrail= """<a class="navtrail" href="%(sweburl)s/youraccount/display">%(account)s</a>""" % {
                                 'sweburl' : sweburl,
                                 'account' : _("Your Account"),
                              },
                    body=t,
                    description="",
                    keywords="",
                    uid=uid,
                    language=ln,
                    req=req,
                    navmenuid='yourapprovals')
    else:
        if doctype == "":
            t = selectDoctype(ln)
        elif categ == "":
            t = selectCateg(doctype, ln)
        elif RN == "":
            t = selectDocument(doctype, categ, ln)
        else:
            t = displayDocument(req, doctype, categ, RN, send, ln)
        return page(title="publication line",
                    navtrail= """<a class="navtrail" href="%(sweburl)s/youraccount/display">%(account)s</a>""" % {
                                 'sweburl' : sweburl,
                                 'account' : _("Your Account"),
                              },
                    body=t,
                    description="",
                    keywords="",
                    uid=uid,
                    language=ln,
                    req=req,
                    navmenuid='yourapprovals')

def selectDoctype(ln = cdslang):
    res = run_sql("select DISTINCT doctype from sbmAPPROVAL")
    docs = []
    for row in res:
        res2 = run_sql("select ldocname from sbmDOCTYPE where sdocname=%s", (row[0],))
        docs.append({
                     'doctype' : row[0],
                     'docname' : res2[0][0],
                    })
    t = websubmit_templates.tmpl_publiline_selectdoctype(
          ln = ln,
          docs = docs,
        )
    return t

def selectCplxDoctype(ln = cdslang):
    res = run_sql("select DISTINCT doctype from sbmCPLXAPPROVAL")
    docs = []
    for row in res:
        res2 = run_sql("select ldocname from sbmDOCTYPE where sdocname=%s", (row[0],))
        docs.append({
                     'doctype' : row[0],
                     'docname' : res2[0][0],
                    })
    t = websubmit_templates.tmpl_publiline_selectcplxdoctype(
          ln = ln,
          docs = docs,
        )
    return t

def selectCateg(doctype, ln = cdslang):
    t=""
    res = run_sql("select ldocname from sbmDOCTYPE where sdocname=%s",(doctype,))
    title = res[0][0]
    sth = run_sql("select * from sbmCATEGORIES where doctype=%s order by lname",(doctype,))
    if len(sth) == 0:
        categ = "unknown"
        return selectDocument(doctype,categ, ln = ln)

    categories = []
    for arr in sth:
        waiting = 0
        rejected = 0
        approved = 0
        sth2 = run_sql("select COUNT(*) from sbmAPPROVAL where doctype=%s and categ=%s and status='waiting'", (doctype,arr[1],))
        waiting = sth2[0][0]
        sth2 = run_sql("select COUNT(*) from sbmAPPROVAL where doctype=%s and categ=%s and status='approved'",(doctype,arr[1],))
        approved = sth2[0][0]
        sth2 = run_sql("select COUNT(*) from sbmAPPROVAL where doctype=%s and categ=%s and status='rejected'",(doctype,arr[1],))
        rejected = sth2[0][0]
        categories.append({
                            'waiting' : waiting,
                            'approved' : approved,
                            'rejected' : rejected,
                            'id' : arr[1],
                          })

    t = websubmit_templates.tmpl_publiline_selectcateg(
          ln = ln,
          categories = categories,
          doctype = doctype,
          title = title,
          images = images,
        )
    return t

def selectCplxCateg(doctype, ln = cdslang):
    t=""
    res = run_sql("SELECT ldocname FROM sbmDOCTYPE WHERE sdocname=%s",(doctype,))
    title = res[0][0]
    sth = run_sql("SELECT * FROM sbmCATEGORIES WHERE doctype=%s ORDER BY lname",(doctype,))
    if len(sth) == 0:
        categ = "unknown"
        return selectCplxDocument(doctype,categ, "", ln = ln)

    types = {}
    for apptype in ('RRP', 'RPB', 'RDA'):
        for arr in sth:
            info = {'id' : arr[1],
                    'desc' : arr[2],}
            for status in ('waiting', 'rejected', 'approved', 'cancelled'):
                info[status] = __db_count_doc (doctype, arr[1], status, apptype)
            types.setdefault (apptype, []).append(info)

    t = websubmit_templates.tmpl_publiline_selectcplxcateg(
          ln = ln,
          types = types,
          doctype = doctype,
          title = title,
          images = images,
        )
    return t

def selectDocument(doctype,categ, ln = cdslang):
    t=""
    res = run_sql("select ldocname from sbmDOCTYPE where sdocname=%s", (doctype,))
    title = res[0][0]
    if categ == "":
        categ == "unknown"

    docs = []
    sth = run_sql("select rn,status from sbmAPPROVAL where doctype=%s and categ=%s order by status DESC,rn DESC",(doctype,categ))
    for arr in sth:
        docs.append({
                     'RN' : arr[0],
                     'status' : arr[1],
                    })

    t = websubmit_templates.tmpl_publiline_selectdocument(
          ln = ln,
          doctype = doctype,
          title = title,
          categ = categ,
          images = images,
          docs = docs,
        )
    return t

def selectCplxDocument(doctype,categ,apptype, ln = cdslang):
    t=""
    res = run_sql("select ldocname from sbmDOCTYPE where sdocname=%s", (doctype,))
    title = res[0][0]

    sth = run_sql("select lname from sbmCATEGORIES where doctype=%s and sname=%s order by lname",(doctype,categ,))
    if len(sth) != 0:
        categname = sth[0][0]
    else:
        categname = "Unknown"

    docs = []
    sth = run_sql("select rn,status from sbmCPLXAPPROVAL where doctype=%s and categ=%s and type=%s order by status DESC,rn DESC",(doctype,categ,apptype))
    for arr in sth:
        docs.append({
                     'RN' : arr[0],
                     'status' : arr[1],
                    })

    t = websubmit_templates.tmpl_publiline_selectcplxdocument(
          ln = ln,
          doctype = doctype,
          title = title,
          categ = categ,
          categname = categname,
          images = images,
          docs = docs,
          apptype = apptype,
        )
    return t

def displayDocument(req, doctype,categ,RN,send, ln = cdslang):

    # load the right message language
    _ = gettext_set_language(ln)

    t=""
    res = run_sql("select ldocname from sbmDOCTYPE where sdocname=%s", (doctype,))
    docname = res[0][0]
    if categ == "":
        categ = "unknown"
    sth = run_sql("select rn,status,dFirstReq,dLastReq,dAction,access from sbmAPPROVAL where rn=%s",(RN,))
    if len(sth) > 0:
        arr = sth[0]
        rn = arr[0]
        status = arr[1]
        dFirstReq = arr[2]
        dLastReq = arr[3]
        dAction = arr[4]
        access = arr[5]
    else:
        return _("Approval has never been requested for this document.") + "<BR>&nbsp;"

    try:
        (authors,title,sysno,newrn) = getInfo(doctype,categ,RN)
    except TypeError:
        return _("Unable to display document.")

    confirm_send = 0
    if send == _("Send Again"):
        if authors == "unknown" or title == "unknown":
            SendWarning(doctype,categ,RN,title,authors,access, ln = ln)
        else:
            # @todo - send in different languages
            SendEnglish(doctype,categ,RN,title,authors,access,sysno)
            run_sql("update sbmAPPROVAL set dLastReq=NOW() where rn=%s",(RN,))
            confirm_send = 1

    if status == "waiting":
        (auth_code, auth_message) = acc_authorize_action(req, "referee",verbose=0,doctype=doctype, categ=categ)
    else:
        (auth_code, auth_message) = (None, None)

    t = websubmit_templates.tmpl_publiline_displaydoc(
          ln = ln,
          docname = docname,
          doctype = doctype,
          categ = categ,
          rn = rn,
          status = status,
          dFirstReq = dFirstReq,
          dLastReq = dLastReq,
          dAction = dAction,
          access = access,
          images = images,
          accessurl = accessurl,
          confirm_send = confirm_send,
          auth_code = auth_code,
          auth_message = auth_message,
          authors = authors,
          title = title,
          sysno = sysno,
          newrn = newrn,
        )
    return t

def displayCplxDocument(req, doctype,categ,RN,apptype, ln = cdslang):

    # load the right message language
    _ = gettext_set_language(ln)

    t=""
    uid = getUid(req)
    res = run_sql("select ldocname from sbmDOCTYPE where sdocname=%s", (doctype,))
    docname = res[0][0]
    if categ == "":
        categ = "unknown"

    key = (RN, apptype)
    infos = __db_get_infos (key)
    if len(infos) > 0:
        (status, id_group, id_bskBASKET, id_EdBoardGroup,
         dFirstReq,dLastReq,dEdBoardSel, dRefereeSel, dRefereeRecom, dEdBoardRecom, dPubComRecom, dProjectLeaderAction) = infos[0]

        dates = {'dFirstReq' : dFirstReq,
                 'dLastReq' : dLastReq,
                 'dEdBoardSel' : dEdBoardSel,
                 'dRefereeSel' : dRefereeSel,
                 'dRefereeRecom' : dRefereeRecom,
                 'dEdBoardRecom' : dEdBoardRecom,
                 'dPubComRecom' : dPubComRecom,
                 'dProjectLeaderAction' : dProjectLeaderAction,
                }
    else:
        return _("Approval has never been requested for this document.") + "<BR>&nbsp;"

    try:
        (authors,title,sysno,newrn) = getInAlice(doctype,categ,RN)
    except TypeError:
        return _("Unable to display document.")

    if status == "waiting":
        isPubCom = __is_PubCom (req, doctype)
        isEdBoard = __is_EdBoard (uid, id_EdBoardGroup)
        isReferee = __is_Referee (uid, id_bskBASKET)
        isProjectLeader = __is_ProjectLeader (req, doctype, categ)
        isAuthor = __is_Author (uid, sysno)
    else:
        isPubCom = None
        isEdBoard = None
        isReferee = None
        isProjectLeader = None
        isAuthor = None

    t += websubmit_templates.tmpl_publiline_displaycplxdoc(
          ln = ln,
          docname = docname,
          doctype = doctype,
          categ = categ,
          rn = RN,
          apptype = apptype,
          status = status,
          dates = dates,
          images = images,
          accessurl = accessurl,
          isPubCom = isPubCom,
          isEdBoard = isEdBoard,
          isReferee = isReferee,
          isProjectLeader = isProjectLeader,
          isAuthor = isAuthor,
          authors = authors,
          title = title,
          sysno = sysno,
          newrn = newrn,
        )

    if id_bskBASKET > 0:
        rights = basketdb.get_max_user_rights_on_basket(uid, id_bskBASKET)
        if not(__check_basket_sufficient_rights(rights, CFG_WEBBASKET_SHARE_LEVELS['READITM'])):
            return t

        comments = basketdb.get_comments(id_bskBASKET, sysno)

        if dProjectLeaderAction != None:
            user_can_add_comment = 0
        else:
            user_can_add_comment = __check_basket_sufficient_rights(rights, CFG_WEBBASKET_SHARE_LEVELS['ADDCMT'])

        t += websubmit_templates.tmpl_publiline_displaycplxdocitem(
                                                  doctype, categ, RN, apptype, "AddComment",
                                                  comments,
                                                  (__check_basket_sufficient_rights(rights, CFG_WEBBASKET_SHARE_LEVELS['READCMT']),
                                                   user_can_add_comment,
                                                   __check_basket_sufficient_rights(rights, CFG_WEBBASKET_SHARE_LEVELS['DELCMT'])),
                                                  selected_category=CFG_WEBBASKET_CATEGORIES['GROUP'], selected_topic=0, selected_group_id=id_group,
                                                  ln=ln)

    return t

def __check_basket_sufficient_rights(rights_user_has, rights_needed):
    """Private function, check if the rights are sufficient."""
    try:
        out = CFG_WEBBASKET_SHARE_LEVELS_ORDERED.index(rights_user_has) >= \
              CFG_WEBBASKET_SHARE_LEVELS_ORDERED.index(rights_needed)
    except ValueError:
        out = 0
    return out

def __is_PubCom (req,doctype):
    (isPubCom, auth_message) = acc_authorize_action(req, "pubcomchair",verbose=0,doctype=doctype)
    return isPubCom

def __is_EdBoard (uid, id_EdBoardGroup):
    isEdBoard = None
    if id_EdBoardGroup > 0:
        edBoard = run_sql("""SELECT u.id
                             FROM user u LEFT JOIN user_usergroup ug ON u.id = ug.id_user
                             WHERE ug.id_usergroup = '%s' and user_status != 'A' AND user_status != 'P'""" % (id_EdBoardGroup, ))
        for uid_scan in edBoard:
            if uid == uid_scan[0]:
                isEdBoard = 0
                break
    return isEdBoard

def __is_Referee (uid, id_bskBASKET):
    isReferee = None
    if id_bskBASKET > 0:
        if basketdb.check_user_owns_baskets (uid, id_bskBASKET) == 1:
            isReferee = 0
    return isReferee

def __is_ProjectLeader (req, doctype, categ):
    (isProjectLeader, auth_message) = acc_authorize_action(req, "projectleader",verbose=0,doctype=doctype,categ=categ)
    return isProjectLeader

def __is_Author (uid, sysno):
    email = Get_Field("8560_f",sysno)
    email = re.sub("[\n\r ]+","",email)
    uid_email = re.sub("[\n\r ]+","", acc_get_user_email(uid))
    isAuthor = None
    if (re.search(uid_email,email,re.IGNORECASE) != None) and (uid_email != ""):
        isAuthor = 0
    return isAuthor

def __db_count_doc (doctype, categ, status, apptype):
    return run_sql("SELECT COUNT(*) FROM sbmCPLXAPPROVAL WHERE doctype=%s AND categ=%s AND status=%s AND type=%s",(doctype,categ,status,apptype,))[0][0]

def __db_get_infos (key):
    return run_sql("SELECT status,id_group,id_bskBASKET,id_EdBoardGroup,dFirstReq,dLastReq,dEdBoardSel,dRefereeSel,dRefereeRecom,dEdBoardRecom,dPubComRecom,dProjectLeaderAction FROM sbmCPLXAPPROVAL WHERE rn=%s and type=%s", key)

def __db_set_EdBoardSel_time (key):
    run_sql("UPDATE sbmCPLXAPPROVAL SET dEdBoardSel=NOW() WHERE  rn=%s and type=%s", key)

def __db_check_EdBoardGroup ((RN,apptype), id_EdBoardGroup, uid, group_descr):
    res = get_group_infos (id_EdBoardGroup)
    if len(res) == 0:
        id_EdBoardGroup = insert_new_group (uid, RN, group_descr % RN, "VM")
        run_sql("UPDATE sbmCPLXAPPROVAL SET id_EdBoardGroup=%s WHERE  rn=%s and type=%s", (id_EdBoardGroup,RN,apptype,))

    return id_EdBoardGroup

def __db_set_basket ((RN,apptype), id_bsk):
    run_sql("UPDATE sbmCPLXAPPROVAL SET id_bskBASKET=%s, dRefereeSel=NOW() WHERE  rn=%s and type=%s", (id_bsk,RN,apptype,))

def __db_set_RefereeRecom_time (key):
    run_sql("UPDATE sbmCPLXAPPROVAL SET dRefereeRecom=NOW() WHERE  rn=%s and type=%s", key)

def __db_set_EdBoardRecom_time (key):
    run_sql("UPDATE sbmCPLXAPPROVAL SET dEdBoardRecom=NOW() WHERE  rn=%s and type=%s", key)

def __db_set_PubComRecom_time (key):
    run_sql("UPDATE sbmCPLXAPPROVAL SET dPubComRecom=NOW() WHERE  rn=%s and type=%s", key)

def __db_set_status ((RN,apptype), status):
    run_sql("UPDATE sbmCPLXAPPROVAL SET status=%s, dProjectLeaderAction=NOW() WHERE  rn=%s and type=%s", (status,RN,apptype,))

def doCplxAction(req, doctype, categ, RN, apptype, action, email_user_pattern, id_user, id_user_remove, validate, id_user_val, msg_subject, msg_body, ln=cdslang):
    """
    Perform complex action. Note: all argume,ts are supposed to be washed already.
    Return HTML body for the paget.
    In case of errors, deletes hard drive. ;-)
    """
    # load the right message language
    _ = gettext_set_language(ln)

    TEXT_RRP_RefereeSel_BASKET_DESCR = "Requests for refereeing process"
    TEXT_RRP_RefereeSel_MSG_REFEREE_SUBJECT = "Referee selection"
    TEXT_RRP_RefereeSel_MSG_REFEREE_BODY = "You have been named as a referee for this document :"
    TEXT_RRP_RefereeSel_MSG_GROUP_SUBJECT = "Please, review this publication"
    TEXT_RRP_RefereeSel_MSG_GROUP_BODY = "Please, review the following publication"
    TEXT_RRP_RefereeRecom_MSG_PUBCOM_SUBJECT = "Final recommendation from the referee"
    TEXT_RRP_PubComRecom_MSG_PRJLEADER_SUBJECT = "Final recommendation from the publication board"
    TEXT_RRP_ProjectLeaderDecision_MSG_SUBJECT = "Final decision from the project leader"

    TEXT_RPB_EdBoardSel_MSG_EDBOARD_SUBJECT = "You have been selected in a editorial board"
    TEXT_RPB_EdBoardSel_MSG_EDBOARD_BODY = "You have been selected as a member of the editorial board of this document :"
    TEXT_RPB_EdBoardSel_EDBOARD_GROUP_DESCR = "Editorial board for %s"
    TEXT_RPB_RefereeSel_BASKET_DESCR = "Requests for publication"
    TEXT_RPB_RefereeSel_MSG_REFEREE_SUBJECT = "Referee selection"
    TEXT_RPB_RefereeSel_MSG_REFEREE_BODY = "You have been named as a referee for this document :"
    TEXT_RPB_RefereeSel_MSG_GROUP_SUBJECT = "Please, review this publication"
    TEXT_RPB_RefereeSel_MSG_GROUP_BODY = "Please, review the following publication"
    TEXT_RPB_RefereeRecom_MSG_EDBOARD_SUBJECT = "Final recommendation from the referee"
    TEXT_RPB_EdBoardRecom_MSG_PUBCOM_SUBJECT = "Final recommendation from the editorial board"
    TEXT_RPB_PubComRecom_MSG_PRJLEADER_SUBJECT = "Final recommendation from the publication board"
    TEXT_RPB_ProjectLeaderDecision_MSG_SUBJECT = "Final decision from the project leader"

    t=""
    uid = getUid(req)

    if categ == "":
        categ = "unknown"

    key = (RN, apptype)

    infos = __db_get_infos (key)
    if len(infos) > 0:
        (status, id_group, id_bskBASKET, id_EdBoardGroup, dummy, dummy,
         dEdBoardSel, dRefereeSel, dRefereeRecom, dEdBoardRecom, dPubComRecom, dProjectLeaderAction) = infos[0]
    else:
        return _("Approval has never been requested for this document.") + "<br />&nbsp;"

    try:
        (authors,title,sysno,newrn) = getInAlice(doctype,categ,RN)
    except TypeError:
        return _("Unable to display document.")

    if (action == "EdBoardSel") and (apptype == "RPB"):
        if __is_PubCom (req, doctype) != 0:
            return _("Action unauthorized for this document.") + "<br />&nbsp;"

        if status == "cancelled":
            return _("Action unavailable for this document.") + "<br />&nbsp;"

        if validate == "go":
            if dEdBoardSel == None:
                __db_set_EdBoardSel_time (key)
                perform_request_send (uid, "", RN, TEXT_RPB_EdBoardSel_MSG_EDBOARD_SUBJECT, TEXT_RPB_EdBoardSel_MSG_EDBOARD_BODY)
            return displayCplxDocument(req, doctype,categ,RN,apptype, ln)

        id_EdBoardGroup = __db_check_EdBoardGroup (key, id_EdBoardGroup, uid, TEXT_RPB_EdBoardSel_EDBOARD_GROUP_DESCR)

        subtitle1 = _('Adding users to the editorial board')

        # remove letters not allowed in an email
        email_user_pattern = cleanstring_email(email_user_pattern)

        stopon1 = ""
        stopon2 = ""
        stopon3 = ""
        users = []
        extrausers = []
        # pattern is entered
        if email_user_pattern:
            # users with matching email-address
            users1 = run_sql("""SELECT id, email FROM user WHERE email RLIKE %s ORDER BY email """, (email_user_pattern, ))
            # users that are connected
            users2 = run_sql("""SELECT DISTINCT u.id, u.email
            FROM user u LEFT JOIN user_usergroup ug ON u.id = ug.id_user
            WHERE ug.id_usergroup = %s AND u.email RLIKE %s
            ORDER BY u.email """, (id_EdBoardGroup, email_user_pattern))

            # no users that match the pattern
            if not (users1 or users2):
                stopon1 = '<p>%s</p>' % _("no qualified users, try new search.")
            elif len(users1) > MAXSELECTUSERS:
                stopon1 = '<p><strong>%s %s</strong>, %s (%s %s)</p>' % (len(users1), _("hits"), _("too many qualified users, specify more narrow search."), _("limit"), MAXSELECTUSERS)

            # show matching users
            else:
                users = []
                extrausers = []
                for (user_id, email) in users1:
                    if (user_id, email) not in users2: users.append([user_id,email,''])
                for (user_id, email) in users2:
                    extrausers.append([-user_id, email,''])

                try: id_user = int(id_user)
                except ValueError: pass
                # user selected already connected to role
                email_out = acc_get_user_email(id_user)
                if id_user < 0:
                    stopon2 = '<p>%s</p>' % _("users in brackets are already attached to the role, try another one...")
                # a user is selected
                elif email_out:
                    result = insert_new_member(id_user, id_EdBoardGroup, "M")
                    stopon2  = '<p>confirm: user <strong>%s</strong> added to the editorial board.</p>' % (email_out, )

        subtitle2 = _('Removing users from the editorial board')

        usersremove = run_sql("""SELECT DISTINCT u.id, u.email
                            FROM user u LEFT JOIN user_usergroup ug ON u.id = ug.id_user
                            WHERE ug.id_usergroup = %s and user_status != 'A' AND user_status != 'P'
                            ORDER BY u.email """, (id_EdBoardGroup, ))

        try: id_user_remove = int(id_user_remove)
        except ValueError: pass
        # user selected already connected to role
        email_out = acc_get_user_email(id_user_remove)
        # a user is selected
        if email_out:
            result = delete_member(id_EdBoardGroup, id_user_remove)
            stopon3  = '<p>confirm: user <strong>%s</strong> removed from the editorial board.</p>' % (email_out, )

        t = websubmit_templates.tmpl_publiline_displaydocplxaction (
              ln = ln,
              doctype = doctype,
              categ = categ,
              rn = RN,
              apptype = apptype,
              action = action,
              status = status,
              images = images,
              authors = authors,
              title = title,
              sysno = sysno,
              subtitle1 = subtitle1,
              email_user_pattern = email_user_pattern,
              stopon1 = stopon1,
              users = users,
              extrausers = extrausers,
              stopon2 = stopon2,
              subtitle2 = subtitle2,
              usersremove = usersremove,
              stopon3 = stopon3,
              validate_btn = _("Validate the editorial board selection"),
            )
        return t

    elif (action == "RefereeSel") and ((apptype == "RRP") or (apptype == "RPB")):
        if apptype == "RRP":
            to_check = __is_PubCom (req, doctype)
            TEXT_RefereeSel_BASKET_DESCR = TEXT_RRP_RefereeSel_BASKET_DESCR
            TEXT_RefereeSel_MSG_REFEREE_SUBJECT = TEXT_RRP_RefereeSel_MSG_REFEREE_SUBJECT
            TEXT_RefereeSel_MSG_REFEREE_BODY = TEXT_RRP_RefereeSel_MSG_REFEREE_BODY
            TEXT_RefereeSel_MSG_GROUP_SUBJECT = TEXT_RRP_RefereeSel_MSG_GROUP_SUBJECT
            TEXT_RefereeSel_MSG_GROUP_BODY = TEXT_RRP_RefereeSel_MSG_GROUP_BODY
        elif apptype == "RPB":
            to_check = __is_EdBoard (uid, id_EdBoardGroup)
            TEXT_RefereeSel_BASKET_DESCR = TEXT_RRP_RefereeSel_BASKET_DESCR
            TEXT_RefereeSel_MSG_REFEREE_SUBJECT = TEXT_RRP_RefereeSel_MSG_REFEREE_SUBJECT
            TEXT_RefereeSel_MSG_REFEREE_BODY = TEXT_RRP_RefereeSel_MSG_REFEREE_BODY
            TEXT_RefereeSel_MSG_GROUP_SUBJECT = TEXT_RRP_RefereeSel_MSG_GROUP_SUBJECT
            TEXT_RefereeSel_MSG_GROUP_BODY = TEXT_RRP_RefereeSel_MSG_GROUP_BODY
        else:
            to_check = None

        if to_check != 0:
            return _("Action unauthorized for this document.") + "<br />&nbsp;"

        if status == "cancelled":
            return _("Action unavailable for this document.") + "<br />&nbsp;"

        if validate == "go":
            if dRefereeSel == None:
                id_bsk = basketdb.create_basket (int(id_user_val), RN, TEXT_RefereeSel_BASKET_DESCR)
                basketdb.share_basket_with_group (id_bsk, id_group, CFG_WEBBASKET_SHARE_LEVELS['ADDCMT'])
                basketdb.add_to_basket (int(id_user_val), (sysno, ), (id_bsk, ))

                __db_set_basket (key, id_bsk)

                referee_name = run_sql("""SELECT nickname FROM user WHERE id = %s """, (id_user_val, ))[0][0]
                perform_request_send (uid, referee_name, "", TEXT_RefereeSel_MSG_REFEREE_SUBJECT, TEXT_RefereeSel_MSG_REFEREE_BODY)

                group_name = run_sql("""SELECT name FROM usergroup WHERE id = %s""", (id_group, ))[0][0]
                perform_request_send (int(id_user_val), "", group_name, TEXT_RefereeSel_MSG_GROUP_SUBJECT, TEXT_RefereeSel_MSG_GROUP_BODY)
            return displayCplxDocument(req, doctype,categ,RN,apptype, ln)

        subtitle1 = _('Referee selection')

        # remove letters not allowed in an email
        email_user_pattern = cleanstring_email(email_user_pattern)

        stopon1 = ""
        stopon2 = ""
        users = []
        extrausers = []
        # pattern is entered
        if email_user_pattern:
            # users with matching email-address
            users1 = run_sql("""SELECT id, email FROM user WHERE email RLIKE %s ORDER BY email """, (email_user_pattern, ))

            # no users that match the pattern
            if not users1:
                stopon1 = '<p>%s</p>' % _("no qualified users, try new search.")
            elif len(users1) > MAXSELECTUSERS:
                stopon1 = '<p><strong>%s %s</strong>, %s (%s %s)</p>' % (len(users1), _("hits"), _("too many qualified users, specify more narrow search."), _("limit"), MAXSELECTUSERS)

            # show matching users
            else:
                users = []
                for (user_id, email) in users1:
                    users.append([user_id,email,''])

                try: id_user = int(id_user)
                except ValueError: pass
                # user selected already connected to role
                email_out = acc_get_user_email(id_user)
                # a user is selected
                if email_out:
                    stopon2  = """<p>user <strong>%s</strong> will be the referee ?
                                    <input type="hidden" name="id_user_val" value="%s" />
                                    <input type="hidden" name="validate" value="go" />
                                    <input class="adminbutton" type="submit" value="Validate the referee selection" />
                                  </p>""" % (email_out, id_user)

        t = websubmit_templates.tmpl_publiline_displaydocplxaction (
              ln = ln,
              doctype = doctype,
              categ = categ,
              rn = RN,
              apptype = apptype,
              action = action,
              status = status,
              images = images,
              authors = authors,
              title = title,
              sysno = sysno,
              subtitle1 = subtitle1,
              email_user_pattern = email_user_pattern,
              stopon1 = stopon1,
              users = users,
              extrausers = [],
              stopon2 = stopon2,
              subtitle2 = "",
              usersremove = [],
              stopon3 = "",
              validate_btn = "",
            )
        return t

    elif (action == "AddAuthorList") and (apptype == "RPB"):
        return ""

    elif (action == "AddComment") and ((apptype == "RRP") or (apptype == "RPB")):
        t = ""

        if validate == "go":
            (errors, infos) = perform_request_save_comment (uid, id_bskBASKET, sysno, msg_subject, msg_body, ln)
            t += "%(infos)s<br /><br />" % {'infos' : infos[0]}

        t += """
  <form action="publiline.py">
    <input type="hidden" name="flow" value="cplx" />
    <input type="hidden" name="doctype" value="%(doctype)s" />
    <input type="hidden" name="categ" value="%(categ)s" />
    <input type="hidden" name="RN" value="%(rn)s" />
    <input type="hidden" name="apptype" value="%(apptype)s" />
    <input type="submit" class="formbutton" value="%(button_label)s" />
  </form>""" % {'doctype' : doctype,
                'categ' : categ,
                'rn' : RN,
                'apptype' : apptype,
                'button_label' : _("Come back to the document"),
               }

        return t

    elif (action == "RefereeRecom") and ((apptype == "RRP") or (apptype == "RPB")):
        if __is_Referee (uid, id_bskBASKET) != 0:
            return _("Action unauthorized for this document.") + "<br />&nbsp;"

        if status == "cancelled":
            return _("Action unavailable for this document.") + "<br />&nbsp;"

        if apptype == "RRP":
            # Build publication committee chair's email address
            user_addr = ""
            # Try to retrieve the publication committee chair's email from the role database
            for user in acc_get_role_users(acc_get_role_id("pubcomchair_%s_%s" % (doctype,categ))):
                user_addr += run_sql("""SELECT nickname FROM user WHERE id = %s """, (user[0], ))[0][0] + ","
            # And if there are general publication committee chair's
            for user in acc_get_role_users(acc_get_role_id("pubcomchair_%s_*" % doctype)):
                user_addr += run_sql("""SELECT nickname FROM user WHERE id = %s """, (user[0], ))[0][0] + ","
            user_addr = re.sub(",$","",user_addr)
            group_addr = ""
            TEXT_RefereeRecom_MSG_SUBJECT = TEXT_RRP_RefereeRecom_MSG_PUBCOM_SUBJECT
        elif apptype == "RPB":
            user_addr = ""
            group_addr = RN
            TEXT_RefereeRecom_MSG_SUBJECT = TEXT_RPB_RefereeRecom_MSG_EDBOARD_SUBJECT
        else:
            user_addr = ""
            group_addr = ""
            TEXT_RefereeRecom_MSG_SUBJECT = ""

        if validate == "go":
            if dRefereeRecom == None:
                perform_request_send (uid, user_addr, group_addr, msg_subject, msg_body)
                __db_set_RefereeRecom_time (key)
            return displayCplxDocument(req, doctype,categ,RN,apptype, ln)

        t = websubmit_templates.tmpl_publiline_displaycplxrecom (
              ln = ln,
              doctype = doctype,
              categ = categ,
              rn = RN,
              apptype = apptype,
              action = action,
              status = status,
              images = images,
              authors = authors,
              title = title,
              sysno = sysno,
              msg_to = user_addr,
              msg_to_group = group_addr,
              msg_subject = TEXT_RefereeRecom_MSG_SUBJECT,
            )

        return t

    elif (action == "EdBoardRecom") and (apptype == "RPB"):
        if __is_EdBoard (uid, id_EdBoardGroup) != 0:
            return _("Action unauthorized for this document.") + "<br />&nbsp;"

        if status == "cancelled":
            return _("Action unavailable for this document.") + "<br />&nbsp;"

        # Build publication committee chair's email address
        user_addr = ""
        # Try to retrieve the publication committee chair's email from the role database
        for user in acc_get_role_users(acc_get_role_id("pubcomchair_%s_%s" % (doctype,categ))):
            user_addr += run_sql("""SELECT nickname FROM user WHERE id = %s """, (user[0], ))[0][0] + ","
        # And if there are general publication committee chair's
        for user in acc_get_role_users(acc_get_role_id("pubcomchair_%s_*" % doctype)):
            user_addr += run_sql("""SELECT nickname FROM user WHERE id = %s """, (user[0], ))[0][0] + ","
        user_addr = re.sub(",$","",user_addr)

        if validate == "go":
            if dEdBoardRecom == None:
                perform_request_send (uid, user_addr, "", msg_subject, msg_body)
                __db_set_EdBoardRecom_time (key)
            return displayCplxDocument(req, doctype,categ,RN,apptype, ln)

        t = websubmit_templates.tmpl_publiline_displaycplxrecom (
              ln = ln,
              doctype = doctype,
              categ = categ,
              rn = RN,
              apptype = apptype,
              action = action,
              status = status,
              images = images,
              authors = authors,
              title = title,
              sysno = sysno,
              msg_to = user_addr,
              msg_to_group = "",
              msg_subject = TEXT_RPB_EdBoardRecom_MSG_PUBCOM_SUBJECT,
            )

        return t

    elif (action == "PubComRecom") and ((apptype == "RRP") or (apptype == "RPB")):
        if __is_PubCom (req, doctype) != 0:
            return _("Action unauthorized for this document.") + "<br />&nbsp;"

        if status == "cancelled":
            return _("Action unavailable for this document.") + "<br />&nbsp;"

        # Build project leader's email address
        user_addr = ""
        # Try to retrieve the project leader's email from the role database
        for user in acc_get_role_users(acc_get_role_id("projectleader_%s_%s" % (doctype,categ))):
            user_addr += run_sql("""SELECT nickname FROM user WHERE id = %s """, (user[0], ))[0][0] + ","
        # And if there are general project leader's
        for user in acc_get_role_users(acc_get_role_id("projectleader_%s_*" % doctype)):
            user_addr += run_sql("""SELECT nickname FROM user WHERE id = %s """, (user[0], ))[0][0] + ","
        user_addr = re.sub(",$","",user_addr)

        if apptype == "RRP":
            TEXT_PubComRecom_MSG_SUBJECT = TEXT_RRP_PubComRecom_MSG_PRJLEADER_SUBJECT
        elif apptype == "RPB":
            group_addr = RN
            TEXT_PubComRecom_MSG_SUBJECT = TEXT_RPB_PubComRecom_MSG_PRJLEADER_SUBJECT
        else:
            TEXT_PubComRecom_MSG_SUBJECT = ""

        if validate == "go":
            if dPubComRecom == None:
                perform_request_send (uid, user_addr, "", msg_subject, msg_body)
                __db_set_PubComRecom_time (key)
            return displayCplxDocument(req, doctype,categ,RN,apptype, ln)

        t = websubmit_templates.tmpl_publiline_displaycplxrecom (
              ln = ln,
              doctype = doctype,
              categ = categ,
              rn = RN,
              apptype = apptype,
              action = action,
              status = status,
              images = images,
              authors = authors,
              title = title,
              sysno = sysno,
              msg_to = user_addr,
              msg_to_group = "",
              msg_subject = TEXT_PubComRecom_MSG_SUBJECT,
            )

        return t

    elif (action == "ProjectLeaderDecision") and ((apptype == "RRP") or (apptype == "RPB")):
        if __is_ProjectLeader (req, doctype, categ) != 0:
            return _("Action unauthorized for this document.") + "<br />&nbsp;"

        if status == "cancelled":
            return _("Action unavailable for this document.") + "<br />&nbsp;"

        t += """
  <form action="publiline.py">
    <input type="hidden" name="flow" value="cplx" />
    <input type="hidden" name="doctype" value="%(doctype)s" />
    <input type="hidden" name="categ" value="%(categ)s" />
    <input type="hidden" name="RN" value="%(rn)s" />
    <input type="hidden" name="apptype" value="%(apptype)s" />
    <input type="submit" class="formbutton" value="%(button_label)s" />
  </form>""" % {'doctype' : doctype,
                'categ' : categ,
                'rn' : RN,
                'apptype' : apptype,
                'button_label' : _("Come back to the document"),
               }

        if validate == "approve":
            if dProjectLeaderAction == None:
                (errors, infos) = perform_request_save_comment (uid, id_bskBASKET, sysno, msg_subject, msg_body, ln)
                out = "%(infos)s<br /><br />" % {'infos' : infos[0]}

                __db_set_status (key, 'approved')
            return out + t

        elif validate == "reject":
            if dProjectLeaderAction == None:
                (errors, infos) = perform_request_save_comment (uid, id_bskBASKET, sysno, msg_subject, msg_body, ln)
                out = "%(infos)s<br /><br />" % {'infos' : infos[0]}

                __db_set_status (key, 'rejected')
            return out + t

        validation = """
    <select name="validate">
      <option> %(select)s</option>
      <option value="approve">%(approve)s</option>
      <option value="reject">%(reject)s</option>
    </select>
    <input type="submit" class="formbutton" value="%(button_label)s" />""" % {'select' : _('Select:'),
                                                                              'approve' : _('Approve'),
                                                                              'reject' : _('Reject'),
                                                                              'button_label' : _('Take a decision'),
                                                                             }

        if apptype == "RRP":
            TEXT_ProjectLeaderDecision_MSG_SUBJECT = TEXT_RRP_ProjectLeaderDecision_MSG_SUBJECT
        elif apptype == "RPB":
            TEXT_ProjectLeaderDecision_MSG_SUBJECT = TEXT_RPB_ProjectLeaderDecision_MSG_SUBJECT
        else:
            TEXT_ProjectLeaderDecision_MSG_SUBJECT = ""

        t = websubmit_templates.tmpl_publiline_displaywritecomment(doctype, categ, RN, apptype, action, _("Take a decision"), TEXT_ProjectLeaderDecision_MSG_SUBJECT, validation, ln)

        return t

    elif (action == "ProjectLeaderDecision") and (apptype == "RDA"):
        if __is_ProjectLeader (req, doctype, categ) != 0:
            return _("Action unauthorized for this document.") + "<br />&nbsp;"

        if status == "cancelled":
            return _("Action unavailable for this document.") + "<br />&nbsp;"

        if validate == "approve":
            if dProjectLeaderAction == None:
                __db_set_status (key, 'approved')
            return displayCplxDocument(req, doctype,categ,RN,apptype, ln)

        elif validate == "reject":
            if dProjectLeaderAction == None:
                __db_set_status (key, 'rejected')
            return displayCplxDocument(req, doctype,categ,RN,apptype, ln)

        t = """<p>
                 <form action="publiline.py">
                    <input type="hidden" name="flow" value="cplx" />
                    <input type="hidden" name="doctype" value="%(doctype)s" />
                    <input type="hidden" name="categ" value="%(categ)s" />
                    <input type="hidden" name="RN" value="%(rn)s" />
                    <input type="hidden" name="apptype" value="%(apptype)s" />
                    <input type="hidden" name="action" value="%(action)s" />
                    <input type="hidden" name="validate" value="approve" />
                    <input class="adminbutton" type="submit" value="%(approve)s" />
                  </form>
                  <form action="publiline.py">
                    <input type="hidden" name="flow" value="cplx" />
                    <input type="hidden" name="doctype" value="%(doctype)s" />
                    <input type="hidden" name="categ" value="%(categ)s" />
                    <input type="hidden" name="RN" value="%(rn)s" />
                    <input type="hidden" name="apptype" value="%(apptype)s" />
                    <input type="hidden" name="action" value="%(action)s" />
                    <input type="hidden" name="validate" value="reject" />
                    <input class="adminbutton" type="submit" value="%(reject)s" />
                  </form>
                </p>""" % {
                 'rn' : RN,
                 'categ' : categ,
                 'doctype' : doctype,
                 'apptype' : apptype,
                 'action' : action,
                 'approve' : _('Approve'),
                 'reject' : _('Reject'),
               }

        return t

    elif (action == "AuthorCancel") and ((apptype == "RRP") or (apptype == "RPB") or (apptype == "RDA")):
        if __is_Author (uid, sysno) != 0:
            return _("Action unauthorized for this document.") + "<br />&nbsp;"

        if (status == "cancelled") or (dProjectLeaderAction != None):
            return _("Action unavailable for this document.") + "<br />&nbsp;"

        if validate == "go":
            __db_set_status (key, 'cancelled')
            return displayCplxDocument(req, doctype,categ,RN,apptype, ln)

        t = """<p>
                 <form action="publiline.py">
                    <input type="hidden" name="flow" value="cplx" />
                    <input type="hidden" name="doctype" value="%(doctype)s" />
                    <input type="hidden" name="categ" value="%(categ)s" />
                    <input type="hidden" name="RN" value="%(rn)s" />
                    <input type="hidden" name="apptype" value="%(apptype)s" />
                    <input type="hidden" name="action" value="%(action)s" />
                    <input type="hidden" name="validate" value="go" />
                    <input class="adminbutton" type="submit" value="%(cancel)s" />
                  </form>
                </p>""" % {
                 'rn' : RN,
                 'categ' : categ,
                 'doctype' : doctype,
                 'apptype' : apptype,
                 'action' : action,
                 'cancel' : _('Cancel'),
               }
        return t

    else:
        return _("Wrong action for this document.") + "<BR>&nbsp;"

    return t

# Retrieve info about document
def getInfo(doctype,categ,RN):
    result = getInPending(doctype,categ,RN)
    if not result:
        result = getInAlice(doctype,categ,RN)
    return result

#seek info in pending directory
def getInPending(doctype,categ,RN):
    PENDIR="%s/pending" % storage
    if os.path.exists("%s/%s/%s/AU" % (PENDIR,doctype,RN)):
        fp = open("%s/%s/%s/AU" % (PENDIR,doctype,RN),"r")
        authors=fp.read()
        fp.close()
    else:
        authors = ""
    if os.path.exists("%s/%s/%s/TI" % (PENDIR,doctype,RN)):
        fp = open("%s/%s/%s/TI" % (PENDIR,doctype,RN),"r")
        title=fp.read()
        fp.close()
    else:
        title = ""
    if os.path.exists("%s/%s/%s/SN" % (PENDIR,doctype,RN)):
        fp = open("%s/%s/%s/SN" % (PENDIR,doctype,RN),"r")
        sysno=fp.read()
        fp.close()
    else:
        sysno = ""
    if title == "" and os.path.exists("%s/%s/%s/TIF" % (PENDIR,doctype,RN)):
        fp = open("%s/%s/%s/TIF" % (PENDIR,doctype,RN),"r")
        title=fp.read()
        fp.close()
    if title == "":
        return 0
    else:
        return (authors,title,sysno,"")

#seek info in Alice database
def getInAlice(doctype,categ,RN):
    # initialize sysno variable
    sysno = ""
    searchresults = list(search_pattern(req=None, p=RN, f="reportnumber"))
    if len(searchresults) == 0:
        return 0
    sysno = searchresults[0]
    if sysno != "":
        title = Get_Field('245__a',sysno)
        emailvalue = Get_Field('8560_f',sysno)
        authors = Get_Field('100__a',sysno)
        authors += "\n%s" % Get_Field('700__a',sysno)
        newrn = Get_Field('037__a',sysno)
        return (authors,title,sysno,newrn)
    else:
        return 0

def SendEnglish(doctype,categ,RN,title,authors,access,sysno):
    FROMADDR = '%s Submission Engine <%s>' % (cdsname,supportemail)
    # retrieve useful information from webSubmit configuration
    res = run_sql("select value from sbmPARAMETERS where name='categformatDAM' and doctype=%s", (doctype,))
    categformat = res[0][0]
    categformat = re.sub("<CATEG>","([^-]*)",categformat)
    categs = re.match(categformat,RN)
    if categs is not None:
        categ = categs.group(1)
    else:
        categ = "unknown"
    res = run_sql("select value from sbmPARAMETERS where name='addressesDAM' and doctype=%s",(doctype,))
    if len(res) > 0:
        otheraddresses = res[0][0]
        otheraddresses = otheraddresses.replace("<CATEG>",categ)
    else:
        otheraddresses = ""
    # Build referee's email address
    refereeaddress = ""
    # Try to retrieve the referee's email from the referee's database
    for user in acc_get_role_users(acc_getRoleId("referee_%s_%s" % (doctype,categ))):
        refereeaddress += user[1] + ","
    # And if there are general referees
    for user in acc_get_role_users(acc_getRoleId("referee_%s_*" % doctype)):
        refereeaddress += user[1] + ","
    refereeaddress = re.sub(",$","",refereeaddress)
    # Creation of the mail for the referee
    addresses = ""
    if refereeaddress != "":
        addresses = refereeaddress + ","
    if otheraddresses != "":
        addresses += otheraddresses
    else:
        addresses = re.sub(",$","",addresses)
    if addresses=="":
        SendWarning(doctype,categ,RN,title,authors,access)
        return 0
    if authors == "":
        authors = "-"
    res = run_sql("select value from sbmPARAMETERS where name='directory' and doctype=%s", (doctype,))
    directory = res[0][0]
    message = """
    The document %s has been published as a Communication.
    Your approval is requested for it to become an official Note.

    Title: %s

    Author(s): %s

    To access the document(s), select the file(s) from the location:
    <%s/record/%s/files/>

    To approve/reject the document, you should go to this URL:
    <%s/approve.py?%s>

    ---------------------------------------------
    Best regards.
    The submission team.""" % (RN,title,authors,urlpath,sysno,urlpath,access)
    # send the mail
    send_email(FROMADDR,addresses,"Request for Approval of %s" % RN, message,footer="")
    return ""

def SendWarning(doctype,categ,RN,title,authors,access):
    FROMADDR = '%s Submission Engine <%s>' % (cdsname,supportemail)
    message = "Failed sending approval email request for %s" % RN
    # send the mail
    send_email(FROMADDR,adminemail,"Failed sending approval email request",message)
    return ""

def errorMsg(title,req,c=cdsname,ln=cdslang):
    return page(title="error",
                body = create_error_box(req, title=title,verbose=0, ln=ln),
                description="%s - Internal Error" % c,
                keywords="%s, Internal Error" % c,
                language=ln,
                req=req,
                navmenuid='yourapprovals')

def warningMsg(title,req,c=cdsname,ln=cdslang):
    return page(title="warning",
                body = title,
                description="%s - Internal Error" % c,
                keywords="%s, Internal Error" % c,
                language=ln,
                req=req,
                navmenuid='yourapprovals')

