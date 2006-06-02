# -*- coding: utf-8 -*-

__lastupdated__ = """$Date$"""

import sys
from mod_python import apache

from invenio.websubmitadmin_engine import *
from invenio.config import cdslang
from invenio.webuser import getUid
from invenio.webpage import page
from invenio.messages import wash_language, gettext_set_language


def index(req, ln=cdslang):
    """Websubmit Admin home page. Default action: list all WebSubmit document types."""
    
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (body, errors, warnings) = perform_request_list_doctypes()
    return page(title       = "Available WebSubmit Document Types",
                body        = body,
                navtrail    = get_navtrail(ln),
                uid         = uid,
                lastupdated = __lastupdated__,
                req         = req,
                language    = ln,
                errors      = errors,
                warnings    = warnings)


def doctypelist(req, ln=cdslang):
    """List all WebSubmit document types."""
    
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (body, errors, warnings) = perform_request_list_doctypes()
    return page(title       = "Available WebSubmit Document Types",
                body        = body,
                navtrail    = get_navtrail(ln),
                uid         = uid,
                lastupdated = __lastupdated__,
                req         = req,
                language    = ln,
                errors      = errors,
                warnings    = warnings)


def jschecklist(req, ln=cdslang):
    """List all WebSubmit JavaScript Checks (checks can be applied to form elements in WebSubmit.)"""
    
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (body, errors, warnings) = perform_request_list_jschecks()
    return page(title       = "Available WebSubmit Checking Functions",
                body        = body,
                navtrail    = get_navtrail(ln),
                uid         = uid,
                lastupdated = __lastupdated__,
                req         = req,
                language    = ln,
                errors      = errors,
                warnings    = warnings)


def actionlist(req, ln=cdslang):
    """List all WebSubmit actions."""
    
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (body, errors, warnings) = perform_request_list_actions()
    return page(title       = "Available WebSubmit Actions",
                body        = body,
                navtrail    = get_navtrail(ln),
                uid         = uid,
                lastupdated = __lastupdated__,
                req         = req,
                language    = ln,
                errors      = errors,
                warnings    = warnings)


def functionlist(req, ln=cdslang):
    """List all WebSubmit FUNCTIONS (Functions do the work of processing a submission)"""
    
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (body, errors, warnings) = perform_request_list_functions()
    return page(title       = "Available WebSubmit Functions",
                body        = body,
                navtrail    = get_navtrail(ln),
                uid         = uid,
                lastupdated = __lastupdated__,
                req         = req,
                language    = ln,
                errors      = errors,
                warnings    = warnings)


def elementlist(req, ln=cdslang):
    """List all WebSubmit form ELEMENTS (elements are input fields on a WebSubmit form)"""
    
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (body, errors, warnings) = perform_request_list_elements()
    return page(title       = "Available WebSubmit Elements",
                body        = body,
                navtrail    = get_navtrail(ln),
                uid         = uid,
                lastupdated = __lastupdated__,
                req         = req,
                language    = ln,
                errors      = errors,
                warnings    = warnings)


def actionadd(req, actid="", actname="", working_dir="", status_text="", actcommit="", ln=cdslang):
    """Add a new action to the WebSubmit database.
       Web form for action details will be displayed if "actid" and "actname" are empty; else
       new action will be committed to websubmit.
       @param actid: unique id for new action (if empty, Web form will be displayed)
       @param actname: name of new action (if empty, Web form will be displayed)
       @param working_dir: action working directory for WebSubmit
       @param status_text: status text displayed at end of WebSubmit action
       @param ln: language
       @return page
    """

    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    # Generate content
    (title, body, errors, warnings) = perform_request_add_action(actid, actname, working_dir, status_text, actcommit)
    return page(title       = _("%s"%(title,)),
                body        = body,
                navtrail    = get_navtrail(ln),
                uid         = uid,
                lastupdated = __lastupdated__,
                req         = req,
                language    = ln,
                errors      = errors,
                warnings    = warnings)

def actionedit(req, actid, actname="", working_dir="", status_text="", actcommit="", ln=cdslang):
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

    # Generate content
    (title, body, errors, warnings) = perform_request_edit_action(actid, actname, working_dir, status_text, actcommit)
    return page(title       = title,
                body        = body,
                navtrail    = get_navtrail(ln),
                uid         = uid,
                lastupdated = __lastupdated__,
                req         = req,
                language    = ln,
                errors      = errors,
                warnings    = warnings)

def jscheckadd(req, chname="", chdesc="", chcommit="", ln=cdslang):
    """Add a new JavaScript CHECK to the WebSubmit database.
       Web form for action details will be displayed if "actid" and "actname" are empty; else
       new action will be committed to WebSubmit.
       @param chname: unique name/ID for new check (if empty, Web form will be displayed)
       @param chdesc: description of new JS check (the JavaScript code that is the check.) (If empty,
                      Web form will be displayed)
       @param ln: language
       @return page
    """

    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    # Generate content
    (title, body, errors, warnings) = perform_request_add_jscheck(chname, chdesc, chcommit)
    return page(title       = _("%s"%(title,)),
                body        = body,
                navtrail    = get_navtrail(ln),
                uid         = uid,
                lastupdated = __lastupdated__,
                req         = req,
                language    = ln,
                errors      = errors,
                warnings    = warnings)

def jscheckedit(req, chname, chdesc="", chcommit="", ln=cdslang):
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

    # Generate content
    (title, body, errors, warnings) = perform_request_edit_jscheck(chname, chdesc, chcommit)
    return page(title       = title,
                body        = body,
                navtrail    = get_navtrail(ln),
                uid         = uid,
                lastupdated = __lastupdated__,
                req         = req,
                language    = ln,
                errors      = errors,
                warnings    = warnings)


def elementadd(req, elname="", elmarccode="", eltype="", elsize="", elrows="", elcols="", elmaxlength="", \
                elval="", elfidesc="", elmodifytext="", elcookie="", elcommit="", ln=cdslang):
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
       @param elcookie: does the element set a cookie?
       @param elcommit: flag variable used to determine whether to commit element modifications or whether
                        to simply display a form containing element details.
       @param ln: language
       @return page
    """

    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    # Generate content
    (title, body, errors, warnings) = perform_request_add_element(elname, elmarccode, eltype, \
                                                                   elsize, elrows, elcols, elmaxlength, \
                                                                   elval, elfidesc, elmodifytext, \
                                                                   elcookie, elcommit)
    return page(title       = _("%s"%(title,)),
                body        = body,
                navtrail    = get_navtrail(ln),
                uid         = uid,
                lastupdated = __lastupdated__,
                req         = req,
                language    = ln,
                errors      = errors,
                warnings    = warnings)


def elementedit(req, elname, elmarccode="", eltype="", elsize="", elrows="", elcols="", elmaxlength="", \
                elval="", elfidesc="", elmodifytext="", elcookie="", elcommit="", ln=cdslang):
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
       @param elcookie: does the element set a cookie?
       @param elcommit: flag variable used to determine whether to commit element modifications or whether
                        to simply display a form containing element details.
       @param ln: language
       @return page
    """

    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    # Generate content
    (title, body, errors, warnings) = perform_request_edit_element(elname, elmarccode, eltype, \
                                                                   elsize, elrows, elcols, elmaxlength, \
                                                                   elval, elfidesc, elmodifytext, \
                                                                   elcookie, elcommit)
    return page(title       = title,
                body        = body,
                navtrail    = get_navtrail(ln),
                uid         = uid,
                lastupdated = __lastupdated__,
                req         = req,
                language    = ln,
                errors      = errors,
                warnings    = warnings)


def functionadd(req, funcname="", funcdescr="", funcaddcommit="", ln=cdslang):
    """Add a new function to WebSubmit"""
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    # Generate content
    (title, body, errors, warnings) = perform_request_add_function(funcname=funcname,
                                                                   funcdescr=funcdescr,
                                                                   funcaddcommit=funcaddcommit
                                                                  )

    return page(title       = title,
                body        = body,
                navtrail    = get_navtrail(ln),
                uid         = uid,
                lastupdated = __lastupdated__,
                req         = req,
                language    = ln,
                errors      = errors,
                warnings    = warnings)


def functionedit(req, funcname="", funcdescr="", funceditaddparam="", funceditaddparamfree="", \
                 funceditdelparam="", funcdescreditcommit="", funcparamdelcommit="", funcparamaddcommit="", ln=cdslang):
    """Edit a WebSubmit function"""
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    # Generate content
    (title, body, errors, warnings) = perform_request_edit_function(funcname=funcname,
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
                language    = ln,
                errors      = errors,
                warnings    = warnings)


def functionusage(req, funcname, ln=cdslang):
    """View the usage cases (document-type and actions) in which a function is used.
       @param function: the function name
       @param ln: the language
       @return: a web page
    """
    
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (body, errors, warnings) = perform_request_function_usage(funcname)
    return page(title       = "WebSubmit Function Usage",
                body        = body,
                navtrail    = get_navtrail(ln),
                uid         = uid,
                lastupdated = __lastupdated__,
                req         = req,
                language    = ln,
                errors      = errors,
                warnings    = warnings)

def doctyperemove(req, doctype="", doctypedelete="", doctypedeleteconfirm="", ln=cdslang):
    """Delete a WebSubmit document-type.
    @param doctype: the unique id of the document type to be deleted
    @param ln: the interface language
    @return: HTML page.
    """
    
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (title, body, errors, warnings) = perform_request_remove_doctype(doctype=doctype,
                                                                     doctypedelete=doctypedelete,
                                                                     doctypedeleteconfirm=doctypedeleteconfirm)
    return page(title       = title,
                body        = body,
                navtrail    = get_navtrail(ln),
                uid         = uid,
                lastupdated = __lastupdated__,
                req         = req,
                language    = ln,
                errors      = errors,
                warnings    = warnings)

def doctypeadd(req, doctype="", doctypename="", doctypedescr="", clonefrom="", doctypedetailscommit="", ln=cdslang):
    """Add a new document type to WebSubmit"""
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    (title, body, errors, warnings) = perform_request_add_doctype(doctype=doctype,
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
                language    = ln,
                errors      = errors,
                warnings    = warnings)

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
                                        ln=cdslang):
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)
    errors = []
    warnings = []
    (title, body, errors, warnings) = perform_request_configure_doctype_submissionfunctions(doctype=doctype,
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
                                                                                            deletefunctionscore=deletefunctionscore
                                                                                           )

    return page(title       = title,
                body        = body,
                navtrail    = get_navtrail(ln),
                uid         = uid,
                lastupdated = __lastupdated__,
                req         = req,
                language    = ln,
                errors      = errors,
                warnings    = warnings)


def doctypeconfigure(req,
                     doctype,
                     doctypename="",
                     doctypedescr="",
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
                     categid="",
                     categdescr="",
                     action="",
                     displayed="",
                     buttonorder="",
                     statustext="",
                     level="",
                     score="",
                     stpage="",
                     endtxt="",
                     doctype_cloneactionfrom="",
                     ln=cdslang):
    """The main entry point to the configuration of a WebSubmit document type and its submission interfaces,
       functions, etc.
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)
    errors = []
    warnings = []
    (title, body, errors, warnings) = perform_request_configure_doctype(doctype=doctype,
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
                                                                        action=action,
                                                                        displayed=displayed,
                                                                        buttonorder=buttonorder,
                                                                        statustext=statustext,
                                                                        level=level,
                                                                        score=score,
                                                                        stpage=stpage,
                                                                        endtxt=endtxt,
                                                                        doctype_cloneactionfrom=doctype_cloneactionfrom,
                                                                       )

    return page(title       = title,
                body        = body,
                navtrail    = get_navtrail(ln),
                uid         = uid,
                lastupdated = __lastupdated__,
                req         = req,
                language    = ln,
                errors      = errors,
                warnings    = warnings)

