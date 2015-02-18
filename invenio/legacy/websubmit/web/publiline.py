# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012,
#               2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
publiline_complex.py --  implementes ...

  actors in this process are:

        1. author -- subilmts ...
        2. edi
        3; ref

Il ne faut pas oublier de definir les roles...
"""

__revision__ = "$Id$"

# import interesting modules:
import os
import re

from invenio.base.globals import cfg

from invenio.config import \
     CFG_ACCESS_CONTROL_LEVEL_SITE, \
     CFG_SITE_ADMIN_EMAIL, \
     CFG_SITE_LANG, \
     CFG_SITE_NAME, \
     CFG_SITE_URL, \
     CFG_PYLIBDIR, \
     CFG_WEBSUBMIT_STORAGEDIR, \
     CFG_SITE_SUPPORT_EMAIL, \
     CFG_SITE_SECURE_URL, \
     CFG_SITE_RECORD
from invenio.legacy.dbquery import run_sql
from invenio.modules.access.engine import acc_authorize_action
from invenio.modules.access.control import acc_get_role_users, acc_get_role_id
from invenio.legacy.webpage import page, error_page
from invenio.legacy.webuser import getUid, get_email, page_not_authorized, collect_user_info
from invenio.base.i18n import gettext_set_language, wash_language
#from invenio.legacy.websubmit.config import *
from invenio.legacy.search_engine import search_pattern, check_user_can_view_record
from invenio.legacy.bibrecord import get_fieldvalues
from invenio.legacy.websubmit.functions.Retrieve_Data import Get_Field
from invenio.ext.email import send_email
from invenio.utils.url import wash_url_argument
from invenio.legacy.websession.dblayer import get_group_infos, insert_new_group, insert_new_member, delete_member
from invenio.modules.access.admin_lib import cleanstring_email
from invenio.modules.access.local_config import MAXSELECTUSERS
from invenio.modules.access.control import acc_get_user_email
from invenio.modules.access.engine import acc_get_authorized_emails
from invenio.legacy.webmessage.api import perform_request_send
import invenio.legacy.webbasket.db_layer as basketdb
from invenio.ext.logging import register_exception
from invenio.legacy.bibrecord import create_records, record_get_field_value, record_get_field_values

from sqlalchemy.exc import SQLAlchemyError as Error, OperationalError

execfile("%s/invenio/websubmit_functions/Retrieve_Data.py" % CFG_PYLIBDIR)

import invenio.legacy.template
websubmit_templates = invenio.legacy.template.load('websubmit')

CFG_WEBSUBMIT_PENDING_DIR = "%s/pending" % CFG_WEBSUBMIT_STORAGEDIR
CFG_WEBSUBMIT_DUMMY_MARC_XML_REC = "dummy_marcxml_rec"
CFG_WEBSUBMIT_MARC_XML_REC = "recmysql"


def perform_request_save_comment(*args, **kwargs):
    """
    FIXME: this function is a dummy workaround for the obsoleted
    function calls below.  Should get deleted at the same time as
    them.
    """
    return

def index(req, c=CFG_SITE_NAME, ln=CFG_SITE_LANG, doctype="", categ="", RN="", send="", flow="", apptype="", action="", email_user_pattern="", id_user="", id_user_remove="", validate="", id_user_val="", msg_subject = "", msg_body="", reply="", commentId=""):

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
    reply = wash_url_argument(reply, 'str')
    commentId = wash_url_argument(commentId, 'str')


    # load the right message language
    _ = gettext_set_language(ln)

    t = ""
    # get user ID:
    try:
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../publiline.py/index",
                                       navmenuid='yourapprovals')
        uid_email = get_email(uid)
    except Error as e:
        return error_page(str(e), req, ln=ln)

    if flow == "cplx":
        if doctype == "":
            t = selectCplxDoctype(ln)
        elif (categ == "") or (apptype == ""):
            t = selectCplxCateg(doctype, ln)
        elif RN == "":
            t = selectCplxDocument(doctype, categ, apptype, ln)
        elif action == "":
            t = __displayCplxDocument(req, doctype, categ, RN, apptype, reply, commentId, ln)
        else:
            t = __doCplxAction(req, doctype, categ, RN, apptype, action, email_user_pattern, id_user, id_user_remove, validate, id_user_val, msg_subject, msg_body, reply, commentId, ln)
        return page(title=_("Document Approval Workflow"),
                    navtrail= """<a class="navtrail" href="%(sitesecureurl)s/youraccount/display">%(account)s</a>""" % {
                                 'sitesecureurl': CFG_SITE_SECURE_URL,
                                 'account': _("Your Account"),
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
            t = __displayDocument(req, doctype, categ, RN, send, ln)
        return page(title=_("Approval and Refereeing Workflow"),
                    navtrail= """<a class="navtrail" href="%(sitesecureurl)s/youraccount/display">%(account)s</a>""" % {
                                 'sitesecureurl': CFG_SITE_SECURE_URL,
                                 'account': _("Your Account"),
                              },
                    body=t,
                    description="",
                    keywords="",
                    uid=uid,
                    language=ln,
                    req=req,
                    navmenuid='yourapprovals')

def selectDoctype(ln = CFG_SITE_LANG):
    res = run_sql("select DISTINCT doctype from sbmAPPROVAL")
    docs = []
    for row in res:
        res2 = run_sql("select ldocname from sbmDOCTYPE where sdocname=%s", (row[0],))
        docs.append({
                     'doctype': row[0],
                     'docname': res2[0][0],
                    })
    t = websubmit_templates.tmpl_publiline_selectdoctype(
          ln = ln,
          docs = docs,
        )
    return t

def selectCplxDoctype(ln = CFG_SITE_LANG):
    res = run_sql("select DISTINCT doctype from sbmCPLXAPPROVAL")
    docs = []
    for row in res:
        res2 = run_sql("select ldocname from sbmDOCTYPE where sdocname=%s", (row[0],))
        docs.append({
                     'doctype': row[0],
                     'docname': res2[0][0],
                    })
    t = websubmit_templates.tmpl_publiline_selectcplxdoctype(
          ln = ln,
          docs = docs,
        )
    return t

def selectCateg(doctype, ln = CFG_SITE_LANG):
    t = ""
    res = run_sql("select ldocname from sbmDOCTYPE where sdocname=%s",(doctype,))
    title = res[0][0]
    sth = run_sql("select * from sbmCATEGORIES where doctype=%s order by lname",(doctype,))
    if len(sth) == 0:
        categ = "unknown"
        return selectDocument(doctype, categ, ln=ln)

    categories = []
    for arr in sth:
        waiting = 0
        rejected = 0
        approved = 0
        sth2 = run_sql("select COUNT(*) from sbmAPPROVAL where doctype=%s and categ=%s and status='waiting'", (doctype, arr[1],))
        waiting = sth2[0][0]
        sth2 = run_sql("select COUNT(*) from sbmAPPROVAL where doctype=%s and categ=%s and status='approved'", (doctype, arr[1],))
        approved = sth2[0][0]
        sth2 = run_sql("select COUNT(*) from sbmAPPROVAL where doctype=%s and categ=%s and status='rejected'", (doctype, arr[1],))
        rejected = sth2[0][0]
        categories.append({
                            'waiting': waiting,
                            'approved': approved,
                            'rejected': rejected,
                            'id': arr[1],
                          })

    t = websubmit_templates.tmpl_publiline_selectcateg(
          ln=ln,
          categories=categories,
          doctype=doctype,
          title=title,
        )
    return t

def selectCplxCateg(doctype, ln=CFG_SITE_LANG):
    t = ""
    res = run_sql("SELECT ldocname FROM sbmDOCTYPE WHERE sdocname=%s", (doctype,))
    title = res[0][0]
    sth = run_sql("SELECT * FROM sbmCATEGORIES WHERE doctype=%s ORDER BY lname", (doctype,))
    if len(sth) == 0:
        categ = "unknown"
        return selectCplxDocument(doctype, categ, "", ln=ln)

    types = {}
    for apptype in ('RRP', 'RPB', 'RDA'):
        for arr in sth:
            info = {'id': arr[1],
                    'desc': arr[2],}
            for status in ('waiting', 'rejected', 'approved', 'cancelled'):
                info[status] = __db_count_doc (doctype, arr[1], status, apptype)
            types.setdefault (apptype, []).append(info)

    t = websubmit_templates.tmpl_publiline_selectcplxcateg(
          ln=ln,
          types=types,
          doctype=doctype,
          title=title,
        )
    return t

def selectDocument(doctype, categ, ln=CFG_SITE_LANG):
    t = ""
    res = run_sql("select ldocname from sbmDOCTYPE where sdocname=%s", (doctype,))
    title = res[0][0]
    if categ == "":
        categ == "unknown"

    docs = []
    sth = run_sql("select rn,status from sbmAPPROVAL where doctype=%s and categ=%s order by status DESC,rn DESC", (doctype, categ))
    for arr in sth:
        docs.append({
                     'RN': arr[0],
                     'status': arr[1],
                    })

    t = websubmit_templates.tmpl_publiline_selectdocument(
          ln=ln,
          doctype=doctype,
          title=title,
          categ=categ,
          docs=docs,
        )
    return t

def selectCplxDocument(doctype, categ, apptype, ln=CFG_SITE_LANG):
    t = ""
    res = run_sql("select ldocname from sbmDOCTYPE where sdocname=%s", (doctype,))
    title = res[0][0]

    sth = run_sql("select lname from sbmCATEGORIES where doctype=%s and sname=%s order by lname",(doctype, categ,))
    if len(sth) != 0:
        categname = sth[0][0]
    else:
        categname = "Unknown"

    docs = []
    sth = run_sql("select rn,status from sbmCPLXAPPROVAL where doctype=%s and categ=%s and type=%s order by status DESC,rn DESC",(doctype, categ, apptype))
    for arr in sth:
        docs.append({
                     'RN': arr[0],
                     'status': arr[1],
                    })

    t = websubmit_templates.tmpl_publiline_selectcplxdocument(
          ln = ln,
          doctype = doctype,
          title = title,
          categ = categ,
          categname = categname,
          docs = docs,
          apptype = apptype,
        )
    return t

def __displayDocument(req, doctype, categ, RN, send, ln = CFG_SITE_LANG):

    # load the right message language
    _ = gettext_set_language(ln)

    t = ""
    res = run_sql("select ldocname from sbmDOCTYPE where sdocname=%s", (doctype,))
    docname = res[0][0]
    if categ == "":
        categ = "unknown"
    sth = run_sql("select rn,status,dFirstReq,dLastReq,dAction,access,note from sbmAPPROVAL where rn=%s",(RN,))
    if len(sth) > 0:
        arr = sth[0]
        rn = arr[0]
        status = arr[1]
        dFirstReq = arr[2]
        dLastReq = arr[3]
        dAction = arr[4]
        access = arr[5]
        note = arr[6]
    else:
        return _("Approval has never been requested for this document.") + "<br />&nbsp;"

    ## Get the details of the pending item:
    item_details = get_pending_item_details(doctype, RN)
    ## get_pending_item_details has returned either None or a dictionary
    ## with the following structure:
    ##   { 'title'            : '-', ## String - the item's title
    ##     'recid'            : '',  ## String - recid
    ##     'report-number'    : '',  ## String - the item's report number
    ##     'authors'          : [],  ## List   - the item's authors
    ##   }

    if item_details is not None:
        authors = ", ".join(item_details['authors'])
        newrn = item_details['report-number']
        title = item_details['title']
        sysno = item_details['recid']
    else:
        # Was not found in the pending directory. Already approved?
        try:
            (authors, title, sysno) = getInfo(RN)
            newrn = RN
            if sysno is None:
                return _("Unable to display document.")
        except:
            return _("Unable to display document.")

    user_info = collect_user_info(req)
    can_view_record_p, msg = check_user_can_view_record(user_info, sysno)
    if can_view_record_p != 0:
        return msg

    confirm_send = 0
    if send == _("Send Again"):
        if authors == "unknown" or title == "unknown":
            SendWarning(doctype, categ, RN, title, authors, access)
        else:
            # @todo - send in different languages
            #SendEnglish(doctype, categ, RN, title, authors, access, sysno)
            send_approval(doctype, categ, RN, title, authors, access, sysno)
            run_sql("update sbmAPPROVAL set dLastReq=NOW() where rn=%s",(RN,))
            confirm_send = 1

    if status == "waiting":
        if categ == "unknown":
            ## FIXME: This was necessary for document types without categories,
            ## such as DEMOBOO:
            categ = "*"
        (auth_code, auth_message) = acc_authorize_action(req, "referee", verbose=0, doctype=doctype, categ=categ)
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
          confirm_send = confirm_send,
          auth_code = auth_code,
          auth_message = auth_message,
          authors = authors,
          title = title,
          sysno = sysno,
          newrn = newrn,
          note = note,
        )
    return t

def __displayCplxDocument(req, doctype, categ, RN, apptype, reply, commentId, ln = CFG_SITE_LANG):
    # load the right message language
    _ = gettext_set_language(ln)

    t = ""
    uid = getUid(req)
    res = run_sql("select ldocname from sbmDOCTYPE where sdocname=%s", (doctype,))
    docname = res[0][0]
    if categ == "":
        categ = "unknown"

    key = (RN, apptype)
    infos = __db_get_infos (key)
    if len(infos) > 0:
        (status, id_group, id_bskBASKET, id_EdBoardGroup,
         dFirstReq, dLastReq, dEdBoardSel, dRefereeSel, dRefereeRecom, dEdBoardRecom, dPubComRecom, dProjectLeaderAction) = infos[0]

        dates = {'dFirstReq': dFirstReq,
                 'dLastReq': dLastReq,
                 'dEdBoardSel': dEdBoardSel,
                 'dRefereeSel': dRefereeSel,
                 'dRefereeRecom': dRefereeRecom,
                 'dEdBoardRecom': dEdBoardRecom,
                 'dPubComRecom': dPubComRecom,
                 'dProjectLeaderAction': dProjectLeaderAction,
                }
    else:
        return _("Approval has never been requested for this document.") + "<br />&nbsp;"

# Removing call to deprecated "getInAlice" function and replacing it with
# a call to the newer "get_brief_doc_details_from_repository" function:
#     try:
#         (authors, title, sysno, newrn) = getInAlice(doctype, categ, RN)
#     except TypeError:
#         return _("Unable to display document.")

    item_details = get_brief_doc_details_from_repository(RN)

    ## get_brief_doc_details_from_repository has returned either None
    ## or a dictionary with the following structure:
    ##   { 'title'            : '-', ## String - the item's title
    ##     'recid'            : '',  ## String - recid
    ##     'report-number'    : '',  ## String - the item's report number
    ##     'authors'          : [],  ## List   - the item's authors
    ##   }
    if item_details is not None:
        ## Details of the item were found in the Invenio repository
        authors = ", ".join(item_details['authors'])
        newrn = item_details['report-number']
        title = item_details['title']
        sysno = item_details['recid']
    else:
        ## Can't find any document details.
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

    user_info = collect_user_info(req)
    can_view_record_p, msg = check_user_can_view_record(user_info, sysno)
    if can_view_record_p != 0:
        return msg

    t += websubmit_templates.tmpl_publiline_displaycplxdoc(
          ln = ln,
          docname = docname,
          doctype = doctype,
          categ = categ,
          rn = RN,
          apptype = apptype,
          status = status,
          dates = dates,
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
        if not(__check_basket_sufficient_rights(rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['READITM'])):
            return t

        # FIXME This error will be fixed with Sam's new version of publiline.
        # pylint: disable=E1101
        comments = basketdb.get_comments(id_bskBASKET, sysno)
        # pylint: enable=E1101

        if dProjectLeaderAction != None:
            user_can_add_comment = 0
        else:
            user_can_add_comment = __check_basket_sufficient_rights(rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['ADDCMT'])

            comment_subject = ""
            comment_body = ""
            if reply == "true":
                #Get the message subject and body from the comment
                for comment in comments:
                    if str(commentId) == str(comment[0]):
                        comment_subject = comment[2]
                        comment_body = comment[3]
                comment_subject = comment_subject.lstrip("Re: ")
                comment_subject = "Re: " + comment_subject
                comment_body = "> " + comment_body.replace("\n", "\n> ")


            t += websubmit_templates.tmpl_publiline_displaycplxdocitem(
                                                  doctype, categ, RN, apptype, "AddComment",
                                                  comments,
                                                  (__check_basket_sufficient_rights(rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['READCMT']),
                                                   user_can_add_comment,
                                                   __check_basket_sufficient_rights(rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['DELCMT'])),
                                                  selected_category=cfg['CFG_WEBBASKET_CATEGORIES']['GROUP'], selected_topic=0, selected_group_id=id_group,
                                                  comment_subject=comment_subject, comment_body=comment_body, ln=ln)

    return t

def __check_basket_sufficient_rights(rights_user_has, rights_needed):
    """Private function, check if the rights are sufficient."""
    try:
        out = cfg['CFG_WEBBASKET_SHARE_LEVELS_ORDERED'].index(rights_user_has) >= \
              cfg['CFG_WEBBASKET_SHARE_LEVELS_ORDERED'].index(rights_needed)
    except ValueError:
        out = 0
    return out

def __is_PubCom (req, doctype):
    (isPubCom, auth_message) = acc_authorize_action(req, "pubcomchair", verbose=0, doctype=doctype)
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
    (isProjectLeader, auth_message) = acc_authorize_action(req, "projectleader", verbose=0, doctype=doctype, categ=categ)
    return isProjectLeader

def __is_Author (uid, sysno):
    email = Get_Field("8560_f", sysno)
    email = re.sub("[\n\r ]+", "", email)
    uid_email = re.sub("[\n\r ]+", "", acc_get_user_email(uid))
    isAuthor = None
    if (re.search(uid_email, email, re.IGNORECASE) != None) and (uid_email != ""):
        isAuthor = 0
    return isAuthor

def __db_count_doc (doctype, categ, status, apptype):
    return run_sql("SELECT COUNT(*) FROM sbmCPLXAPPROVAL WHERE doctype=%s AND categ=%s AND status=%s AND type=%s",(doctype, categ, status, apptype,))[0][0]

def __db_get_infos (key):
    return run_sql("SELECT status,id_group,id_bskBASKET,id_EdBoardGroup,dFirstReq,dLastReq,dEdBoardSel,dRefereeSel,dRefereeRecom,dEdBoardRecom,dPubComRecom,dProjectLeaderAction FROM sbmCPLXAPPROVAL WHERE rn=%s and type=%s", key)

def __db_set_EdBoardSel_time (key):
    run_sql("UPDATE sbmCPLXAPPROVAL SET dEdBoardSel=NOW() WHERE  rn=%s and type=%s", key)

def __db_check_EdBoardGroup ((RN, apptype), id_EdBoardGroup, uid, group_descr):
    res = get_group_infos (id_EdBoardGroup)
    if len(res) == 0:
        id_EdBoardGroup = insert_new_group (uid, RN, group_descr % RN, "VM")
        run_sql("UPDATE sbmCPLXAPPROVAL SET id_EdBoardGroup=%s WHERE  rn=%s and type=%s", (id_EdBoardGroup, RN, apptype,))

    return id_EdBoardGroup

def __db_set_basket ((RN, apptype), id_bsk):
    run_sql("UPDATE sbmCPLXAPPROVAL SET id_bskBASKET=%s, dRefereeSel=NOW() WHERE  rn=%s and type=%s", (id_bsk, RN, apptype,))

def __db_set_RefereeRecom_time (key):
    run_sql("UPDATE sbmCPLXAPPROVAL SET dRefereeRecom=NOW() WHERE  rn=%s and type=%s", key)

def __db_set_EdBoardRecom_time (key):
    run_sql("UPDATE sbmCPLXAPPROVAL SET dEdBoardRecom=NOW() WHERE  rn=%s and type=%s", key)

def __db_set_PubComRecom_time (key):
    run_sql("UPDATE sbmCPLXAPPROVAL SET dPubComRecom=NOW() WHERE  rn=%s and type=%s", key)

def __db_set_status ((RN, apptype), status):
    run_sql("UPDATE sbmCPLXAPPROVAL SET status=%s, dProjectLeaderAction=NOW() WHERE  rn=%s and type=%s", (status, RN, apptype,))

def __doCplxAction(req, doctype, categ, RN, apptype, action, email_user_pattern, id_user, id_user_remove, validate, id_user_val, msg_subject, msg_body, reply, commentId, ln=CFG_SITE_LANG):
    """
    Perform complex action. Note: all argume, ts are supposed to be washed already.
    Return HTML body for the paget.
    In case of errors, deletes hard drive. ;-)
    """
    # load the right message language
    _ = gettext_set_language(ln)

    TEXT_RSN_RefereeSel_BASKET_DESCR = "Requests for refereeing process"
    TEXT_RSN_RefereeSel_MSG_REFEREE_SUBJECT = "Referee selection"
    TEXT_RSN_RefereeSel_MSG_REFEREE_BODY = "You have been named as a referee for this document :"
    TEXT_RSN_RefereeSel_MSG_GROUP_SUBJECT = "Please, review this publication"
    TEXT_RSN_RefereeSel_MSG_GROUP_BODY = "Please, review the following publication"
    TEXT_RSN_RefereeRecom_MSG_PUBCOM_SUBJECT = "Final recommendation from the referee"
    TEXT_RSN_PubComRecom_MSG_PRJLEADER_SUBJECT = "Final recommendation from the publication board : "
    TEXT_RSN_ProjectLeaderDecision_MSG_SUBJECT = "Final decision from the project leader"

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

    t = ""
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


# Removing call to deprecated "getInAlice" function and replacing it with
# a call to the newer "get_brief_doc_details_from_repository" function:
#     try:
#         (authors, title, sysno, newrn) = getInAlice(doctype, categ, RN)
#     except TypeError:
#         return _("Unable to display document.")
    item_details = get_brief_doc_details_from_repository(RN)
    ## get_brief_doc_details_from_repository has returned either None
    ## or a dictionary with the following structure:
    ##   { 'title'            : '-', ## String - the item's title
    ##     'recid'            : '',  ## String - recid
    ##     'report-number'    : '',  ## String - the item's report number
    ##     'authors'          : [],  ## List   - the item's authors
    ##   }
    if item_details is not None:
        ## Details of the item were found in the Invenio repository
        authors = ", ".join(item_details['authors'])
        newrn = item_details['report-number']
        title = item_details['title']
        sysno = item_details['recid']
    else:
        ## Can't find any document details.
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
            return __displayCplxDocument(req, doctype, categ, RN, apptype, reply, commentId, ln)

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
            try:
                users1 = run_sql("""SELECT id, email FROM user WHERE email<>'' AND email RLIKE %s ORDER BY email """, (email_user_pattern, ))
            except OperationalError:
                users1 = ()
            # users that are connected
            try:
                users2 = run_sql("""SELECT DISTINCT u.id, u.email
                FROM user u LEFT JOIN user_usergroup ug ON u.id = ug.id_user
                WHERE u.email<>'' AND ug.id_usergroup = %s AND u.email RLIKE %s
                ORDER BY u.email """, (id_EdBoardGroup, email_user_pattern))
            except OperationalError:
                users2 = ()

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
                    if (user_id, email) not in users2: users.append([user_id, email,''])
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
                            WHERE u.email <> "" AND ug.id_usergroup = %s and user_status != 'A' AND user_status != 'P'
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
            TEXT_RefereeSel_BASKET_DESCR = TEXT_RSN_RefereeSel_BASKET_DESCR
            TEXT_RefereeSel_MSG_REFEREE_SUBJECT = TEXT_RSN_RefereeSel_MSG_REFEREE_SUBJECT
            TEXT_RefereeSel_MSG_REFEREE_BODY = TEXT_RSN_RefereeSel_MSG_REFEREE_BODY + " " + "\"" + item_details['title'] + "\""
            TEXT_RefereeSel_MSG_GROUP_SUBJECT = TEXT_RSN_RefereeSel_MSG_GROUP_SUBJECT
            TEXT_RefereeSel_MSG_GROUP_BODY = TEXT_RSN_RefereeSel_MSG_GROUP_BODY + " " + "\"" + item_details['title'] + "\""
        elif apptype == "RPB":
            to_check = __is_EdBoard (uid, id_EdBoardGroup)
            TEXT_RefereeSel_BASKET_DESCR = TEXT_RSN_RefereeSel_BASKET_DESCR
            TEXT_RefereeSel_MSG_REFEREE_SUBJECT = TEXT_RSN_RefereeSel_MSG_REFEREE_SUBJECT
            TEXT_RefereeSel_MSG_REFEREE_BODY = TEXT_RSN_RefereeSel_MSG_REFEREE_BODY + " " + "\"" + item_details['title'] + "\""
            TEXT_RefereeSel_MSG_GROUP_SUBJECT = TEXT_RSN_RefereeSel_MSG_GROUP_SUBJECT
            TEXT_RefereeSel_MSG_GROUP_BODY = TEXT_RSN_RefereeSel_MSG_GROUP_BODY + " " + "\"" + item_details['title'] + "\""
        else:
            to_check = None

        if to_check != 0:
            return _("Action unauthorized for this document.") + "<br />&nbsp;"

        if status == "cancelled":
            return _("Action unavailable for this document.") + "<br />&nbsp;"

        if validate == "go":
            if dRefereeSel == None:
                id_bsk = basketdb.create_basket (int(id_user_val), RN, TEXT_RefereeSel_BASKET_DESCR)
                basketdb.share_basket_with_group (id_bsk, id_group, cfg['CFG_WEBBASKET_SHARE_LEVELS']['ADDCMT'])
                basketdb.add_to_basket (int(id_user_val), (sysno, ), (id_bsk, ))

                __db_set_basket (key, id_bsk)

                email_address = run_sql("""SELECT email FROM user WHERE id = %s """, (id_user_val, ))[0][0]
                perform_request_send (uid, email_address, "", TEXT_RefereeSel_MSG_REFEREE_SUBJECT, TEXT_RefereeSel_MSG_REFEREE_BODY, 0, 0, 0, ln, 1)
                sendMailToReferee(doctype, categ, RN, email_address, authors)

                group_name = run_sql("""SELECT name FROM usergroup WHERE id = %s""", (id_group, ))[0][0]
                perform_request_send (int(id_user_val), "", group_name, TEXT_RefereeSel_MSG_GROUP_SUBJECT, TEXT_RefereeSel_MSG_GROUP_BODY)
                sendMailToGroup(doctype, categ, RN, id_group, authors)
            return __displayCplxDocument(req, doctype, categ, RN, apptype, reply, commentId, ln)

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
            try:
                users1 = run_sql("""SELECT id, email FROM user WHERE email <> "" AND email RLIKE %s ORDER BY email """, (email_user_pattern, ))
            except OperationalError:
                users1 = ()
            # no users that match the pattern
            if not users1:
                stopon1 = '<p>%s</p>' % _("no qualified users, try new search.")
            elif len(users1) > MAXSELECTUSERS:
                stopon1 = '<p><strong>%s %s</strong>, %s (%s %s)</p>' % (len(users1), _("hits"), _("too many qualified users, specify more narrow search."), _("limit"), MAXSELECTUSERS)

            # show matching users
            else:
                users = []
                for (user_id, email) in users1:
                    users.append([user_id, email,''])

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
            t += "%(infos)s<br /><br />" % {'infos': infos[0]}

        t += """
  <form action="publiline.py">
    <input type="hidden" name="flow" value="cplx" />
    <input type="hidden" name="doctype" value="%(doctype)s" />
    <input type="hidden" name="categ" value="%(categ)s" />
    <input type="hidden" name="RN" value="%(rn)s" />
    <input type="hidden" name="apptype" value="%(apptype)s" />
    <input type="submit" class="formbutton" value="%(button_label)s" />
  </form>""" % {'doctype': doctype,
                'categ': categ,
                'rn': RN,
                'apptype': apptype,
                'button_label': _("Come back to the document"),
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
            for user in acc_get_role_users(acc_get_role_id("pubcomchair_%s_%s" % (doctype, categ))):
                user_addr += run_sql("""SELECT email FROM user WHERE id = %s """, (user[0], ))[0][0] + ","
            # And if there are general publication committee chair's
            for user in acc_get_role_users(acc_get_role_id("pubcomchair_%s_*" % doctype)):
                user_addr += run_sql("""SELECT email FROM user WHERE id = %s """, (user[0], ))[0][0] + ","
            user_addr = re.sub(",$", "", user_addr)
            group_addr = ""
            TEXT_RefereeRecom_MSG_SUBJECT = TEXT_RSN_RefereeRecom_MSG_PUBCOM_SUBJECT
        elif apptype == "RPB":
            user_addr = ""
            group_addr = RN
            TEXT_RefereeRecom_MSG_SUBJECT = TEXT_RPB_RefereeRecom_MSG_EDBOARD_SUBJECT
        else:
            user_addr = ""
            group_addr = ""
            TEXT_RefereeRecom_MSG_SUBJECT = ""

        if validate == "approve" or validate == "reject":
            if dRefereeRecom == None:
                perform_request_send (uid, user_addr, group_addr, msg_subject, msg_body, 0, 0, 0, ln, 1)

                if validate == "approve":
                    msg_body = "Approved : " + msg_body
                else:
                    msg_body = "Rejected : " + msg_body

                #Get the Project Leader's email address
#                email = ""
#                for user in acc_get_role_users(acc_get_role_id("projectleader_%s_%s" % (doctype, categ))):
#                    email += run_sql("""SELECT email FROM user WHERE id = %s """, (user[0], ))[0][0] + ","
#                sendMailToProjectLeader(doctype, categ, RN, email, authors, "referee", msg_body)
                sendMailtoCommitteeChair(doctype, categ, RN, user_addr, authors)
                __db_set_RefereeRecom_time (key)
            return __displayCplxDocument(req, doctype, categ, RN, apptype, reply, commentId, ln)

        t = websubmit_templates.tmpl_publiline_displaycplxrecom (
              ln = ln,
              doctype = doctype,
              categ = categ,
              rn = RN,
              apptype = apptype,
              action = action,
              status = status,
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
        for user in acc_get_role_users(acc_get_role_id("pubcomchair_%s_%s" % (doctype, categ))):
            user_addr += run_sql("""SELECT nickname FROM user WHERE id = %s """, (user[0], ))[0][0] + ","
        # And if there are general publication committee chair's
        for user in acc_get_role_users(acc_get_role_id("pubcomchair_%s_*" % doctype)):
            user_addr += run_sql("""SELECT nickname FROM user WHERE id = %s """, (user[0], ))[0][0] + ","
        user_addr = re.sub(",$", "", user_addr)

        if validate == "go":
            if dEdBoardRecom == None:
                perform_request_send (uid, user_addr, "", msg_subject, msg_body)
                __db_set_EdBoardRecom_time (key)
            return __displayCplxDocument(req, doctype, categ, RN, apptype, reply, commentId, ln)

        t = websubmit_templates.tmpl_publiline_displaycplxrecom (
              ln = ln,
              doctype = doctype,
              categ = categ,
              rn = RN,
              apptype = apptype,
              action = action,
              status = status,
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
        for user in acc_get_role_users(acc_get_role_id("projectleader_%s_%s" % (doctype, categ))):
            user_addr += run_sql("""SELECT email FROM user WHERE id = %s """, (user[0], ))[0][0] + ","
        # And if there are general project leader's
        for user in acc_get_role_users(acc_get_role_id("projectleader_%s_*" % doctype)):
            user_addr += run_sql("""SELECT email FROM user WHERE id = %s """, (user[0], ))[0][0] + ","
        user_addr = re.sub(",$", "", user_addr)

        if apptype == "RRP":
            TEXT_PubComRecom_MSG_SUBJECT = TEXT_RSN_PubComRecom_MSG_PRJLEADER_SUBJECT
        elif apptype == "RPB":
            group_addr = RN
            TEXT_PubComRecom_MSG_SUBJECT = TEXT_RPB_PubComRecom_MSG_PRJLEADER_SUBJECT
        else:
            TEXT_PubComRecom_MSG_SUBJECT = ""

        if validate == "approve" or validate == "reject":

            if validate == "approve":
                msg_body = "Approved : " + msg_body
            else:
                msg_body = "Rejected : " + msg_body

            if dPubComRecom == None:
                perform_request_send (uid, user_addr, "", msg_subject, msg_body, 0, 0, 0, ln, 1)
                sendMailToProjectLeader(doctype, categ, RN, user_addr, authors, "publication committee chair", msg_body)
                __db_set_PubComRecom_time (key)
            return __displayCplxDocument(req, doctype, categ, RN, apptype, reply, commentId, ln)

        t = websubmit_templates.tmpl_publiline_displaycplxrecom (
              ln = ln,
              doctype = doctype,
              categ = categ,
              rn = RN,
              apptype = apptype,
              action = action,
              status = status,
              authors = authors,
              title = title,
              sysno = sysno,
              msg_to = user_addr,
              msg_to_group = "",
              msg_subject = TEXT_PubComRecom_MSG_SUBJECT + " " + "\"" + item_details['title'] + "\"",
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
  </form>""" % {'doctype': doctype,
                'categ': categ,
                'rn': RN,
                'apptype': apptype,
                'button_label': _("Back to the document"),
               }

        if validate == "approve":
            if dProjectLeaderAction == None:
                (errors, infos) = perform_request_save_comment (uid, id_bskBASKET, sysno, msg_subject, msg_body, ln)
                out = "%(infos)s<br /><br />" % {'infos': infos[0]}

                sendMailToSubmitter(doctype, categ, RN, "approved")
                __db_set_status (key, 'approved')
            return out + t

        elif validate == "reject":
            if dProjectLeaderAction == None:
                (errors, infos) = perform_request_save_comment (uid, id_bskBASKET, sysno, msg_subject, msg_body, ln)
                out = "%(infos)s<br /><br />" % {'infos': infos[0]}

                sendMailToSubmitter(doctype, categ, RN, "rejected")
                __db_set_status (key, 'rejected')
            return out + t

        validation = """
    <select name="validate">
      <option value="%(select)s"> %(select)s</option>
      <option value="approve">%(approve)s</option>
      <option value="reject">%(reject)s</option>
    </select>
    <input type="submit" class="formbutton" value="%(button_label)s" />""" % {'select': _('Select:'),
                                                                              'approve': _('Approve'),
                                                                              'reject': _('Reject'),
                                                                              'button_label': _('Take a decision'),
                                                                             }

        if apptype == "RRP":
            TEXT_ProjectLeaderDecision_MSG_SUBJECT = TEXT_RSN_ProjectLeaderDecision_MSG_SUBJECT
        elif apptype == "RPB":
            TEXT_ProjectLeaderDecision_MSG_SUBJECT = TEXT_RPB_ProjectLeaderDecision_MSG_SUBJECT
        else:
            TEXT_ProjectLeaderDecision_MSG_SUBJECT = ""

        t = websubmit_templates.tmpl_publiline_displaywritecomment(doctype, categ, RN, apptype, action, _("Take a decision"), TEXT_ProjectLeaderDecision_MSG_SUBJECT, validation, "", ln)

        return t

    elif (action == "ProjectLeaderDecision") and (apptype == "RDA"):
        if __is_ProjectLeader (req, doctype, categ) != 0:
            return _("Action unauthorized for this document.") + "<br />&nbsp;"

        if status == "cancelled":
            return _("Action unavailable for this document.") + "<br />&nbsp;"

        if validate == "approve":
            if dProjectLeaderAction == None:
                __db_set_status (key, 'approved')
            return __displayCplxDocument(req, doctype, categ, RN, apptype, reply, commentId, ln)

        elif validate == "reject":
            if dProjectLeaderAction == None:
                __db_set_status (key, 'rejected')
            return __displayCplxDocument(req, doctype, categ, RN, apptype, reply, commentId, ln)

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
                 'rn': RN,
                 'categ': categ,
                 'doctype': doctype,
                 'apptype': apptype,
                 'action': action,
                 'approve': _('Approve'),
                 'reject': _('Reject'),
               }

        return t

    elif (action == "AuthorCancel") and ((apptype == "RRP") or (apptype == "RPB") or (apptype == "RDA")):
        if __is_Author (uid, sysno) != 0:
            return _("Action unauthorized for this document.") + "<br />&nbsp;"

        if (status == "cancelled") or (dProjectLeaderAction != None):
            return _("Action unavailable for this document.") + "<br />&nbsp;"

        if validate == "go":
            __db_set_status (key, 'cancelled')
            return __displayCplxDocument(req, doctype, categ, RN, apptype, reply, commentId, ln)

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
                 'rn': RN,
                 'categ': categ,
                 'doctype': doctype,
                 'apptype': apptype,
                 'action': action,
                 'cancel': _('Cancel'),
               }
        return t

    else:
        return _("Wrong action for this document.") + "<br />&nbsp;"

    return t

def get_pending_item_details(doctype, reportnumber):
    """Given a doctype and reference number, try to retrieve an item's details.
       The first place to search for them should be the WebSubmit pending
       directory. If nothing is retrieved from there, and attempt is made
       to retrieve them from the Invenio repository itself.
       @param doctype: (string) - the doctype of the item for which brief
        details are to be retrieved.
       @param reportnumber: (string) - the report number of the item
        for which details are to be retrieved.
       @return: (dictionary or None) - If details are found for the item,
        they will be returned in a dictionary structured as follows:
            { 'title'         : '-', ## String - the item's title
              'recid'         : '',  ## String - recid taken from the SN file
              'report-number' : '',  ## String - the item's report number
              'authors'       : [],  ## List   - the item's authors
            }
        If no details were found a NoneType is returned.
    """
    ## First try to get the details of a document from the pending dir:
    item_details = get_brief_doc_details_from_pending(doctype, \
                                                      reportnumber)
    if item_details is None:
        item_details = get_brief_doc_details_from_repository(reportnumber)
    ## Return the item details:
    return item_details

def get_brief_doc_details_from_pending(doctype, reportnumber):
    """Try to get some brief details about the submission that is awaiting
       the referee's decision.
       Details sought are:
        + title
        + Authors
        + recid (why?)
        + report-number (why?)
       This function searches for a MARC XML record in the pending submission's
       working directory. It prefers the so-called 'dummy' record, but will
       search for the final MARC XML record that would usually be passed to
       bibupload (i.e. recmysql) if that is not present. If neither of these
       records are present, no details will be found.
       @param doctype: (string) - the WebSubmit document type of the item
        to be refereed. It is used in order to locate the submission's
        working directory in the WebSubmit pending directory.
       @param reportnumber: (string) - the report number of the item for
        which details are to be recovered. It is used in order to locate the
        submission's working directory in the WebSubmit pending directory.
       @return: (dictionary or None) - If details are found for the item,
        they will be returned in a dictionary structured as follows:
            { 'title'            : '-', ## String - the item's title
              'recid'            : '',  ## String - recid taken from the SN file
              'report-number'    : '',  ## String - the item's report number
              'authors'          : [],  ## List   - the item's authors
            }
        If no details were found (i.e. no MARC XML files in the submission's
        working directory), a NoneType is returned.
    """
    pending_doc_details = None
    marcxml_rec_name = None
    ## Check for a MARC XML record in the pending dir.
    ## If it's there, we will use it to obtain certain bibliographic
    ## information such as title, author(s), etc, which we will then
    ## display to the referee.
    ## We favour the "dummy" record (created with the WebSubmit function
    ## "Make_Dummy_MARC_XML_Record"), because it was made for this
    ## purpose. If it's not there though, we'll take the normal
    ## (final) recmysql record that would generally be passed to bibupload.
    if os.access("%s/%s/%s/%s" % (CFG_WEBSUBMIT_PENDING_DIR, \
                                  doctype, \
                                  reportnumber, \
                                  CFG_WEBSUBMIT_DUMMY_MARC_XML_REC), \
                 os.F_OK|os.R_OK):
        ## Found the "dummy" marc xml record in the submission dir.
        ## Use it:
        marcxml_rec_name = CFG_WEBSUBMIT_DUMMY_MARC_XML_REC
    elif os.access("%s/%s/%s/%s" % (CFG_WEBSUBMIT_PENDING_DIR, \
                                    doctype, \
                                    reportnumber, \
                                    CFG_WEBSUBMIT_MARC_XML_REC), \
                   os.F_OK|os.R_OK):
        ## Although we didn't find the "dummy" marc xml record in the
        ## submission dir, we did find the "real" one (that which would
        ## normally be passed to bibupload). Use it:
        marcxml_rec_name = CFG_WEBSUBMIT_MARC_XML_REC

    ## If we have a MARC XML record in the pending submission's
    ## working directory, go ahead and use it:
    if marcxml_rec_name is not None:
        try:
            fh_marcxml_record = open("%s/%s/%s/%s" \
                                     % (CFG_WEBSUBMIT_PENDING_DIR, \
                                        doctype, \
                                        reportnumber, \
                                        marcxml_rec_name), "r")
            xmltext = fh_marcxml_record.read()
            fh_marcxml_record.close()
        except IOError:
            ## Unfortunately, it wasn't possible to read the details of the
            ## MARC XML record. Register the exception.
            exception_prefix = "Error: Publiline was unable to read the " \
                               "MARC XML record [%s/%s/%s/%s] when trying to " \
                               "use it to recover details about a pending " \
                               "submission." % (CFG_WEBSUBMIT_PENDING_DIR, \
                                                doctype, \
                                                reportnumber, \
                                                marcxml_rec_name)
            register_exception(prefix=exception_prefix)
        else:
            ## Attempt to use bibrecord to create an internal representation
            ## of the record, from which we can extract certain bibliographic
            ## information:
            records = create_records(xmltext, 1, 1)
            try:
                record = records[0][0]
                if record is None:
                    raise ValueError
            except (IndexError, ValueError):
                ## Bibrecord couldn't successfully represent the record
                ## contained in the xmltext string. The record must have
                ## been empty or badly formed (or something).
                pass
            else:
                ## Dictionary to hold the interesting details of the
                ## pending item:
                pending_doc_details = { 'title': '-',
                                        'recid': '',
                                        'report-number': '',
                                        'authors': [],
                                      }
                ## Get the recid:
                ## Note - the old "getInPending" function reads the "SN"
                ## file from the submission's working directory and since
                ## the "SN" file is currently "magic" and hardcoded
                ## throughout WebSubmit, I'm going to stick to this model.
                ## I could, however, have tried to get it from the MARC XML
                ## record as so:
                ## recid = record_get_field_value(rec=record, tag="001")
                try:
                    fh_recid = open("%s/%s/%s/SN" \
                                    % (CFG_WEBSUBMIT_PENDING_DIR, \
                                       doctype, \
                                       reportnumber), "r")
                    recid = fh_recid.read()
                    fh_recid.close()
                except IOError:
                    ## Probably, there was no "SN" file in the submission's
                    ## working directory.
                    pending_doc_details['recid'] = ""
                else:
                    pending_doc_details['recid'] = recid.strip()

                ## Item report number (from record):
                ## Note: I don't know what purpose this serves. It appears
                ## to be used in the email that is sent to the author, but
                ## it seems funny to me, since we already have the report
                ## number (which is indeed used to find the submission's
                ## working directory in pending). Perhaps it's used for
                ## cases when the reportnumber is changed after approval?
                ## To investigate when time allows:
                finalrn = record_get_field_value(rec=record, \
                                                 tag="037", \
                                                 code="a")
                if finalrn != "":
                    pending_doc_details['report-number'] = finalrn

                ## Item title:
                title = record_get_field_value(rec=record, \
                                               tag="245", \
                                               code="a")
                if title != "":
                    pending_doc_details['title'] = title
                else:
                    ## Alternative title:
                    alt_title = record_get_field_value(rec=record, \
                                                       tag="246", \
                                                       ind1="1", \
                                                       code="a")
                    if alt_title != "":
                        pending_doc_details['title'] = alt_title

                ## Item first author:
                first_author = record_get_field_value(rec=record, \
                                                      tag="100", \
                                                      code="a")
                if first_author != "":
                    pending_doc_details['authors'].append(first_author)

                ## Other Authors:
                other_authors = record_get_field_values(rec=record, \
                                                        tag="700", \
                                                        code="a")
                for author in other_authors:
                    pending_doc_details['authors'].append(author)

    ## Return the details discovered about the pending document:
    return pending_doc_details


def get_brief_doc_details_from_repository(reportnumber):
    """Try to get some brief details about the submission that is awaiting
       the referee's decision.
       Details sought are:
        + title
        + Authors
        + recid (why?)
        + report-number (why?)
        + email
       This function searches in the Invenio repository, based on
       "reportnumber" for a record and then pulls the interesting fields
       from it.
       @param reportnumber: (string) - the report number of the item for
        which details are to be recovered. It is used in the search.
       @return: (dictionary or None) - If details are found for the item,
        they will be returned in a dictionary structured as follows:
            { 'title'            : '-', ## String - the item's title
              'recid'            : '',  ## String - recid taken from the SN file
              'report-number'    : '',  ## String - the item's report number
              'authors'          : [],  ## List   - the item's authors
            }
        If no details were found a NoneType is returned.
    """
    ## Details of the pending document, as found in the repository:
    pending_doc_details = None
    ## Search for records matching this "report number"
    found_record_ids = list(search_pattern(req=None, \
                                           p=reportnumber, \
                                           f="reportnumber", \
                                           m="e"))
    ## How many records were found?
    if len(found_record_ids) == 1:
        ## Found only 1 record. Get the fields of interest:
        pending_doc_details = { 'title': '-',
                                'recid': '',
                                'report-number': '',
                                'authors': [],
                                'email': '',
                              }
        recid = found_record_ids[0]
        ## Authors:
        first_author  = get_fieldvalues(recid, "100__a")
        for author in first_author:
            pending_doc_details['authors'].append(author)
        other_authors = get_fieldvalues(recid, "700__a")
        for author in other_authors:
            pending_doc_details['authors'].append(author)
        ## Title:
        title = get_fieldvalues(recid, "245__a")
        if len(title) > 0:
            pending_doc_details['title'] = title[0]
        else:
            ## There was no value for title - check for an alternative title:
            alt_title = get_fieldvalues(recid, "2641_a")
            if len(alt_title) > 0:
                pending_doc_details['title'] = alt_title[0]
        ## Record ID:
        pending_doc_details['recid'] = recid
        ## Report Number:
        reptnum = get_fieldvalues(recid, "037__a")
        if len(reptnum) > 0:
            pending_doc_details['report-number'] = reptnum[0]
        ## Email:
        email = get_fieldvalues(recid, "859__f")
        if len(email) > 0:
            pending_doc_details['email'] = email[0]
    elif len(found_record_ids) > 1:
        ## Oops. This is unexpected - there shouldn't be me multiple matches
        ## for this item. The old "getInAlice" function would have simply
        ## taken the first record in the list. That's not very nice though.
        ## Some kind of warning or error should be raised here. FIXME.
        pass
    return pending_doc_details


# Retrieve info about document
def getInfo(RN):
    """
    Retrieve basic info from record with given report number.
    Returns (authors, title, sysno)
    """
    authors = None
    title = None
    sysno = None

    recids = search_pattern(p=RN, f='037__a')
    if len(recids) == 1:
        sysno = int(recids.tolist()[0])
        authors = ','.join(get_fieldvalues(sysno, "100__a") + get_fieldvalues(sysno, "700__a"))
        title = ','.join(get_fieldvalues(sysno, "245__a"))

    return (authors, title, sysno)

#seek info in pending directory
def getInPending(doctype, categ, RN):
    """FIXME: DEPRECATED!"""
    PENDIR = "%s/pending" % CFG_WEBSUBMIT_STORAGEDIR
    if os.path.exists("%s/%s/%s/AU" % (PENDIR, doctype, RN)):
        fp = open("%s/%s/%s/AU" % (PENDIR, doctype, RN),"r")
        authors = fp.read()
        fp.close()
    else:
        authors = ""
    if os.path.exists("%s/%s/%s/TI" % (PENDIR, doctype, RN)):
        fp = open("%s/%s/%s/TI" % (PENDIR, doctype, RN),"r")
        title = fp.read()
        fp.close()
    else:
        title = ""
    if os.path.exists("%s/%s/%s/SN" % (PENDIR, doctype, RN)):
        fp = open("%s/%s/%s/SN" % (PENDIR, doctype, RN),"r")
        sysno = fp.read()
        fp.close()
    else:
        sysno = ""
    if title == "" and os.path.exists("%s/%s/%s/TIF" % (PENDIR, doctype, RN)):
        fp = open("%s/%s/%s/TIF" % (PENDIR, doctype, RN),"r")
        title = fp.read()
        fp.close()
    if title == "":
        return 0
    else:
        return (authors, title, sysno,"")

#seek info in Alice database
def getInAlice(doctype, categ, RN):
    """FIXME: DEPRECATED!"""
    # initialize sysno variable
    sysno = ""
    searchresults = list(search_pattern(req=None, p=RN, f="reportnumber"))
    if len(searchresults) == 0:
        return 0
    sysno = searchresults[0]
    if sysno != "":
        title = Get_Field('245__a', sysno)
        emailvalue = Get_Field('8560_f', sysno)
        authors = Get_Field('100__a', sysno)
        authors += "\n%s" % Get_Field('700__a', sysno)
        newrn = Get_Field('037__a', sysno)
        return (authors, title, sysno, newrn)
    else:
        return 0

def SendEnglish(doctype, categ, RN, title, authors, access, sysno):
    FROMADDR = '%s Submission Engine <%s>' % (CFG_SITE_NAME, CFG_SITE_SUPPORT_EMAIL)
    # retrieve useful information from webSubmit configuration
    res = run_sql("select value from sbmPARAMETERS where name='categformatDAM' and doctype=%s", (doctype,))
    categformat = res[0][0]
    categformat = re.sub("<CATEG>", "([^-]*)", categformat)
    categs = re.match(categformat, RN)
    if categs is not None:
        categ = categs.group(1)
    else:
        categ = "unknown"
    res = run_sql("select value from sbmPARAMETERS where name='addressesDAM' and doctype=%s",(doctype,))
    if len(res) > 0:
        otheraddresses = res[0][0]
        otheraddresses = otheraddresses.replace("<CATEG>", categ)
    else:
        otheraddresses = ""
    # Build referee's email address
    refereeaddress = ""
    # Try to retrieve the referee's email from the referee's database
    for user in acc_get_role_users(acc_get_role_id("referee_%s_%s" % (doctype, categ))):
        refereeaddress += user[1] + ","
    # And if there are general referees
    for user in acc_get_role_users(acc_get_role_id("referee_%s_*" % doctype)):
        refereeaddress += user[1] + ","
    refereeaddress = re.sub(",$", "", refereeaddress)
    # Creation of the mail for the referee
    addresses = ""
    if refereeaddress != "":
        addresses = refereeaddress + ","
    if otheraddresses != "":
        addresses += otheraddresses
    else:
        addresses = re.sub(",$", "", addresses)
    if addresses == "":
        SendWarning(doctype, categ, RN, title, authors, access)
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
    <%s/%s/%s/files/>

    To approve/reject the document, you should go to this URL:
    <%s/approve.py?access=%s>

    ---------------------------------------------
    Best regards.
    The submission team.""" % (RN, title, authors, CFG_SITE_URL, CFG_SITE_RECORD, sysno, CFG_SITE_URL, access)
    # send the mail
    send_email(FROMADDR, addresses,"Request for Approval of %s" % RN, message, footer="")
    return ""

def send_approval(doctype, categ, rn, title, authors, access, sysno):
    fromaddr = '%s Submission Engine <%s>' % (CFG_SITE_NAME, CFG_SITE_SUPPORT_EMAIL)
    if not categ:
        categ = "nocategory"
    if not doctype:
        doctype = "nodoctype"
    addresses = acc_get_authorized_emails('referee', categ=categ, doctype=doctype)
    if not addresses:
        return SendWarning(doctype, categ, rn, title, authors, access)
    if not authors:
        authors = "-"
    message = """
    The document %s has been published as a Communication.
    Your approval is requested for it to become an official Note.

    Title: %s

    Author(s): %s

    To access the document(s), select the file(s) from the location:
    <%s/record/%s/files/>

    As a referee for this document, you may approve or reject it
    from the submission interface:
    <%s/submit?doctype=%s>

    ---------------------------------------------
    Best regards.
    The submission team.""" % (rn, title, authors, CFG_SITE_URL, sysno, CFG_SITE_URL, doctype)
    # send the mail
    return send_email(fromaddr, ', '.join(addresses), "Request for Approval of %s" % rn, message, footer="")

def SendWarning(doctype, categ, RN, title, authors, access):
    FROMADDR = '%s Submission Engine <%s>' % (CFG_SITE_NAME, CFG_SITE_SUPPORT_EMAIL)
    message = "Failed sending approval email request for %s" % RN
    # send the mail
    send_email(FROMADDR, CFG_SITE_ADMIN_EMAIL, "Failed sending approval email request", message)
    return ""

def sendMailToReferee(doctype, categ, RN, email, authors):
    item_details = get_brief_doc_details_from_repository(RN)
    ## get_brief_doc_details_from_repository has returned either None
    ## or a dictionary with the following structure:
    ##   { 'title'            : '-', ## String - the item's title
    ##     'recid'            : '',  ## String - recid
    ##     'report-number'    : '',  ## String - the item's report number
    ##     'authors'          : [],  ## List   - the item's authors
    ##   }


    FROMADDR = '%s Submission Engine <%s>' % (CFG_SITE_NAME, CFG_SITE_SUPPORT_EMAIL)

    message = """
    Scientific Note approval for document %s has been submitted to the CERN Document Server.
    Your recommendation is requested on it.

    Requested subcategory: %s

    Title: %s

    Author(s): %s

    To access the document(s), select the file(s) from the location:
    <%s/%s/%s>

    To make a reccommendation, you should go to this URL:
    <%s>

    You can also check the status of the document:
    <%s>

    ---------------------------------------------
    Best regards.
    The submission team.""" % (str(RN),
                               str(categ),
                               str(item_details['title']),
                               authors,
                               CFG_SITE_URL,
                               CFG_SITE_URL,
                               str(item_details['recid']),
                               str(CFG_SITE_URL + "/publiline.py?flow=cplx&doctype="+doctype+"&ln=en&apptype=RRP&categ="+categ+"&RN="+RN+"&action=RefereeRecom"),
                               str(CFG_SITE_URL + "/publiline.py?flow=cplx&doctype="+doctype+"&ln=en&apptype=RRP&categ="+categ+"&RN="+RN))

    # send the mail
    send_email(FROMADDR, email,"Request for document %s recommendation" % (RN), message)
    return ""

def sendMailToGroup(doctype, categ, RN, group_id, authors):
    item_details = get_brief_doc_details_from_repository(RN)
    ## get_brief_doc_details_from_repository has returned either None
    ## or a dictionary with the following structure:
    ##   { 'title'            : '-', ## String - the item's title
    ##     'recid'            : '',  ## String - recid
    ##     'report-number'    : '',  ## String - the item's report number
    ##     'authors'          : [],  ## List   - the item's authors
    ##   }


    FROMADDR = '%s Submission Engine <%s>' % (CFG_SITE_NAME, CFG_SITE_SUPPORT_EMAIL)

    message = """
    Scientific Note approval for document %s has been submitted to the CERN Document Server.
    Your comments are requested on this document.

    Requested subcategory: %s

    Title: %s

    Author(s): %s

    To access the document(s), select the file(s) from the location:
    <%s/%s/%s>

    To leave a comment or check the status of the approval process, you should go to this URL:
    <%s>

    """ % (str(RN),
           str(categ),
           str(item_details['title']),
           authors,
           CFG_SITE_URL,
           CFG_SITE_RECORD,
           str(item_details['recid']),
           str(CFG_SITE_URL + "/publiline.py?flow=cplx&doctype="+doctype+"&ln=en&apptype=RRP&categ="+categ+"&RN="+RN))

    # send mails to all members of the ATLAS group
    group_member_ids = run_sql("SELECT id_user FROM user_usergroup WHERE id_usergroup = '%s'" % (group_id))
    for member_id in group_member_ids:
        member_email = run_sql("SELECT email FROM user WHERE id = '%s'" % (member_id))
        if not member_email[0][0] == "info@invenio-software.org":
            send_email(FROMADDR, member_email[0][0],"Request for comment on document %s" % (RN), message)
    return ""

def sendMailToProjectLeader(doctype, categ, RN, email, authors, actor, recommendation):
    item_details = get_brief_doc_details_from_repository(RN)
    ## get_brief_doc_details_from_repository has returned either None
    ## or a dictionary with the following structure:
    ##   { 'title'            : '-', ## String - the item's title
    ##     'recid'            : '',  ## String - recid
    ##     'report-number'    : '',  ## String - the item's report number
    ##     'authors'          : [],  ## List   - the item's authors
    ##   }

    FROMADDR = '%s Submission Engine <%s>' % (CFG_SITE_NAME, CFG_SITE_SUPPORT_EMAIL)

    message = """
    Scientific Note approval for document %s has been submitted to the CERN Document Server.
    Your approval is requested for this document. Once you have received recommendations from both the referee and the publication committee chair, you will be able to make your decision.

    Requested subcategory: %s

    Title: %s

    Author(s): %s

    To access the document(s), select the file(s) from the location:
    <%s/%s/%s>

    The %s has made a recommendation for the document. He/she said the following:

    %s

    You can approve this document by visiting this page:
    <%s>

    You can also check the status of the document from:
    <%s>

    """ % (str(RN),
           str(categ),
           str(item_details['title']),
           authors,
           CFG_SITE_URL,
           CFG_SITE_RECORD,
           str(item_details['recid']),
           actor,
           recommendation,
           str(CFG_SITE_URL + "/publiline.py?flow=cplx&doctype="+doctype+"&ln=en&apptype=RRP&categ="+categ+"&RN="+RN+"&action=ProjectLeaderDecision"),
           str(CFG_SITE_URL + "/publiline.py?flow=cplx&doctype="+doctype+"&ln=en&apptype=RRP&categ="+categ+"&RN="+RN))

    # send mails to all members of the ATLAS group
    send_email(FROMADDR, email,"Request for approval/rejection of document %s" % (RN), message)
    return ""

def sendMailToSubmitter(doctype, categ, RN, outcome):
    item_details = get_brief_doc_details_from_repository(RN)
    ## get_brief_doc_details_from_repository has returned either None
    ## or a dictionary with the following structure:
    ##   { 'title'            : '-', ## String - the item's title
    ##     'recid'            : '',  ## String - recid
    ##     'report-number'    : '',  ## String - the item's report number
    ##     'authors'          : [],  ## List   - the item's authors
    ##   }

    FROMADDR = '%s Submission Engine <%s>' % (CFG_SITE_NAME, CFG_SITE_SUPPORT_EMAIL)

    message = """
    The approval process for your document : %s, has been completed. The details of this document are as follows:

    Requested subcategory: %s
    Title: %s

    The project leader has made the following recommendation for the document:

    %s
    """ % (RN, categ, item_details['title'], outcome)

    # send mails to all members of the ATLAS group
    send_email(FROMADDR, item_details['email'],"Final outcome for approval of document : %s" % (RN), message)
    return ""

def sendMailtoCommitteeChair(doctype, categ, RN, email, authors):
    item_details = get_brief_doc_details_from_repository(RN)
    ## get_brief_doc_details_from_repository has returned either None
    ## or a dictionary with the following structure:
    ##   { 'title'            : '-', ## String - the item's title
    ##     'recid'            : '',  ## String - recid
    ##     'report-number'    : '',  ## String - the item's report number
    ##     'authors'          : [],  ## List   - the item's authors
    ##   }

    FROMADDR = '%s Submission Engine <%s>' % (CFG_SITE_NAME, CFG_SITE_SUPPORT_EMAIL)

    message = """
    The referree assigned to the document detailed below has made a reccommendation. You are now requested to make a reccommendation of your own.

    Requested subcategory: %s

    Title: %s

    Author(s): %s

    To access the document(s), select the file(s) from the location:
    <%s/%s/%s>

    You can make a reccommendation by visiting this page:
    <%s>
    """ % (str(categ),
           str(item_details['title']),
           authors,
           CFG_SITE_URL,
           CFG_SITE_RECORD,
           str(item_details['recid']),
           str(CFG_SITE_URL + "/publiline.py?flow=cplx&doctype="+doctype+"&ln=en&apptype=RRP&categ="+categ+"&RN="+RN))

    # send mails to all members of the ATLAS group
    send_email(FROMADDR, email,"Request for reccommendation of document %s" % (RN), message)
