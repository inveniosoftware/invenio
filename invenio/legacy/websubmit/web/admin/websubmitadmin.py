# -*- coding: utf-8 -*-

# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

from invenio.legacy.websubmit.admin_engine import *
from invenio.config import CFG_SITE_LANG
from invenio.legacy.webuser import getUid, page_not_authorized
from invenio.legacy.webpage import page
from invenio.base.i18n import wash_language, gettext_set_language

def index(req, ln=CFG_SITE_LANG):
    """Websubmit Admin home page. Default action: list all WebSubmit document types."""

    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (auth_code, auth_msg) = check_user(req, 'cfgwebsubmit')
    if not auth_code:
        ## user is authorised to use WebSubmit Admin:
        body = perform_request_list_doctypes()
        return page(title       = "Available WebSubmit Document Types",
                    body        = body,
                    navtrail    = get_navtrail(ln),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = ln)
    else:
        ## user is not authorised to use WebSubmit Admin:
        return page_not_authorized(req=req, text=auth_msg, navtrail=get_navtrail(ln))

def showall(req, ln=CFG_SITE_LANG):
    """Placeholder for the showall functionality"""

    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (auth_code, auth_msg) = check_user(req, 'cfgwebsubmit')
    if not auth_code:
        ## user is authorised to use WebSubmit Admin:
        body = perform_request_list_doctypes()
        return page(title       = "Available WebSubmit Document Types",
                    body        = body,
                    navtrail    = get_navtrail(ln),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = ln)
    else:
        ## user is not authorised to use WebSubmit Admin:
        return page_not_authorized(req=req, text=auth_msg, navtrail=get_navtrail(ln))

def doctypelist(req, ln=CFG_SITE_LANG):
    """List all WebSubmit document types."""

    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (auth_code, auth_msg) = check_user(req, 'cfgwebsubmit')
    if not auth_code:
        ## user is authorised to use WebSubmit Admin:
        body = perform_request_list_doctypes()
        return page(title       = "Available WebSubmit Document Types",
                    body        = body,
                    navtrail    = get_navtrail(ln),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = ln)
    else:
        ## user is not authorised to use WebSubmit Admin:
        return page_not_authorized(req=req, text=auth_msg, navtrail=get_navtrail(ln))


def jschecklist(req, ln=CFG_SITE_LANG):
    """List all WebSubmit JavaScript Checks (checks can be applied to form elements in WebSubmit.)"""

    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (auth_code, auth_msg) = check_user(req, 'cfgwebsubmit')
    if not auth_code:
        ## user is authorised to use WebSubmit Admin:
        body = perform_request_list_jschecks()
        return page(title       = "Available WebSubmit Checking Functions",
                    body        = body,
                    navtrail    = get_navtrail(ln),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = ln)
    else:
        ## user is not authorised to use WebSubmit Admin:
        return page_not_authorized(req=req, text=auth_msg, navtrail=get_navtrail(ln))


def actionlist(req, ln=CFG_SITE_LANG):
    """List all WebSubmit actions."""

    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (auth_code, auth_msg) = check_user(req, 'cfgwebsubmit')
    if not auth_code:
        ## user is authorised to use WebSubmit Admin:
        body = perform_request_list_actions()
        return page(title       = "Available WebSubmit Actions",
                    body        = body,
                    navtrail    = get_navtrail(ln),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = ln)
    else:
        ## user is not authorised to use WebSubmit Admin:
        return page_not_authorized(req=req, text=auth_msg, navtrail=get_navtrail(ln))


def functionlist(req, ln=CFG_SITE_LANG):
    """List all WebSubmit FUNCTIONS (Functions do the work of processing a submission)"""

    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (auth_code, auth_msg) = check_user(req, 'cfgwebsubmit')
    if not auth_code:
        ## user is authorised to use WebSubmit Admin:
        body = perform_request_list_functions()
        return page(title       = "Available WebSubmit Functions",
                    body        = body,
                    navtrail    = get_navtrail(ln),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = ln)
    else:
        ## user is not authorised to use WebSubmit Admin:
        return page_not_authorized(req=req, text=auth_msg, navtrail=get_navtrail(ln))

def elementlist(req, ln=CFG_SITE_LANG):
    """List all WebSubmit form ELEMENTS (elements are input fields on a WebSubmit form)"""

    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (auth_code, auth_msg) = check_user(req, 'cfgwebsubmit')
    if not auth_code:
        ## user is authorised to use WebSubmit Admin:
        body = perform_request_list_elements()
        return page(title       = "Available WebSubmit Elements",
                    body        = body,
                    navtrail    = get_navtrail(ln),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = ln)
    else:
        ## user is not authorised to use WebSubmit Admin:
        return page_not_authorized(req=req, text=auth_msg, navtrail=get_navtrail(ln))

def actionadd(req, actid=None, actname=None, working_dir=None, status_text=None, actcommit="", ln=CFG_SITE_LANG):
    """Add a new action to the WebSubmit database.
       Web form for action details will be displayed if "actid" and "actname" are empty; else
       new action will be committed to websubmit.
       @param actid: unique id for new action (if empty, Web form will be displayed)
       @param actname: name of new action (if empty, Web form will be displayed)
       @param working_dir: action working directory for WebSubmit
       @param status_text: status text displayed at end of WebSubmit action
       @param ln: language
       @return: page
    """

    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (auth_code, auth_msg) = check_user(req, 'cfgwebsubmit')
    if not auth_code:
        ## user is authorised to use WebSubmit Admin:
        # Generate content
        (title, body) = perform_request_add_action(actid, actname, working_dir, status_text, actcommit)
        return page(title       = title,
                    body        = body,
                    navtrail    = get_navtrail(ln),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = ln)
    else:
        ## user is not authorised to use WebSubmit Admin:
        return page_not_authorized(req=req, text=auth_msg, navtrail=get_navtrail(ln))

def actionedit(req, actid, actname=None, working_dir=None, status_text=None, actcommit="", ln=CFG_SITE_LANG):
    """Display the details of a WebSubmit action in a Web form so that it can be viewed and/or edited.
       @param actid: The unique action identifier code.
       @param actname: name of action (if present, action will be updated, else action details will be displayed)
       @param working_dir: action working directory for websubmit
       @param status_text: status text displayed at end of websubmit action
       @param ln: language
       @return: page
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (auth_code, auth_msg) = check_user(req, 'cfgwebsubmit')
    if not auth_code:
        ## user is authorised to use WebSubmit Admin:
        # Generate content
        (title, body) = perform_request_edit_action(actid, actname, working_dir, status_text, actcommit)
        return page(title       = title,
                    body        = body,
                    navtrail    = get_navtrail(ln),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = ln)
    else:
        ## user is not authorised to use WebSubmit Admin:
        return page_not_authorized(req=req, text=auth_msg, navtrail=get_navtrail(ln))

def jscheckadd(req, chname=None, chdesc=None, chcommit="", ln=CFG_SITE_LANG):
    """Add a new JavaScript CHECK to the WebSubmit database.
       Web form for action details will be displayed if "actid" and "actname" are empty; else
       new action will be committed to WebSubmit.
       @param chname: unique name/ID for new check (if empty, Web form will be displayed)
       @param chdesc: description of new JS check (the JavaScript code that is the check.) (If empty,
                      Web form will be displayed)
       @param ln: language
       @return: page
    """

    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (auth_code, auth_msg) = check_user(req, 'cfgwebsubmit')
    if not auth_code:
        ## user is authorised to use WebSubmit Admin:
        # Generate content
        (title, body) = perform_request_add_jscheck(chname, chdesc, chcommit)
        return page(title       = title,
                    body        = body,
                    navtrail    = get_navtrail(ln),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = ln)
    else:
        ## user is not authorised to use WebSubmit Admin:
        return page_not_authorized(req=req, text=auth_msg, navtrail=get_navtrail(ln))

def jscheckedit(req, chname, chdesc=None, chcommit="", ln=CFG_SITE_LANG):
    """Display the details of a WebSubmit checking function in a Web form so that it can be viewed
       and/or edited.
       @param chname: The unique Check name/identifier code.
       @param chdesc: The description of the Check (if present, Check will be updated, else Check
                      details will be displayed)
       @param ln: language
       @return: page
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (auth_code, auth_msg) = check_user(req, 'cfgwebsubmit')
    if not auth_code:
        ## user is authorised to use WebSubmit Admin:
        # Generate content
        (title, body) = perform_request_edit_jscheck(chname, chdesc, chcommit)
        return page(title       = title,
                    body        = body,
                    navtrail    = get_navtrail(ln),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = ln)
    else:
        ## user is not authorised to use WebSubmit Admin:
        return page_not_authorized(req=req, text=auth_msg, navtrail=get_navtrail(ln))

def elementadd(req, elname=None, elmarccode=None, eltype=None, elsize=None, elrows=None, elcols=None, elmaxlength=None, \
                elval=None, elfidesc=None, elmodifytext=None, elcommit="", ln=CFG_SITE_LANG):
    """Add a new WebSubmit ELEMENT to the WebSubmit database.
       @param elname: unique name/ID for new check (if empty, Web form will be displayed)
       @param elmarccode: MARC Code for element
       @param eltype: type of element.
       @param elsize: size of element.
       @param elrows: number of rows in element.
       @param elcols: number of columns in element.
       @param elmaxlength: element maximum length.
       @param elval: element value.
       @param elfidesc: element description.
       @param elmodifytext: Modification text for the element.
       @param elcommit: flag variable used to determine whether to commit element modifications or whether
                        to simply display a form containing element details.
       @param ln: language
       @return: page
    """

    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (auth_code, auth_msg) = check_user(req, 'cfgwebsubmit')
    if not auth_code:
        ## user is authorised to use WebSubmit Admin:
        # Generate content
        (title, body) = perform_request_add_element(elname, elmarccode, eltype, \
                                                    elsize, elrows, elcols, elmaxlength, \
                                                    elval, elfidesc, elmodifytext, \
                                                    elcommit)
        return page(title       = title,
                    body        = body,
                    navtrail    = get_navtrail(ln),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = ln)
    else:
        ## user is not authorised to use WebSubmit Admin:
        return page_not_authorized(req=req, text=auth_msg, navtrail=get_navtrail(ln))

def elementedit(req, elname, elmarccode=None, eltype=None, elsize=None, elrows=None, elcols=None, elmaxlength=None, \
                elval=None, elfidesc=None, elmodifytext=None, elcommit="", ln=CFG_SITE_LANG):
    """Display the details of a WebSubmit ELEMENT in a Web form so that it can be viewed
       and/or edited.
       @param elname: unique name/ID for new check (if empty, Web form will be displayed)
       @param elmarccode: MARC Code for element
       @param eltype: type of element.
       @param elsize: size of element.
       @param elrows: number of rows in element.
       @param elcols: number of columns in element.
       @param elmaxlength: element maximum length.
       @param elval: element value.
       @param elfidesc: element description.
       @param elmodifytext: Modification text for the element.
       @param elcommit: flag variable used to determine whether to commit element modifications or whether
                        to simply display a form containing element details.
       @param ln: language
       @return: page
    """

    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (auth_code, auth_msg) = check_user(req, 'cfgwebsubmit')
    if not auth_code:
        ## user is authorised to use WebSubmit Admin:
        # Generate content
        (title, body) = perform_request_edit_element(elname, elmarccode, eltype, \
                                                     elsize, elrows, elcols, elmaxlength, \
                                                     elval, elfidesc, elmodifytext, \
                                                     elcommit)
        return page(title       = title,
                    body        = body,
                    navtrail    = get_navtrail(ln),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = ln)
    else:
        ## user is not authorised to use WebSubmit Admin:
        return page_not_authorized(req=req, text=auth_msg, navtrail=get_navtrail(ln))

def functionadd(req, funcname=None, funcdescr=None, funcaddcommit="", ln=CFG_SITE_LANG):
    """Add a new function to WebSubmit"""
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (auth_code, auth_msg) = check_user(req, 'cfgwebsubmit')
    if not auth_code:
        ## user is authorised to use WebSubmit Admin:
        # Generate content
        (title, body) = perform_request_add_function(funcname=funcname,
                                                     funcdescr=funcdescr,
                                                     funcaddcommit=funcaddcommit)

        return page(title       = title,
                    body        = body,
                    navtrail    = get_navtrail(ln),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = ln)
    else:
        ## user is not authorised to use WebSubmit Admin:
        return page_not_authorized(req=req, text=auth_msg, navtrail=get_navtrail(ln))

def functionedit(req, funcname=None, funcdescr=None, funceditaddparam=None, funceditaddparamfree=None, \
                 funceditdelparam=None, funcdescreditcommit="", funcparamdelcommit="", funcparamaddcommit="", ln=CFG_SITE_LANG):
    """Edit a WebSubmit function"""
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (auth_code, auth_msg) = check_user(req, 'cfgwebsubmit')
    if not auth_code:
        ## user is authorised to use WebSubmit Admin:
        # Generate content
        (title, body) = perform_request_edit_function(funcname=funcname,
                                                      funcdescr=funcdescr,
                                                      funceditdelparam=funceditdelparam,
                                                      funceditaddparam=funceditaddparam,
                                                      funceditaddparamfree=funceditaddparamfree,
                                                      funcdescreditcommit=funcdescreditcommit,
                                                      funcparamdelcommit=funcparamdelcommit,
                                                      funcparamaddcommit=funcparamaddcommit
                                                                       )

        return page(title       = title,
                    body        = body,
                    navtrail    = get_navtrail(ln),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = ln)
    else:
        ## user is not authorised to use WebSubmit Admin:
        return page_not_authorized(req=req, text=auth_msg, navtrail=get_navtrail(ln))

def functionusage(req, funcname, ln=CFG_SITE_LANG):
    """View the usage cases (document-type and actions) in which a function is used.
       @param function: the function name
       @param ln: the language
       @return: a web page
    """

    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (auth_code, auth_msg) = check_user(req, 'cfgwebsubmit')
    if not auth_code:
        ## user is authorised to use WebSubmit Admin:
        body = perform_request_function_usage(funcname)
        return page(title       = "WebSubmit Function Usage",
                    body        = body,
                    navtrail    = get_navtrail(ln),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = ln)
    else:
        ## user is not authorised to use WebSubmit Admin:
        return page_not_authorized(req=req, text=auth_msg, navtrail=get_navtrail(ln))

def doctyperemove(req, doctype="", doctypedelete="", doctypedeleteconfirm="", ln=CFG_SITE_LANG):
    """Delete a WebSubmit document-type.
    @param doctype: the unique id of the document type to be deleted
    @param ln: the interface language
    @return: HTML page.
    """

    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (auth_code, auth_msg) = check_user(req, 'cfgwebsubmit')
    if not auth_code:
        ## user is authorised to use WebSubmit Admin:
        (title, body) = perform_request_remove_doctype(doctype=doctype,
                                                       doctypedelete=doctypedelete,
                                                       doctypedeleteconfirm=doctypedeleteconfirm)
        return page(title       = title,
                    body        = body,
                    navtrail    = get_navtrail(ln),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = ln)
    else:
        ## user is not authorised to use WebSubmit Admin:
        return page_not_authorized(req=req, text=auth_msg, navtrail=get_navtrail(ln))

def doctypeadd(req, doctype=None, doctypename=None, doctypedescr=None, clonefrom=None, doctypedetailscommit="", ln=CFG_SITE_LANG):
    """Add a new document type to WebSubmit"""
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (auth_code, auth_msg) = check_user(req, 'cfgwebsubmit')
    if not auth_code:
        ## user is authorised to use WebSubmit Admin:
        (title, body) = perform_request_add_doctype(doctype=doctype,
                                                                      doctypename=doctypename,
                                                                      doctypedescr=doctypedescr,
                                                                      clonefrom=clonefrom,
                                                                      doctypedetailscommit=doctypedetailscommit
                                                                      )

        return page(title       = title,
                    body        = body,
                    navtrail    = get_navtrail(ln),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = ln)
    else:
        ## user is not authorised to use WebSubmit Admin:
        return page_not_authorized(req=req, text=auth_msg, navtrail=get_navtrail(ln))

def doctypeconfiguresubmissionpageelements(req,
                                           doctype="",
                                           action="",
                                           pagenum="",
                                           movefieldfromposn="",
                                           movefieldtoposn="",
                                           deletefieldposn="",
                                           editfieldposn="",
                                           editfieldposncommit="",
                                           addfield="",
                                           addfieldcommit="",
                                           fieldname="",
                                           fieldtext="",
                                           fieldlevel="",
                                           fieldshortdesc="",
                                           fieldcheck="",
                                           ln=CFG_SITE_LANG):
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (auth_code, auth_msg) = check_user(req, 'cfgwebsubmit')
    if not auth_code:
        ## user is authorised to use WebSubmit Admin:
        (title, body) = perform_request_configure_doctype_submissionpage_elements(doctype=doctype,
                                                                                                    action=action,
                                                                                                    pagenum=pagenum,
                                                                                                    movefieldfromposn=movefieldfromposn,
                                                                                                    movefieldtoposn=movefieldtoposn,
                                                                                                    deletefieldposn=deletefieldposn,
                                                                                                    editfieldposn=editfieldposn,
                                                                                                    editfieldposncommit=editfieldposncommit,
                                                                                                    addfield=addfield,
                                                                                                    addfieldcommit=addfieldcommit,
                                                                                                    fieldname=fieldname,
                                                                                                    fieldtext=fieldtext,
                                                                                                    fieldlevel=fieldlevel,
                                                                                                    fieldshortdesc=fieldshortdesc,
                                                                                                    fieldcheck=fieldcheck)
        return page(title       = title,
                    body        = body,
                    navtrail    = get_navtrail(ln),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = ln)
    else:
        ## user is not authorised to use WebSubmit Admin:
        return page_not_authorized(req=req, text=auth_msg, navtrail=get_navtrail(ln))


def doctypeconfiguresubmissionpagespreview(req,
                                           doctype="",
                                           action="",
                                           pagenum="",
                                           ln=CFG_SITE_LANG):
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (auth_code, auth_msg) = check_user(req, 'cfgwebsubmit')
    if not auth_code:
        ## user is authorised to use WebSubmit Admin:
        (title, body) = perform_request_configure_doctype_submissionpage_preview(doctype=doctype,
                                                                                 action=action,
                                                                                 pagenum=pagenum)
        return page(title       = title,
                    body        = body,
                    navtrail    = get_navtrail(ln),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = ln)

    else:
        ## user is not authorised to use WebSubmit Admin:
        return page_not_authorized(req=req, text=auth_msg, navtrail=get_navtrail(ln))



def doctypeconfiguresubmissionpages(req,
                                    doctype="",
                                    action="",
                                    pagenum="",
                                    movepage="",
                                    movepagedirection="",
                                    deletepage="",
                                    deletepageconfirm="",
                                    addpage="",
                                    ln=CFG_SITE_LANG
                                   ):
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (auth_code, auth_msg) = check_user(req, 'cfgwebsubmit')
    if not auth_code:
        ## user is authorised to use WebSubmit Admin:
        (title, body) = perform_request_configure_doctype_submissionpages(doctype=doctype,
                                                                                            action=action,
                                                                                            pagenum=pagenum,
                                                                                            movepage=movepage,
                                                                                            movepagedirection=movepagedirection,
                                                                                            deletepage=deletepage,
                                                                                            deletepageconfirm=deletepageconfirm,
                                                                                            addpage=addpage)
        return page(title       = title,
                    body        = body,
                    navtrail    = get_navtrail(ln),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = ln)
    else:
        ## user is not authorised to use WebSubmit Admin:
        return page_not_authorized(req=req, text=auth_msg, navtrail=get_navtrail(ln))

def doctypeconfiguresubmissionfunctionsparameters(req,
                                                  doctype="",
                                                  action="",
                                                  functionname="",
                                                  functionstep="",
                                                  functionscore="",
                                                  paramname="",
                                                  paramval="",
                                                  editfunctionparametervalue="",
                                                  editfunctionparametervaluecommit="",
                                                  editfunctionparameterfile="",
                                                  editfunctionparameterfilecommit="",
                                                  paramfilename="",
                                                  paramfilecontent="",
                                                  ln=CFG_SITE_LANG):
    """Configure the parameters for a function belonging to a given submission.
       @param doctype: (string) the unique ID of a document type
       @param action: (string) the unique ID of an action
       @param functionname: (string) the name of a WebSubmit function
       @param functionstep: (integer) the step at which a WebSubmit function is located
       @param functionscore: (integer) the score (within a step) at which a WebSubmit function is located
       @param paramname: (string) the name of a parameter being edited
       @param paramval: (string) the value to be allocated to a parameter that is being editied
       @param editfunctionparametervalue: (string) a flag to signal that a form should be displayed for editing the value
        of a parameter
       @param editfunctionparametervaluecommit: (string) a flag to signal that a parameter value has been edited and should
        be committed
       @param editfunctionparameterfile: (string) a flag to signal that a form containing a parameter file is to be displayed
       @param editfunctionparameterfilecommit: (string) a flag to signal that a modified parameter file is to be committed
       @param paramfilename: (string) the name of a parameter file
       @param paramfilecontent: (string) the contents of a parameter file
       @param ln: (string) the language code (e.g. en, fr, de, etc); defaults to the default installation language
       @return: (string) HTML-page body
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (auth_code, auth_msg) = check_user(req, 'cfgwebsubmit')
    if not auth_code:
        ## user is authorised to use WebSubmit Admin:
        (title, body) =\
          perform_request_configure_doctype_submissionfunctions_parameters(doctype=doctype,
                                                                           action=action,
                                                                           functionname=functionname,
                                                                           functionstep=functionstep,
                                                                           functionscore=functionscore,
                                                                           paramname=paramname,
                                                                           paramval=paramval,
                                                                           editfunctionparametervalue=editfunctionparametervalue,
                                                                           editfunctionparametervaluecommit=editfunctionparametervaluecommit,
                                                                           editfunctionparameterfile=editfunctionparameterfile,
                                                                           editfunctionparameterfilecommit=editfunctionparameterfilecommit,
                                                                           paramfilename=paramfilename,
                                                                           paramfilecontent=paramfilecontent)
        return page(title       = title,
                    body        = body,
                    navtrail    = get_navtrail(ln),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = ln)
    else:
        ## user is not authorised to use WebSubmit Admin:
        return page_not_authorized(req=req, text=auth_msg, navtrail=get_navtrail(ln))


def doctypeconfiguresubmissionfunctions(req,
                                        doctype="",
                                        action="",
                                        moveupfunctionname="",
                                        moveupfunctionstep="",
                                        moveupfunctionscore="",
                                        movedownfunctionname="",
                                        movedownfunctionstep="",
                                        movedownfunctionscore="",
                                        movefromfunctionname="",
                                        movefromfunctionstep="",
                                        movefromfunctionscore="",
                                        movetofunctionname="",
                                        movetofunctionstep="",
                                        movetofunctionscore="",
                                        deletefunctionname="",
                                        deletefunctionstep="",
                                        deletefunctionscore="",
                                        configuresubmissionaddfunction="",
                                        configuresubmissionaddfunctioncommit="",
                                        addfunctionname="",
                                        addfunctionstep="",
                                        addfunctionscore="",
                                        ln=CFG_SITE_LANG):
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (auth_code, auth_msg) = check_user(req, 'cfgwebsubmit')
    if not auth_code:
        ## user is authorised to use WebSubmit Admin:
        (title, body) = \
                perform_request_configure_doctype_submissionfunctions(doctype=doctype,
                                                                      action=action,
                                                                      moveupfunctionname=moveupfunctionname,
                                                                      moveupfunctionstep=moveupfunctionstep,
                                                                      moveupfunctionscore=moveupfunctionscore,
                                                                      movedownfunctionname=movedownfunctionname,
                                                                      movedownfunctionstep=movedownfunctionstep,
                                                                      movedownfunctionscore=movedownfunctionscore,
                                                                      movefromfunctionname=movefromfunctionname,
                                                                      movefromfunctionstep=movefromfunctionstep,
                                                                      movefromfunctionscore=movefromfunctionscore,
                                                                      movetofunctionname=movetofunctionname,
                                                                      movetofunctionstep=movetofunctionstep,
                                                                      movetofunctionscore=movetofunctionscore,
                                                                      deletefunctionname=deletefunctionname,
                                                                      deletefunctionstep=deletefunctionstep,
                                                                      deletefunctionscore=deletefunctionscore,
                                                                      configuresubmissionaddfunction=configuresubmissionaddfunction,
                                                                      configuresubmissionaddfunctioncommit=configuresubmissionaddfunctioncommit,
                                                                      addfunctionname=addfunctionname,
                                                                      addfunctionstep=addfunctionstep,
                                                                      addfunctionscore=addfunctionscore)

        return page(title       = title,
                    body        = body,
                    navtrail    = get_navtrail(ln),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = ln)
    else:
        ## user is not authorised to use WebSubmit Admin:
        return page_not_authorized(req=req, text=auth_msg, navtrail=get_navtrail(ln))

def doctypeconfigure(req,
                     doctype,
                     doctypename=None,
                     doctypedescr=None,
                     doctypedetailsedit="",
                     doctypedetailscommit="",
                     doctypecategoryadd="",
                     doctypecategoryedit="",
                     doctypecategoryeditcommit="",
                     doctypecategorydelete="",
                     doctypesubmissionadd="",
                     doctypesubmissiondelete="",
                     doctypesubmissiondeleteconfirm="",
                     doctypesubmissionedit="",
                     doctypesubmissionaddclonechosen="",
                     doctypesubmissiondetailscommit="",
                     doctypesubmissionadddetailscommit="",
                     doctypesubmissioneditdetailscommit="",
                     categid=None,
                     categdescr=None,
                     movecategup=None,
                     movecategdown=None,
                     jumpcategout=None,
                     jumpcategin=None,
                     action=None,
                     displayed=None,
                     buttonorder=None,
                     statustext=None,
                     level=None,
                     score=None,
                     stpage=None,
                     endtxt=None,
                     doctype_cloneactionfrom=None,
                     ln=CFG_SITE_LANG):
    """The main entry point to the configuration of a WebSubmit document type and its submission interfaces,
       functions, etc.
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (auth_code, auth_msg) = check_user(req, 'cfgwebsubmit')
    if not auth_code:
        ## user is authorised to use WebSubmit Admin:
        (title, body) = perform_request_configure_doctype(doctype=doctype,
                                                          doctypename=doctypename,
                                                          doctypedescr=doctypedescr,
                                                          doctypedetailsedit=doctypedetailsedit,
                                                          doctypedetailscommit=doctypedetailscommit,
                                                          doctypecategoryadd=doctypecategoryadd,
                                                          doctypecategoryedit=doctypecategoryedit,
                                                          doctypecategoryeditcommit=doctypecategoryeditcommit,
                                                          doctypecategorydelete=doctypecategorydelete,
                                                          doctypesubmissionadd=doctypesubmissionadd,
                                                          doctypesubmissiondelete=doctypesubmissiondelete,
                                                          doctypesubmissiondeleteconfirm=doctypesubmissiondeleteconfirm,
                                                          doctypesubmissionedit=doctypesubmissionedit,
                                                          doctypesubmissionaddclonechosen=doctypesubmissionaddclonechosen,
                                                          doctypesubmissionadddetailscommit=doctypesubmissionadddetailscommit,
                                                          doctypesubmissioneditdetailscommit=doctypesubmissioneditdetailscommit,
                                                          categid=categid,
                                                          categdescr=categdescr,
                                                          movecategup=movecategup,
                                                          movecategdown=movecategdown,
                                                          jumpcategout=jumpcategout,
                                                          jumpcategin=jumpcategin,
                                                          action=action,
                                                          displayed=displayed,
                                                          buttonorder=buttonorder,
                                                          statustext=statustext,
                                                          level=level,
                                                          score=score,
                                                          stpage=stpage,
                                                          endtxt=endtxt,
                                                          doctype_cloneactionfrom=doctype_cloneactionfrom)

        return page(title       = title,
                    body        = body,
                    navtrail    = get_navtrail(ln),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = ln)
    else:
        ## user is not authorised to use WebSubmit Admin:
        return page_not_authorized(req=req, text=auth_msg, navtrail=get_navtrail(ln))


def organisesubmissionpage(req,
                           doctype="",
                           sbmcolid="",
                           catscore="",
                           addsbmcollection="",
                           deletesbmcollection="",
                           addtosbmcollection="",
                           adddoctypes="",
                           movesbmcollectionup="",
                           movesbmcollectiondown="",
                           deletedoctypefromsbmcollection="",
                           movedoctypeupinsbmcollection="",
                           movedoctypedowninsbmcollection="",
                           ln=CFG_SITE_LANG):
    """Entry point for organising the document types on a submission page.
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (auth_code, auth_msg) = check_user(req, 'cfgwebsubmit')
    if not auth_code:
        ## user is authorised to use WebSubmit Admin:
        (title, body) = \
         perform_request_organise_submission_page(doctype=doctype,
                                                  sbmcolid=sbmcolid,
                                                  catscore=catscore,
                                                  addsbmcollection=addsbmcollection,
                                                  deletesbmcollection=deletesbmcollection,
                                                  addtosbmcollection=addtosbmcollection,
                                                  adddoctypes=adddoctypes,
                                                  movesbmcollectionup=movesbmcollectionup,
                                                  movesbmcollectiondown=movesbmcollectiondown,
                                                  deletedoctypefromsbmcollection=deletedoctypefromsbmcollection,
                                                  movedoctypeupinsbmcollection=movedoctypeupinsbmcollection,
                                                  movedoctypedowninsbmcollection=movedoctypedowninsbmcollection)

        return page(title       = title,
                    body        = body,
                    navtrail    = get_navtrail(ln),
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    req         = req,
                    language    = ln)
    else:
        ## user is not authorised to use WebSubmit Admin:
        return page_not_authorized(req=req, text=auth_msg, navtrail=get_navtrail(ln))
