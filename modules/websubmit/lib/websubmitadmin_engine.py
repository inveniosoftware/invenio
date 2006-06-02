# -*- coding: utf-8 -*-

import re
from invenio.websubmitadmin_dblayer import *
from invenio.websubmitadmin_config import *
from invenio.access_control_admin import acc_getAllRoles, acc_getRoleUsers
from invenio.config import cdslang
from invenio.access_control_engine import acc_authorize_action

import invenio.template

try:
    websubmitadmin_templates = invenio.template.load('websubmitadmin')
except:
    pass



## utility functions:

def is_adminuser(uid, role):
    """check if user is a registered administrator. """
    return acc_authorize_action(uid, role)

def check_user(uid, role, adminarea=2, authorized=0):
    (auth_code, auth_message) = is_adminuser(uid, role)
    if not authorized and auth_code != 0:
        return ("false", auth_message)
    return ("", auth_message)

def get_navtrail(ln=cdslang):
    """gets the navtrail for title...
       @param title: title of the page
       @param ln: language
       @return HTML output
    """
    navtrail = websubmitadmin_templates.tmpl_navtrail(ln)
    return navtrail

def stringify_listvars(mylist):
    """Accept a list (or a list of lists) (or tuples).
       Convert each item in the list, into a string (replace None with the empty
       string "").
       @param mylist: A list/tuple of values, or a list/tuple of value list/tuples.
       @return: a tuple of string values or a tuple of string value tuples
    """
    string_list = []
    try:
        if type(mylist[0]) in (tuple,list):
            for row in mylist:
                string_list.append(map(lambda x: x is not None and str(x) or "", row))
        else:
            string_list = map(lambda x: x is not None and str(x) or "", mylist)
    except IndexError:
        pass
    return string_list

## def wash_form_var(var, test_type, force_convert=0, minlen=None, maxlen=None):
##     """Intended to be used to test values submitted to a form, to see whether they
##        meet some criteria, as defined by the "test_type" argument
##        @param svar: the string value to test
##        @param typematch: the type that we want to test our string against - may take
##          a value of:
##          'alphanum' : the value may only contain alphanumeric values and the underscore
##                       (the set [a-zA-Z0-9_])
##          'alpha'    : the value may only contain alphabetical values (the set [a-zA-Z])
##          'digit'    : the value may only contain the integer digits [0-9]
##        @param forcematch: 
##     """
##     out = None
##     var_ok = 1 ## Assume that var is correct type (will reset flag if not)

##     if test_type == 'alphanum':
##         ## Test to see whether
##         pass
##     elif test_type == 'alpha':
##         pass
##     elif test_type == 'digit':
##         pass
##     elif test_type == 'str':
##         pass
##     elif test_type == 'int':
##         pass
##     elif test_type == 'list':
##         pass
##     elif test_type == 'tuple':
##         pass
##     elif test_type == 'dict':
##         pass


    
##     testtypes = ('alphanum', 'alpha', 'digit')
##     if typematch not in testtypes:
##         raise TypeError("Unknown value for typematch")
##     (re.compile(r'\W',re.U)).search
        
## def wash_url_argument(var, new_type):
##     """
##     Wash argument into 'new_type', that can be 'list', 'str', 'int', 'tuple' or 'dict'.
##     If needed, the check 'type(var) is not None' should be done before calling this function
##     @param var: variable value
##     @param new_type: variable type, 'list', 'str', 'int', 'tuple' or 'dict'
##     @return as much as possible, value var as type new_type
##             If var is a list, will change first element into new_type.
##             If int check unsuccessful, returns 0
##     """
##     out = []
##     if new_type == 'list':  # return lst
##         if type(var) is list:
##             out = var
##         else:
##             out = [var]
##     elif new_type == 'str':  # return str
##         if type(var) is list:
##             try:
##                 out = "%s" % var[0]
##             except:
##                 out = ""
##         elif type(var) is str:
##             out = var
##         else:
##             out = "%s" % var
##     elif new_type == 'int': # return int
##         if type(var) is list:
##             try:
##                 out = int(var[0])
##             except:
##                 out = 0
##         elif type(var) is int:
##             out = var
##         elif type(var) is str:
##             try:
##                 out = int(var)
##             except:
##                 out = 0
##         else:
##             out = 0
##     elif new_type == 'tuple': # return tuple
##         if type(var) is tuple:
##             out = var
##         else:
##             out = (var,)
##     elif new_type == 'dict': # return dictionary
##         if type(var) is dict:
##             out = var
##         else:
##             out = {0:var}
##     return out




## Internal Business-Logic functions


## Functions for adding new catalgue to DB:
def _add_new_action(actid,actname,working_dir,status_text):
    """Insert the details of a new action into the websubmit system database.
       @param actid: unique action id (sactname)
       @param actname: action name (lactname)
       @param working_dir: directory action works from (dir)
       @param status_text: text string indicating action status (statustext)
    """
    (actid,actname,working_dir,status_text) = (str(actid).upper(),str(actname),str(working_dir),str(status_text))
    err_code = insert_action_details(actid,actname,working_dir,status_text)
    return err_code


def perform_request_add_function(funcname="", funcdescr="", funcaddcommit=""):
    """(title, body, errors, warnings) = perform_request_add_function(function)"""
    errors = []
    warnings = []
    body = ""
    title = "Create New WebSubmit Function"

    if funcaddcommit != "" and funcaddcommit != None:
        ## Add a new function definition - IF it is not already present
        err_code = insert_function_details(funcname, funcdescr)

        ## Handle error code - redisplay form with warning about no DB commit, or display with options
        ## to edit function:
        if err_code == 0:
            user_msg = """'%s' Function Added to WebSubmit""" % (funcname,)
            body = websubmitadmin_templates.tmpl_display_addfunctionform(funcname=funcname,
                                                                         funcdescr=funcdescr,
                                                                         perform_act="functionedit",
                                                                         user_msg=user_msg
                                                                        )
        else:
            ## Could not commit function to WebSubmit DB - redisplay form with function description:
            user_msg = """Could Not Add '%s' Function to WebSubmit""" % (funcname,)
            body = websubmitadmin_templates.tmpl_display_addfunctionform(funcdescr=funcdescr, user_msg=user_msg)

    else:
        ## Display Web form for new function addition:
        body = websubmitadmin_templates.tmpl_display_addfunctionform(funcdescr=funcdescr)

    return (title, body, errors, warnings)


def perform_request_add_action(actid="",actname="",working_dir="",status_text="", actcommit=""):
    """An interface for the addition of a new WebSubmit action.
       If form fields filled, will insert new action into WebSubmit database, else will display
       web form prompting for action details.
       @param actid:       unique id for new action
       @param actname:     name of new action
       @param working_dir: action working directory for WebSubmit core
       @param status_text: status text displayed at end of action
       @return: tuple containing "title" (title of page), body (page body), errors (list of errors),
                warnings (list of warnings).
    """
    errors = []
    warnings = []
    body = ""
    title = "Create New WebSubmit Action"

    if actcommit != "" and actcommit != None:
        ## Commit new action to WebSubmit DB:
        err_code = _add_new_action(actid,actname,working_dir,status_text)

        ## Handle error code - redisplay form with warning about no DB commit, or move to list
        ## of actions
        if err_code == 0:
            ## Action added: show page listing WebSubmit actions
            user_msg = """'%s' Action Added to WebSubmit""" % (actid,)
            all_actions = get_actid_actname_allactions()
            body = websubmitadmin_templates.tmpl_display_allactions(all_actions,user_msg=user_msg)
            title = "Available WebSubmit Actions"
        else:
            ## Could not commit action to WebSubmit DB redisplay form with completed details and error message
            ## warnings.append(('ERR_WEBSUBMIT_ADMIN_ADDACTIONFAILDUPLICATE',actid) ## TODO
            user_msg = """Could Not Add '%s' Action to WebSubmit""" % (actid,)
            body = websubmitadmin_templates.tmpl_display_addactionform(actid=actid, actname=actname, working_dir=working_dir, status_text=status_text, user_msg=user_msg)
    else:
        ## Display Web form for new action details:
        user_msg = ""
## FIXME - ERROR CHECKING
##         if actname != "":
##             user_msg = """The field "Action Description" is Mandatory"""
        body = websubmitadmin_templates.tmpl_display_addactionform(actid=actid, actname=actname, working_dir=working_dir, status_text=status_text, user_msg=user_msg)
    return (title, body, errors, warnings)

def perform_request_add_jscheck(chname="", chdesc="", chcommit=""):
    """An interface for the addition of a new WebSubmit JavaScript Check, as used on form elements.
       If form fields filled, will insert new Check into WebSubmit database, else will display
       Web form prompting for Check details.
       @param chname:       unique id/name for new Check
       @param chdesc:     description (JavaScript code body) of new Check
       @return: tuple containing "title" (title of page), body (page body), errors (list of errors),
                warnings (list of warnings).
    """
    errors = []
    warnings = []
    body = ""
    title = "Create New WebSubmit Checking Function"

    if chcommit != "" and chcommit != None:
        ## Commit new check to WebSubmit DB:
        err_code = insert_jscheck_details(chname, chdesc)

        ## Handle error code - redisplay form wih warning about no DB commit, or move to list
        ## of checks
        if err_code == 0:
            ## Check added: show page listing WebSubmit JS Checks
            user_msg = """'%s' Checking Function Added to WebSubmit""" % (chname,)
            all_jschecks = get_chname_alljschecks()
            body = websubmitadmin_templates.tmpl_display_alljschecks(all_jschecks, user_msg=user_msg)
            title = "Available WebSubmit Checking Functions"
        else:
            ## Could not commit Check to WebSubmit DB: redisplay form with completed details and error message
            ## TODO : Warning Message
            user_msg = """Could Not Add '%s' Checking Function to WebSubmit""" % (chname,)
            body = websubmitadmin_templates.tmpl_display_addjscheckform(chname=chname, chdesc=chdesc, user_msg=user_msg)
    else:
        ## Display Web form for new check details:
        user_msg = ""
## FIXME - ERROR CHECKING
##         if chdesc != "":
##             user_msg = """The field "Check Name" is Mandatory"""
        body = websubmitadmin_templates.tmpl_display_addjscheckform(chname=chname, chdesc=chdesc, user_msg=user_msg)
    return (title, body, errors, warnings)


def perform_request_add_element(elname="", elmarccode="", eltype="", elsize="", elrows="", \
                                elcols="", elmaxlength="", elval="", elfidesc="", \
                                elmodifytext="", elcookie="", elcommit=""):
    """An interface for adding a new ELEMENT to the WebSubmit DB.
       @param elname: element name.
       @param elmarccode: element's MARC code.
       @param eltype: element type.
       @param elsize: element size.
       @param elrows: number of rows in element.
       @param elcols: number of columns in element.
       @param elmaxlength: maximum length of element
       @param elval: default value of element
       @param elfidesc: description of element
       @param elmodifytext: modification text of element
       @param elcookie: does the element set a cookie?
       @param elcommit: If this value is not empty, attempt to commit element details to WebSubmit DB
       @return: tuple containing "title" (title of page), body (page body), errors (list of errors),
                warnings (list of warnings).
    """
    errors = []
    warnings = []
    body = ""
    title = "Create New WebSubmit Element"
    if elcommit != "" and elcommit != None:
        ## Commit new element description to WebSubmit DB:
        ## First, wash and check arguments:
        
        err_code = insert_element_details(elname=elname, elmarccode=elmarccode, eltype=eltype, \
                                          elsize=elsize, elrows=elrows, elcols=elcols, \
                                          elmaxlength=elmaxlength, elval=elval, elfidesc=elfidesc, \
                                          elmodifytext=elmodifytext, elcookie=elcookie)
        if err_code == 0:
            ## Element added: show page listing WebSubmit elements
            user_msg = """'%s' Element Added to WebSubmit""" % (elname,)
            title = "Available WebSubmit Elements"
            all_elements = get_elename_allelements()
            body = websubmitadmin_templates.tmpl_display_allelements(all_elements, user_msg=user_msg)
        else:
            ## Could not commit element to WebSubmit DB: redisplay form with completed details and error message
            ## TODO : Warning Message
            user_msg = """Could Not Add '%s' Element to WebSubmit""" % (elname,)
            body = websubmitadmin_templates.tmpl_display_addelementform(elname=elname,
                                                                        elmarccode=elmarccode,
                                                                        eltype=eltype,
                                                                        elsize=elsize,
                                                                        elrows=elrows,
                                                                        elcols=elcols,
                                                                        elmaxlength=elmaxlength,
                                                                        elval=elval,
                                                                        elfidesc=elfidesc,
                                                                        elmodifytext=elmodifytext,
                                                                        elcookie=elcookie,
                                                                        user_msg=user_msg,
                                                                       )
    else:
        ## Display Web form for new element details:
        user_msg = ""
        body = websubmitadmin_templates.tmpl_display_addelementform(elname=elname,
                                                                    elmarccode=elmarccode,
                                                                    eltype=eltype,
                                                                    elsize=elsize,
                                                                    elrows=elrows,
                                                                    elcols=elcols,
                                                                    elmaxlength=elmaxlength,
                                                                    elval=elval,
                                                                    elfidesc=elfidesc,
                                                                    elmodifytext=elmodifytext,
                                                                    elcookie=elcookie,
                                                                    user_msg=user_msg,
                                                                   )
    return (title, body, errors, warnings)
        

def perform_request_edit_element(elname, elmarccode="", eltype="", elsize="", \
                                 elrows="", elcols="", elmaxlength="", elval="", \
                                 elfidesc="", elmodifytext="", elcookie="", elcommit=""):
    """An interface for the editing and updating the details of a WebSubmit ELEMENT.
       @param elname: element name.
       @param elmarccode: element's MARC code.
       @param eltype: element type.
       @param elsize: element size.
       @param elrows: number of rows in element.
       @param elcols: number of columns in element.
       @param elmaxlength: maximum length of element
       @param elval: default value of element
       @param elfidesc: description of element
       @param elmodifytext: modification text of element
       @param elcookie: does the element set a cookie?
       @param elcommit: If this value is not empty, attempt to commit element details to WebSubmit DB
       @return: tuple containing "title" (title of page), body (page body), errors (list of errors),
                warnings (list of warnings).
    """
    errors = []
    warnings = []
    body = ""
    title = "Edit WebSubmit Element"
    if elcommit != "" and elcommit != None:
        ## Commit updated element description to WebSubmit DB:
        err_code = update_element_details(elname=elname, elmarccode=elmarccode, eltype=eltype, \
                                          elsize=elsize, elrows=elrows, elcols=elcols, \
                                          elmaxlength=elmaxlength, elval=elval, elfidesc=elfidesc, \
                                          elmodifytext=elmodifytext, elcookie=elcookie)
        if err_code == 0:
            ## Element Updated: Show All Element Details Again
            user_msg = """'%s' Element Updated""" % (elname,)
            ## Get submission page usage of element:
            el_use = get_subname_pagenb_element_use(elname)
            element_dets = get_element_details(elname)
            element_dets = stringify_listvars(element_dets)
            ## Take elements from results tuple:
            (elmarccode, eltype, elsize, elrows, elcols, elmaxlength, \
             elval, elfidesc, elcd, elmd, elmodifytext, elcookie) = \
               (element_dets[0][0], element_dets[0][1], element_dets[0][2], element_dets[0][3], \
                element_dets[0][4], element_dets[0][5], element_dets[0][6], element_dets[0][7], \
                element_dets[0][8], element_dets[0][9], element_dets[0][10], element_dets[0][11])
            ## Pass to template:
            body = websubmitadmin_templates.tmpl_display_addelementform(elname=elname,
                                                                        elmarccode=elmarccode,
                                                                        eltype=eltype,
                                                                        elsize=elsize,
                                                                        elrows=elrows,
                                                                        elcols=elcols,
                                                                        elmaxlength=elmaxlength,
                                                                        elval=elval,
                                                                        elfidesc=elfidesc,
                                                                        elcd=elcd,
                                                                        elmd=elmd,
                                                                        elmodifytext=elmodifytext,
                                                                        elcookie=elcookie,
                                                                        perform_act="elementedit",
                                                                        user_msg=user_msg,
                                                                        el_use_tuple=el_use
                                                                       )
        else:
            ## Could Not Update Element: Maybe Key Violation, or Invalid elname? Redisplay all Checks.
            ## TODO : LOGGING
            all_elements = get_elename_allelements()
            user_msg = """Could Not Update Element '%s'""" % (elname,)
            title = "Available WebSubmit Elements"
            body = websubmitadmin_templates.tmpl_display_allelements(all_elements, user_msg=user_msg)
    else:
        ## Display Web form containing existing details of element:
        element_dets = get_element_details(elname)
        ## Get submission page usage of element:
        el_use = get_subname_pagenb_element_use(elname)
        num_rows_ret = len(element_dets)
        element_dets = stringify_listvars(element_dets)
        if num_rows_ret == 1:
            ## Display Element details
            ## Take elements from results tuple:
            (elmarccode, eltype, elsize, elrows, elcols, elmaxlength, \
             elval, elfidesc, elcd, elmd, elmodifytext, elcookie) = \
               (element_dets[0][0], element_dets[0][1], element_dets[0][2], element_dets[0][3], \
                element_dets[0][4], element_dets[0][5], element_dets[0][6], element_dets[0][7], \
                element_dets[0][8], element_dets[0][9], element_dets[0][10], element_dets[0][11])
            ## Pass to template:
            body = websubmitadmin_templates.tmpl_display_addelementform(elname=elname,
                                                                        elmarccode=elmarccode,
                                                                        eltype=eltype,
                                                                        elsize=elsize,
                                                                        elrows=elrows,
                                                                        elcols=elcols,
                                                                        elmaxlength=elmaxlength,
                                                                        elval=elval,
                                                                        elfidesc=elfidesc,
                                                                        elcd=elcd,
                                                                        elmd=elmd,
                                                                        elmodifytext=elmodifytext,
                                                                        elcookie=elcookie,
                                                                        perform_act="elementedit",
                                                                        el_use_tuple=el_use
                                                                       )
        else:
            ## Either no rows, or more than one row for ELEMENT: log error, and display all Elements
            ## TODO : LOGGING
            title = "Available WebSubmit Elements"
            all_elements = get_elename_allelements()
            if num_rows_ret > 1:
                ## Key Error - duplicated elname
                user_msg = """Found Several Rows for Element with Name '%s' - Inform Administrator""" % (elname,)
                ## LOG MESSAGE
            else:
                ## No rows for ELEMENT
                user_msg = """Could Not Find Any Rows for Element with Name '%s'""" % (elname,)
                ## LOG MESSAGE
            body = websubmitadmin_templates.tmpl_display_allelements(all_elements, user_msg=user_msg)
    return (title, body, errors, warnings)


def perform_request_edit_jscheck(chname, chdesc="", chcommit=""):
    """Interface for editing and updating the details of a WebSubmit Check.
       If only "chname" provided, will display the details of a Check in a Web form.
       If "chdesc" not empty, will assume that this is a call to commit update to Check details.
       @param chname: unique id for Check
       @param chdesc: modified value for WebSubmit Check description (code body) - (presence invokes update)
       @return: tuple containing "title" (title of page), body (page body), errors (list of errors),
                warnings (list of warnings).
    """
    errors = []
    warnings = []
    body = ""
    title = "Edit WebSubmit Checking Function"
    (chname, chdesc) = (str(chname), str(chdesc))

## FIXME - ERROR CHECKING
    if chcommit != "" and chcommit != None:
        ## Commit updated Check details to WebSubmit DB:
        err_code = update_jscheck_details(chname, chdesc)
        if err_code == 0:
            ## Check Updated: Show All Check Details Again
            user_msg = """'%s' Check Updated""" % (chname,)
            jscheck_dets = get_jscheck_details(chname)
            body = websubmitadmin_templates.tmpl_display_addjscheckform(chname=jscheck_dets[0][0],
                                                                        chdesc=jscheck_dets[0][1],
                                                                        perform_act="jscheckedit",
                                                                        cd=jscheck_dets[0][2],
                                                                        md=jscheck_dets[0][3],
                                                                        user_msg=user_msg
                                                                       )
        else:
            ## Could Not Update Check: Maybe Key Violation, or Invalid chname? Redisplay all Checks.
            ## TODO : LOGGING
            all_jschecks = get_chname_alljschecks()
            user_msg = """Could Not Update Checking Function '%s'""" % (chname,)
            body = websubmitadmin_templates.tmpl_display_alljschecks(all_jschecks, user_msg=user_msg)
            title = "Available WebSubmit Checking Functions"
    else:
        ## Display Web form containing existing details of Check:
        jscheck_dets = get_jscheck_details(chname)
        num_rows_ret = len(jscheck_dets)
        if num_rows_ret == 1:
            ## Display Check details
            body = websubmitadmin_templates.tmpl_display_addjscheckform(chname=jscheck_dets[0][0],
                                                                        chdesc=jscheck_dets[0][1],
                                                                        perform_act="jscheckedit",
                                                                        cd=jscheck_dets[0][2],
                                                                        md=jscheck_dets[0][3]
                                                                       )
        else:
            ## Either no rows, or more than one row for Check: log error, and display all Checks
            ## TODO : LOGGING
            title = "Available WebSubmit Checking Functions"
            all_jschecks = get_chname_alljschecks()
            if num_rows_ret > 1:
                ## Key Error - duplicated chname
                user_msg = """Found Several Rows for Checking Function with Name '%s' - Inform Administrator""" % (chname,)
                ## LOG MESSAGE
            else:
                ## No rows for action
                user_msg = """Could Not Find Any Rows for Checking Function with Name '%s'""" % (chname,)
                ## LOG MESSAGE
            body = websubmitadmin_templates.tmpl_display_alljschecks(all_jschecks, user_msg=user_msg)
    return (title, body, errors, warnings)


def perform_request_edit_action(actid, actname="", working_dir="", status_text="", actcommit=""):
    """Interface for editing and updating the details of a WebSubmit action.
       If only "actid" provided, will display the details of an action in a Web form.
       If "actname" not empty, will assume that this is a call to commit update to action details.
       @param actid: unique id for action
       @param actname: modified value for WebSubmit action name/description (presence invokes update)
       @param working_dir: modified value for WebSubmit action working_dir
       @param status_text: modified value for WebSubmit action status text
       @return: tuple containing "title" (title of page), body (page body), errors (list of errors),
                warnings (list of warnings).
    """
    errors = []
    warnings = []
    body = ""
    title = "Edit WebSubmit Action"
    (actid, actname, working_dir, status_text) = (str(actid).upper(), str(actname), str(working_dir), str(status_text))

## FIXME - ERROR CHECKING
    if actcommit != "" and actcommit != None:
        ## Commit updated action details to WebSubmit DB:
        err_code = update_action_details(actid, actname, working_dir, status_text)
        if err_code == 0:
            ## Action Updated: Show Action Details Again
            user_msg = """'%s' Action Updated""" % (actid,)
            action_dets = get_action_details(actid)
            body = websubmitadmin_templates.tmpl_display_addactionform(actid=action_dets[0][0],
                                                                       actname=action_dets[0][1],
                                                                       working_dir=action_dets[0][2],
                                                                       status_text=action_dets[0][3],
                                                                       perform_act="actionedit",
                                                                       cd=action_dets[0][4],
                                                                       md=action_dets[0][5],
                                                                       user_msg=user_msg
                                                                      )
        else:
            ## Could Not Update Action: Maybe Key Violation, or Invalid actid? Redisplay all actions.
            ## TODO : LOGGING
            all_actions = get_actid_actname_allactions()
            user_msg = """Could Not Update Action '%s'""" % (actid,)
            body = websubmitadmin_templates.tmpl_display_allactions(all_actions, user_msg=user_msg)
            title = "Available WebSubmit Actions"
    else:
        ## Display Web form containing existing details of action:
        action_dets = get_action_details(actid)
        num_rows_ret = len(action_dets)
        if num_rows_ret == 1:
            ## Display action details
            body = websubmitadmin_templates.tmpl_display_addactionform(actid=action_dets[0][0],
                                                                       actname=action_dets[0][1],
                                                                       working_dir=action_dets[0][2],
                                                                       status_text=action_dets[0][3],
                                                                       perform_act="actionedit",
                                                                       cd=action_dets[0][4],
                                                                       md=action_dets[0][5]
                                                                       )
        else:
            ## Either no rows, or more than one row for action: log error, and display all actions
            ## TODO : LOGGING
            title = "Available WebSubmit Actions"
            all_actions = get_actid_actname_allactions()
            if num_rows_ret > 1:
                ## Key Error - duplicated actid
                user_msg = """Found Several Rows for Action with ID '%s' - Inform Administrator""" % (actid,)
                ## LOG MESSAGE
            else:
                ## No rows for action
                user_msg = """Could Not Find Any Rows for Action with ID '%s'""" % (actid,)
                ## LOG MESSAGE
            body = websubmitadmin_templates.tmpl_display_allactions(all_actions, user_msg=user_msg)
    return (title, body, errors, warnings)


def _functionedit_display_function_details(errors, warnings, funcname, user_msg=""):
    """Display the details of a function, along with any message to the user that may have been provided.
       @param errors: LIST of errors (passed by reference from caller) - errors will be appended to it
       @param warnings: LIST of warnings (passed by reference from caller) - warnings will be appended to it
       @param funcname: unique name of function to be updated
       @param user_msg: Any message to the user that is to be displayed on the page.
       @return: tuple containing (page title, HTML page body).
    """
    title = "Edit WebSubmit Function"
    func_descr_res = get_function_description(function=funcname)
    num_rows_ret = len(func_descr_res)
    if num_rows_ret == 1:
        ## Display action details
        funcdescr = func_descr_res[0][0]
        if funcdescr is None:
            funcdescr = ""
        ## get parameters for this function:
        this_function_parameters = get_function_parameters(function=funcname)
        ## get all function parameters in WebSubmit:
        all_function_parameters = get_distinct_paramname_all_websubmit_function_parameters()
        body = websubmitadmin_templates.tmpl_display_addfunctionform(funcname=funcname,
                                                                     funcdescr=funcdescr,
                                                                     func_parameters=this_function_parameters,
                                                                     all_websubmit_func_parameters=all_function_parameters,
                                                                     perform_act="functionedit",
                                                                     user_msg=user_msg
                                                                    )
    else:
        ## Either no rows, or more than one row for function: log error, and display all functions
        ## TODO : LOGGING
        if user_msg != "":
            ## display the intended message, followed by the new error message
            user_msg += """<br />\n"""
        title = "Available WebSubmit Functions"
        all_functions = get_funcname_funcdesc_allfunctions()
        if num_rows_ret > 1:
            ## Key Error - duplicated function name
            user_msg += """Found Several Rows for Function with Name '%s' - Inform Administrator""" % (funcname,)
            ## LOG MESSAGE
        else:
            ## No rows for function
            user_msg += """Could Not Find Any Rows for Function with Name '%s'""" % (funcname,)
            ## LOG MESSAGE
        body = websubmitadmin_templates.tmpl_display_allfunctions(all_functions, user_msg=user_msg)
    return (title, body)


def _functionedit_update_description(errors, warnings, funcname, funcdescr):
    """Perform an update of the description for a given function.
       @param errors: LIST of errors (passed by reference from caller) - errors will be appended to it
       @param warnings: LIST of warnings (passed by reference from caller) - warnings will be appended to it
       @param funcname: unique name of function to be updated
       @param funcdescr: description to be updated for funcname
       @return: a tuple containing (page title, HTML body content)
    """
    err_code = update_function_description(funcname, funcdescr)
    if err_code == 0:
        ## Function updated - redisplay
        user_msg = """'%s' Function Description Updated""" % (funcname,)
    else:
        ## Could not update function description
## TODO : ERROR LIBS
        user_msg = """Could Not Update Description for Function '%s'""" % (funcname,)
    ## Display function details
    (title, body) = _functionedit_display_function_details(errors=errors, warnings=warnings, funcname=funcname, user_msg=user_msg)
    return (title, body)


def _functionedit_delete_parameter(errors, warnings, funcname, deleteparam):
    """Delete a parameter from a given function.
       Important: if any document types have been using the function from which this parameter will be deleted,
        and therefore have values for this parameter, these values will not be deleted from the WebSubmit DB.
        The deleted parameter therefore may continue to exist in the WebSubmit DB, but will be disassociated
        from this function.
       @param errors: LIST of errors (passed by reference from caller) - errors will be appended to it
       @param warnings: LIST of warnings (passed by reference from caller) - warnings will be appended to it
       @param funcname: unique name of the function from which the parameter is to be deleted.
       @param deleteparam: the name of the parameter to be deleted from the function.
       @return: tuple containing (title, HTML body content)
    """
    err_code = delete_function_parameter(function=funcname, parameter_name=deleteparam)
    if err_code == 0:
        ## Parameter deleted - redisplay function details
        user_msg = """'%s' Parameter Deleted from '%s' Function""" % (deleteparam, funcname)
    else:
        ## could not delete param - it does not exist for this function
## TODO : ERROR LIBS
        user_msg = """'%s' Parameter Does not Seem to Exist for Function '%s' - Could not Delete""" \
                   % (deleteparam, funcname)
    ## Display function details
    (title, body) = _functionedit_display_function_details(errors=errors, warnings=warnings, funcname=funcname, user_msg=user_msg)
    return (title, body)


def _functionedit_add_parameter(errors, warnings, funcname, funceditaddparam="", funceditaddparamfree=""):
    """Add (connect) a parameter to a given WebSubmit function.
       @param errors: LIST of errors (passed by reference from caller) - errors will be appended to it
       @param warnings: LIST of warnings (passed by reference from caller) - warnings will be appended to it
       @param funcname: unique name of the function to which the parameter is to be added.
       @param funceditaddparam: the value of a HTML select list: if present, will contain the name of the
        parameter to be added to the function.  May also be empty - the user may have used the free-text field
        (funceditaddparamfree) to manually enter the name of a parameter.  The important thing is that one
        must be present for the parameter to be added sucessfully.
       @param funceditaddparamfree: The name of the parameter to be added to the function, as taken from a free-
        text HTML input field. May also be empty - the user may have used the HTML select-list (funceditaddparam)
        field to choose the parameter.  The important thing is that one must be present for the parameter to be
        added sucessfully.  The value "funceditaddparamfree" value will take priority over the "funceditaddparam"
        list value.
       @return: tuple containing (title, HTML body content)
    """
    if funceditaddparam in ("", None, "NO_VALUE") and funceditaddparamfree in ("", None):
        ## no parameter chosen
## TODO : ERROR LIBS
        user_msg = """Unable to Find the Parameter to be Added to Function '%s' - Could not Add""" % (funcname,)
    else:
        add_parameter = ""
        if funceditaddparam not in ("", None) and funceditaddparamfree not in ("", None):
            ## both select box and free-text values provided for parameter - prefer free-text
            add_parameter = funceditaddparamfree
        elif funceditaddparam not in ("", None):
            ## take add select-box chosen parameter
            add_parameter = funceditaddparam
        else:
            ## take add free-text chosen parameter
            add_parameter = funceditaddparamfree
        ## attempt to commit parameter:
        err_code = add_function_parameter(function=funcname, parameter_name=add_parameter)
        if err_code == 0:
            ## Parameter added - redisplay function details
            user_msg = """'%s' Parameter Added to '%s' Function""" % (add_parameter, funcname)
        else:
            ## could not add param - perhaps it already exists for this function
## TODO : ERROR LIBS
            user_msg = """Could not Add '%s' Parameter to Function '%s' - It Already Exists for this Function""" \
                       % (add_parameter, funcname)
    ## Display function details
    (title, body) = _functionedit_display_function_details(errors=errors, warnings=warnings, funcname=funcname, user_msg=user_msg)
    return (title, body)


def perform_request_edit_function(funcname, funcdescr="", funceditaddparam="", funceditaddparamfree="",
                                  funceditdelparam="", funcdescreditcommit="", funcparamdelcommit="",
                                  funcparamaddcommit=""):
    """Edit a WebSubmit function. 3 possibilities: edit the function description; delete a parameter from the
        function; add a new parameter to the function.
        @param funcname: the name of the function to be modified
        @param funcdescr: the new function description
        @param funceditaddparam: the name of the parameter to be added to the function (taken from HTML SELECT-list)
        @param funceditaddparamfree: the name of the parameter to be added to the function (taken from free-text input)
        @param funceditdelparam: the name of the parameter to be deleted from the function
        @param funcdescreditcommit: a flag to indicate that this request is to update the description of a function
        @param funcparamdelcommit: a flag to indicate that this request is to delete a parameter from a function
        @param funcparamaddcommit: a flag to indicate that this request is to add a new parameter to a function
        @return: tuple containing (page title, HTML page body, list of errors encountered, list of warnings)
    """
    errors = []
    warnings = []
    body = ""
    title = "Edit WebSubmit Function"
    if funcdescreditcommit != "" and funcdescreditcommit != None:
        ## Update the definition of a function:
        (title, body) = _functionedit_update_description(errors=errors, warnings=warnings, funcname=funcname, funcdescr=funcdescr)
    elif funcparamaddcommit != "" and funcparamaddcommit != None:
        ## Request to add a new parameter to a function
        (title, body) = _functionedit_add_parameter(errors=errors, warnings=warnings, funcname=funcname,
                                                    funceditaddparam=funceditaddparam, funceditaddparamfree=funceditaddparamfree)
    elif funcparamdelcommit != "" and funcparamdelcommit != None:
        ## Request to delete a parameter from a function
        (title, body) = _functionedit_delete_parameter(errors=errors, warnings=warnings, funcname=funcname, deleteparam=funceditdelparam)
    else:
        ## Display Web form for new function addition:
        (title, body) = _functionedit_display_function_details(errors=errors, warnings=warnings, funcname=funcname)
    return (title, body, errors, warnings)


def perform_request_function_usage(funcname):
    """Display a page containing the usage details of a given function.
       @param function: the function name
       @return: page body
    """
    errors = []
    warnings = []
    body = ""
    func_usage = get_doctype_docnam_actid_actnam_fstep_fscore_function(funcname)
    func_usage = stringify_listvars(func_usage)
    body = websubmitadmin_templates.tmpl_display_function_usage(funcname, func_usage)
    return (body, errors, warnings)


def perform_request_list_actions():
    """Display a list of all WebSubmit actions.
       @return: tuple: (body,errors,warnings), where errors and warnings are lists of errors/warnings
         encountered along the way, and body is a string of HTML, which is a page body.
    """
    errors = []
    warnings = []
    body = ""
    all_actions = get_actid_actname_allactions()
    body = websubmitadmin_templates.tmpl_display_allactions(all_actions)
    return (body, errors, warnings)

def perform_request_list_doctypes():
    """Display a list of all WebSubmit document types.
       @return: tuple:(body,errors,warnings), where errors and warnings are lists of errors/warnings
         encountered along the way, and body is a string of HTML, which is a page body.
    """
    errors = []
    warnings = []
    body = ""
    all_doctypes = get_docid_docname_alldoctypes()
    body = websubmitadmin_templates.tmpl_display_alldoctypes(all_doctypes)
    return (body, errors, warnings)

def perform_request_list_jschecks():
    """Display a list of all WebSubmit JavaScript element checking functions.
       @return: tuple:(body,errors,warnings), where errors and warnings are lists of errors/warnings
         encountered along the way, and body is a string of HTML, which is a page body.
    """
    errors = []
    warnings = []
    body = ""
    all_jschecks = get_chname_alljschecks()
    body = websubmitadmin_templates.tmpl_display_alljschecks(all_jschecks)
    return (body, errors, warnings)

def perform_request_list_functions():
    """Display a list of all WebSubmit FUNCTIONS.
       @return: tuple:(body,errors,warnings), where errors and warnings are lists of errors/warnings
         encountered along the way, and body is a string of HTML, which is a page body.
    """
    errors = []
    warnings = []
    body = ""
    all_functions = get_funcname_funcdesc_allfunctions()
    body = websubmitadmin_templates.tmpl_display_allfunctions(all_functions)
    return (body, errors, warnings)

def perform_request_list_elements():
    """Display a list of all WebSubmit ELEMENTS.
       @return: tuple:(body,errors,warnings), where errors and warnings are lists of errors/warnings
         encountered along the way, and body is a string of HTML, which is a page body.
    """
    errors = []
    warnings = []
    body = ""
    all_elements = get_elename_allelements()
    body = websubmitadmin_templates.tmpl_display_allelements(all_elements)
    return (body, errors, warnings)

def _remove_doctype(errors, warnings, doctype):
    """Process removal of a document type.
       @param errors: LIST of errors (passed by reference from caller) - errors will be appended to it
       @param warnings: LIST of warnings (passed by reference from caller) - warnings will be appended to it
       @param doctype: the document type to be removed.
       @return: a tuple containing page title, and HTML page body)
    """
    title = ""
    body = ""
    user_msg = []
    numrows_doctype = get_number_doctypes_docid(docid=doctype)
    if numrows_doctype == 1:
        ## Doctype is unique and can therefore be deleted:
        ## Delete any function parameters for this document type:
        error_code = delete_all_parameters_doctype(doctype=doctype)
        if error_code != 0:
            ## problem deleting some or all parameters - inform user and log error
            ## TODO : ERROR LOGGING
            user_msg.append("""Unable to delete some or all function parameter values for document type "%s".""" % (doctype,))
        ## delete all functions called by this doctype's actions
        error_code = delete_all_functions_doctype(doctype=doctype)
        if error_code != 0:
            ## problem deleting some or all functions - inform user and log error
            ## TODO : ERROR LOGGING
            user_msg.append("""Unable to delete some or all functions for document type "%s".""" % (doctype,))
        ## delete all categories of this doctype
        error_code = delete_all_categories_doctype(doctype=doctype)
        if error_code != 0:
            ## problem deleting some or all categories - inform user and log error
            ## TODO : ERROR LOGGING
            user_msg.append("""Unable to delete some or all parameters for document type "%s".""" % (doctype,))
        ## delete all submission interface fields for this doctype
        error_code = delete_all_submissionfields_doctype(doctype=doctype)
        if error_code != 0:
            ## problem deleting some or all submission fields - inform user and log error
            ## TODO : ERROR LOGGING
            user_msg.append("""Unable to delete some or all submission fields for document type "%s".""" % (doctype,))
        ## delete all submissions for this doctype
        error_code = delete_all_submissions_doctype(doctype)
        if error_code != 0:
            ## problem deleting some or all submissions - inform user and log error
            ## TODO : ERROR LOGGING
            user_msg.append("""Unable to delete some or all submissions for document type "%s".""" % (doctype,))
        ## delete entry for this doctype in the collection-doctypes table
        error_code = delete_collection_doctype_entry_doctype(doctype)
        if error_code != 0:
            ## problem deleting this doctype from the collection-doctypes table
            ## TODO : ERROR LOGGING
            user_msg.append("""Unable to delete document type "%s" from the collection-doctypes table.""" % (doctype,))
        ## delete the doctype itself
        error_code = delete_doctype(doctype)
        if error_code != 0:
            ## problem deleting this doctype from the doctypes table
            ## TODO : ERROR LOGGING
            user_msg.append("""Unable to delete document type "%s" from the document types table.""" % (doctype,))
        user_msg.append("""The "%s" document type should now have been deleted, but you should not ignore any warnings.""" % (doctype,))
        title = """Available WebSubmit Document Types"""
        all_doctypes = get_docid_docname_alldoctypes()
        body = websubmitadmin_templates.tmpl_display_alldoctypes(doctypes=all_doctypes, user_msg=user_msg)
    else:
        ## doctype is not unique and cannot be deleted
        if numrows_doctype > 1:
            ## doctype is duplicated - cannot delete - needs admin intervention
            ## TODO : LOG ERROR
            user_msg.append("""%s WebSubmit document types have been identified for doctype id "%s" - unable to delete.""" \
                       """ Please inform administrator.""" % (numrows_doctype, doctype))
        else:
            ## no document types found for this doctype id
            ## TODO : LOG ERROR
            user_msg.append("""Unable to find any document types in the WebSubmit database for doctype id "%s" - unable to delete""" \
                       % (doctype,))
        ## get a list of all document types, and once more display the delete form, with the message
        alldoctypes = get_docid_docname_and_docid_alldoctypes()
        title = "Remove WebSubmit Doctument Type"
        body = websubmitadmin_templates.tmpl_display_delete_doctype_form(doctype="", alldoctypes=alldoctypes, user_msg=user_msg)
    return (title, body)

def perform_request_remove_doctype(doctype="", doctypedelete="", doctypedeleteconfirm=""):
    """Remove a document type from WebSubmit.
       @param doctype: the document type to be removed
       @doctypedelete: flag to signal that a confirmation for deletion should be displayed
       @doctypedeleteconfirm: flag to signal that confirmation for deletion has been received and
        the doctype should be removed
       @return: a tuple (title, body, errors, warnings)
    """
    errors = []
    warnings = []
    body = ""
    title = "Remove WebSubmit Document Type"
    if doctypedeleteconfirm not in ("", None):
        ## Delete the document type:
        (title, body) = _remove_doctype(errors=errors, warnings=warnings, doctype=doctype)
    else:
        ## Display "doctype delete form"
        if doctypedelete not in ("", None) and doctype not in ("", None):
            ## don't bother to get list of doctypes - user will be prompted to confirm the deletion of "doctype"
            alldoctypes = None
        else:
            ## get list of all doctypes to pass to template so that it can prompt the user to choose a doctype to delete
            ## alldoctypes = get_docid_docname_alldoctypes()
            alldoctypes = get_docid_docname_and_docid_alldoctypes()
        body = websubmitadmin_templates.tmpl_display_delete_doctype_form(doctype=doctype, alldoctypes=alldoctypes)
    return (title, body, errors, warnings)

def _create_add_doctype_form(doctype="", doctypename="", doctypedescr="", clonefrom="", user_msg=""):
    """Perform the steps necessary to create the "add a new doctype" form.
       @param doctype: The unique ID that is to be used for the new doctype.
       @param doctypename: the name that is to be given to a doctype.
       @param doctypedescr: the description to be allocated to the new doctype.
       @param user_msg: any message to be displayed to the user.
       @return: a tuple containing page title and HTML body of page: (title, body)
    """
    title = """Add New WebSubmit Document Type"""
    alldoctypes = get_docid_docname_and_docid_alldoctypes()
    body = websubmitadmin_templates.tmpl_display_doctypedetails_form(doctype=doctype,
                                                                 doctypename=doctypename,
                                                                 doctypedescr=doctypedescr,
                                                                 clonefrom=clonefrom,
                                                                 alldoctypes=alldoctypes,
                                                                 user_msg=user_msg
                                                                )
    return (title, body)

def _clone_categories_doctype(errors, warnings, user_msg, fromdoctype, todoctype):
    """Clone the categories of one document type, to another document type.
       @param errors: a list of errors encountered while cloning categories
       @param warnings: a list of warnings encountered while cloning categories
       @param user_msg: any message to be displayed to the user (this is a list)
       @param fromdoctype: the doctype from which categories are to be cloned
       @param todoctype: the doctype into which categories are to be cloned
       @return: integer value (0/1/2) - if doctype's categories couldn't be deleted, return 0 (cloning failed);
        if some categories could be cloned, return 1 (cloning partially successful); if all categories could be
        cloned, return 2 (cloning successful).
    """
    error_code = clone_categories_fromdoctype_todoctype(fromdoctype=fromdoctype, todoctype=todoctype)
    if error_code == 1:
        ## doctype had existing categories and they could not be deleted
        ## TODO : LOG ERRORS
        user_msg.append("""Categories already existed for the document type "%s" but could not be deleted. Unable to clone""" \
                           """ categories of doctype "%s".""" % (todoctype, fromdoctype))
        return 1  ## cloning failed
    elif error_code == 2:
        ## could not clone all categories for new doctype
        ## TODO : LOG ERRORS
        user_msg.append("""Unable to clone all categories from doctype "%s", for doctype "%s".""" % (fromdoctype, todoctype))
        return 2  ## cloning at least partially successful
    else:
        return 0  ## cloning successful

def _clone_functions_foraction_doctype(errors, warnings, user_msg, fromdoctype, todoctype, action):
    """Clone the functions of a given action of one document type, to the same action on another document type.
       @param errors: a list of errors encountered while cloning functions
       @param warnings: a list of warnings encountered while cloning functions
       @param user_msg: any message to be displayed to the user (this is a list)
       @param fromdoctype: the doctype from which functions are to be cloned
       @param todoctype: the doctype into which functions are to be cloned
       @param action: the action for which functions are to be cloned
       @return: an integer value (0/1/2). In the case that todoctype had existing functions for the given action and
        they could not be deleted return 0, signalling that this is a serious problem; in the case that some
        functions were cloned, return 1; in the case that all functions were cloned, return 2.
    """
    error_code = clone_functions_foraction_fromdoctype_todoctype(fromdoctype=fromdoctype, todoctype=todoctype, action=action)
    if error_code == 1:
        ## doctype had existing functions for the given action and they could not be deleted
        ## TODO : LOG ERRORS
        user_msg.append("""Functions already existed for the "%s" action of the document type "%s" but they could not be """ \
                        """deleted. Unable to clone the functions of Document Type "%s" for action "%s".""" \
                        % (actname, todoctype, fromdoctype, action))
        ## critical - return 1 to signal this
        return 1
    elif error_code == 2:
        ## could not clone all functions for given action for new doctype
        ## TODO : LOG ERRORS
        user_msg.append("""Unable to clone all functions for the "%s" action from doctype "%s", for doctype "%s".""" \
                        % (action, fromdoctype, todoctype))
        return 2  ## not critical
    else:
        return 0  ## total success

def _clone_functionparameters_foraction_fromdoctype_todoctype(errors, warnings, user_msg, fromdoctype, todoctype, action):
    """Clone the parameters/values of a given action of one document type, to the same action on another document type.
       @param errors: a list of errors encountered while cloning parameters
       @param warnings: a list of warnings encountered while cloning parameters
       @param user_msg: any message to be displayed to the user (this is a list)
       @param fromdoctype: the doctype from which parameters are to be cloned
       @param todoctype: the doctype into which parameters are to be cloned
       @param action: the action for which parameters are to be cloned
       @return: 0 if it was not possible to clone all parameters/values; 1 if all parameters/values were cloned successfully.
    """
    error_code = clone_functionparameters_foraction_fromdoctype_todoctype(fromdoctype=fromdoctype, \
                                                                          todoctype=todoctype, action=action)
    if error_code in (1, 2):
        ## something went wrong and it was not possible to clone all parameters/values of "action"/"fromdoctype" for "action"/"todoctype"
        ## TODO : LOG ERRORS
        user_msg.append("""It was not possible to clone all parameter values from the action "%(act)s" of the document type""" \
                        """ "%(fromdt)s" for the action "%(act)s" of the document type "%(todt)s".""" \
                        % { 'act' : action, 'fromdt' : fromdoctype, 'todt' : todoctype }
                       )
        return 2 ## to signal that addition wasn't 100% successful
    else:
        return 0  ## all parameters were cloned

def _add_doctype(errors, warnings, doctype, doctypename, doctypedescr, clonefrom):
    title = ""
    body = ""
    user_msg = []
    numrows_doctype = get_number_doctypes_docid(docid=doctype)
    if numrows_doctype > 0:
        ## this document type already exists - do not add
        ## TODO : LOG ERROR
        user_msg.append("""A document type identified by "%s" already seems to exist and there cannot be added. Choose another ID.""" \
                   % (doctype,))
        (title, body) = _create_add_doctype_form(doctypename=doctypename, doctypedescr=doctypedescr, clonefrom=clonefrom, user_msg=user_msg)
    else:
        ## proceed with addition
        ## add the document type details:
        error_code = insert_doctype_details(doctype=doctype, doctypename=doctypename, doctypedescr=doctypedescr)
        if error_code == 0:
            ## added successfully
            if clonefrom not in ("", "None", None):
                ## document type should be cloned from "clonefrom"
                ## first, clone the categories from another doctype:
                error_code = _clone_categories_doctype(errors=errors,
                                                       warnings=warnings,
                                                       user_msg=user_msg,
                                                       fromdoctype=clonefrom,
                                                       todoctype=doctype)
                ## get details of clonefrom's submissions
                all_actnames_submissions_clonefrom = get_actname_all_submissions_doctype(doctype=clonefrom)
                if len(all_actnames_submissions_clonefrom) > 0:
                    ## begin cloning
                    for doc_submission_actname in all_actnames_submissions_clonefrom:
                        ## clone submission details:
                        action_name = doc_submission_actname[0]
                        _clone_submission_fromdoctype_todoctype(errors=errors, warnings=errors, user_msg=user_msg,
                                                                todoctype=doctype, action=action_name, clonefrom=clonefrom)

            user_msg.append("""The "%s" document type has been added.""" % (doctype,))
            title = """Available WebSubmit Document Types"""
            all_doctypes = get_docid_docname_alldoctypes()
            body = websubmitadmin_templates.tmpl_display_alldoctypes(doctypes=all_doctypes, user_msg=user_msg)
        else:
            ## could not add document type details - do no more
            ## TODO : LOG ERROR!
            user_msg.append("""Unable to add details for document type "%s".""" % (doctype,))
            (title, body) = _create_add_doctype_form(user_msg=user_msg)

    return (title, body)

def perform_request_add_doctype(doctype="", doctypename="", doctypedescr="", clonefrom="", doctypedetailscommit=""):
    errors = []
    warnings = []
    body = ""
    if doctypedetailscommit not in ("", None) and doctype not in ("", None):
        (title, body) = _add_doctype(errors=errors, warnings=warnings, doctype=doctype,
                                     doctypename=doctypename, doctypedescr=doctypedescr, clonefrom=clonefrom)
    else:
        (title, body) = _create_add_doctype_form(doctype=doctype, doctypename=doctypename, doctypedescr=doctypedescr, clonefrom=clonefrom)
    return (title, body, errors, warnings)

def _delete_referee_doctype(errors, warnings, doctype, categid, refereeid):
    """Delete a referee from a given category of a document type.
       @param doctype: the document type from whose category the referee is to be removed
       @param categid: the name/ID of the category from which the referee is to be removed
       @param refereeid: the id of the referee to be removed from the given category
       @return: a tuple containing 2 strings: (page title, page body)
    """
    user_msg = []
    role_name = """referee_%s_%s""" % (doctype, categid)
    error_code = acc_deleteUserRole(id_user=refereeid, name_roll=role_name)
    if error_code > 0:
        ## referee was deleted from category
        user_msg.append(""" "%s".""" % (doctype,))

def _create_list_referees_doctype(doctype):
    referees = {}
    referees_details = {}
    ## get all CDS Invenio roles:
    all_roles = acc_getAllRoles()
    for role in all_roles:
        (roleid, rolename) = (role[0], role[1])
        if re.match("^referee_%s_" % (doctype,), rolename):
            ## this is a "referee" role - get users of this role:
            role_users = acc_getRoleUsers(roleid)
            if role_users is not None and (type(role_users) in (tuple, list) and len(role_users) > 0):
                ## this role has users, record them in dictionary:
                referees[rolename] = role_users
    ## for each "group" of referees:
    for ref_role in referees.keys():
        ## get category ID for this referee-role:
        try:
            categid = re.match("^referee_%s_(.*)" % (doctype,), ref_role).group(1)
            ## from WebSubmit DB, get categ name for "categid":
            if categid != "*":
                categ_details = get_all_categories_sname_lname_for_doctype_categsname(doctype=doctype, categsname=categid)
                if len(categ_details) > 0:
                    ## if possible to receive details of this category, record them in a tuple in the format:
                    ## ("categ name", (tuple of users details)):
                    referees_details[ref_role] = (categid, categ_details[0][1], referees[ref_role])
            else:
                ## general referee entry:
                referees_details[ref_role] = (categid, "General Referee(s)", referees[ref_role])
        except AttributeError:
            ## there is no category for this role - it is broken, so pass it
            pass
    return referees_details

def _create_edit_doctype_details_form(errors, warnings, doctype, doctypename="", doctypedescr="", doctypedetailscommit="", user_msg=""):
    if user_msg == "" or type(user_msg) not in (list, tuple, str, unicode):
        user_msg = []
    elif type(user_msg) in (str, unicode):
        user_msg = [user_msg]
    title = "Edit Document Type Details"
    doctype_details = get_doctype_docname_descr_cd_md_fordoctype(doctype)
    if len(doctype_details) == 1:
        docname = doctype_details[0][1]
        docdescr = doctype_details[0][2]
        (cd, md) = (doctype_details[0][3], doctype_details[0][4])
        if doctypedetailscommit != "":
            ## could not commit details
            docname = doctypename
            docdescr = doctypedescr
        body = websubmitadmin_templates.tmpl_display_doctypedetails_form(doctype=doctype,
                                                                         doctypename=docname,
                                                                         doctypedescr=docdescr,
                                                                         cd=cd,
                                                                         md=md,
                                                                         user_msg=user_msg,
                                                                         perform_act="doctypeconfigure")
    else:
        ## problem retrieving details of doctype:
        user_msg.append("""Unable to retrieve details of doctype '%s' - cannot edit.""" % (doctype,),)
        ## TODO : LOG ERROR
        all_doctypes = get_docid_docname_alldoctypes()
        body = websubmitadmin_templates.tmpl_display_alldoctypes(doctypes=all_doctypes, user_msg=user_msg)
        title = "Available WebSubmit Document Types"
    return (title, body)

def _create_add_submission_choose_clonefrom_form(errors, warnings, doctype, action, user_msg=""):
    if user_msg == "" or type(user_msg) not in (list, tuple, str, unicode):
        user_msg = []
    elif type(user_msg) in (str, unicode):
        user_msg = [user_msg]
    
    ## does this doctype already have this action?
    numrows_doctype_action = get_number_submissions_doctype_action(doctype=doctype, action=action)
    if numrows_doctype_action < 1:
        ## action not present for this doctype - can be added
        ## get list of all doctypes implementing this action (for possible cloning purposes)
        doctypes_implementing_action = get_doctypeid_doctypes_implementing_action(action=action)
        ## create form to display document types to clone from
        title = "Add Submission '%s' to Document Type '%s'" % (action, doctype)
        body = websubmitadmin_templates.tmpl_display_submission_clone_form(doctype=doctype,
                                                                           action=action,
                                                                           clonefrom_list=doctypes_implementing_action,
                                                                           user_msg=user_msg
                                                                          )
    else:
        ## warn user that action already exists for doctype and canot be added, then display all
        ## details of doctype again
        user_msg.append("The Document Type '%s' already implements the Submission '%s' - cannot add it again" \
                        % (doctype, action))
        ## TODO : LOG WARNING
        (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
    return (title, body)

def _create_add_submission_form(errors, warnings, doctype, action, displayed="", buttonorder="", statustext="",
                                level="", score="", stpage="", endtxt="", user_msg=""):
    if user_msg == "" or type(user_msg) not in (list, tuple, str, unicode):
        user_msg = []
    elif type(user_msg) in (str, unicode):
        user_msg = [user_msg]
    title = "Add Submission '%s' to Document Type '%s'" % (action, doctype)
    body = websubmitadmin_templates.tmpl_display_submissiondetails_form(doctype=doctype,
                                                                        action=action,
                                                                        displayed=displayed,
                                                                        buttonorder=buttonorder,
                                                                        statustext=statustext,
                                                                        level=level,
                                                                        score=score,
                                                                        stpage=stpage,
                                                                        endtxt=endtxt,
                                                                        user_msg=user_msg,
                                                                        saveaction="add"
                                                                       )
    return (title, body)

def _create_delete_submission_form(errors, warnings, doctype, action):
    user_msg = []
    title = """Delete Submission "%s" from Document Type "%s" """ % (action, doctype)
    numrows_doctypesubmission = get_number_submissions_doctype_action(doctype=doctype, action=action)
    if numrows_doctypesubmission > 0:
        ## submission exists: create form to delete it:
        body = websubmitadmin_templates.tmpl_display_delete_doctypesubmission_form(doctype=doctype, action=action)
    else:
        ## submission doesn't seem to exist. Display details of doctype only:
        user_msg.append("""The Submission "%s" doesn't seem to exist for the Document Type "%s" - unable to delete it""" % (action, doctype))
        ## TODO : LOG ERRORS
        (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
    return (title, body)


def _create_edit_submission_form(errors, warnings, doctype, action, user_msg=""):
    if user_msg == "" or type(user_msg) not in (list, tuple, str, unicode):
        user_msg = []
    elif type(user_msg) in (str, unicode):
        user_msg = [user_msg]
    submission_details = get_submissiondetails_doctype_action(doctype=doctype, action=action)
    numrows_submission_details = len(submission_details)
    if numrows_submission_details == 1:
        ## correctly retrieved details of submission - display:
        submission_details = stringify_listvars(submission_details)
        displayed = submission_details[0][3]
        buttonorder = submission_details[0][7]
        statustext = submission_details[0][8]
        level = submission_details[0][9]
        score = submission_details[0][10]
        stpage = submission_details[0][11]
        endtxt = submission_details[0][12]
        cd = submission_details[0][5]
        md = submission_details[0][6]
        title = "Edit Details of '%s' Submission of '%s' Document Type" % (action, doctype)
        body = websubmitadmin_templates.tmpl_display_submissiondetails_form(doctype=doctype,
                                                                            action=action,
                                                                            displayed=displayed,
                                                                            buttonorder=buttonorder,
                                                                            statustext=statustext,
                                                                            level=level,
                                                                            score=score,
                                                                            stpage=stpage,
                                                                            endtxt=endtxt,
                                                                            cd=cd,
                                                                            md=md,
                                                                            user_msg=user_msg
                                                                           )
    else:
        if numrows_submission_details > 1:
            ## multiple rows for this submission - this is a key violation
            user_msg.append("Found multiple rows for the Submission '%s' of the Document Type '%s'" \
                            % (action, doctype))
        else:
            ## submission does not exist
            user_msg.append("The Submission '%s' of the Document Type '%s' doesn't seem to exist." \
                            % (action, doctype))
            ## TODO : LOG ERROR
        (title, body) = _create_configure_doctype_form(doctype, user_msg=user_msg)
    return (title, body)

def _create_edit_category_form(errors, warnings, doctype, categid):
    title = "Edit Category Description"
    categ_details = get_all_categories_sname_lname_for_doctype_categsname(doctype=doctype, categsname=categid)
    if len(categ_details) == 1:
        ## disaply details
        retrieved_categid=categ_details[0][0]
        retrieved_categdescr=categ_details[0][1]
        body = websubmitadmin_templates.tmpl_display_edit_category_form(doctype=doctype,
                                                                        categid=retrieved_categid,
                                                                        categdescr=retrieved_categdescr
                                                                       )
    else:
        ## problem retrieving details of categ
        user_msg = """Unable to retrieve details of category '%s'""" % (categid,)
        ## TODO : LOG ERRORS
        (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
    return (title, body)

def _create_configure_doctype_form(doctype, user_msg=""):
    title = "Configure Document Type"
    body = ""
    if user_msg == "" or type(user_msg) not in (list, tuple, str, unicode):
        user_msg = []
    ## get details of doctype:
    doctype_details = get_doctype_docname_descr_cd_md_fordoctype(doctype)
    docname = doctype_details[0][1]
    docdescr = doctype_details[0][2]
    (cd, md) = (doctype_details[0][3], doctype_details[0][4])
    ## get categories for doctype:
    doctype_categs = get_all_categories_sname_lname_doctype(doctype=doctype)
    ## get submissions for doctype:
    doctype_submissions = get_submissiondetails_all_submissions_doctype(doctype=doctype)
    ## get list of actions that this doctype doesn't have:
    unlinked_actions = get_actions_sname_lname_not_linked_to_doctype(doctype=doctype)
    ## get referees for doctype:
    referees_dets = _create_list_referees_doctype(doctype=doctype)
    body = websubmitadmin_templates.tmpl_configure_doctype_overview(doctype=doctype, doctypename=docname,
                                                                    doctypedescr=docdescr, doctype_cdate=cd,
                                                                    doctype_mdate=md, doctype_categories=doctype_categs,
                                                                    doctype_submissions=doctype_submissions,
                                                                    doctype_referees=referees_dets,
                                                                    add_actions_list=unlinked_actions,
                                                                    user_msg=user_msg
                                                                   )
    return (title, body)

def _delete_category_from_doctype(errors, warnings, doctype, categid):
    """Delete a category (categid) from the document type identified by "doctype".
       @param errors:  a list of errors encountered while deleting the category
       @param warnings: a list of warnings encountered while deleting the category
       @param doctype: the unique ID of the document type from which the category is to be deleted
       @param categid: the unique category ID of the category to be deleted from doctype
       @return: a tuple containing 2 strings: (page title, page body)
    """
    user_msg = []
    error_code = delete_category_doctype(doctype=doctype, categ=categid)
    if error_code == 0:
        ## successful delete
        user_msg.append("""'%s' Category Successfully Deleted""" % (categid,))
    else:
        ## could not delete category
        user_msg.append("""Unable to Delete '%s' Category""" % (categid,))
        ## TODO : LOG ERROR
    (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
    return (title, body)

def _clone_submission_fromdoctype_todoctype(errors, warnings, user_msg, todoctype, action, clonefrom):
    ## first, delete the submission from todoctype (if it exists):
    error_code = delete_submissiondetails_doctype(doctype=todoctype, action=action)
    if error_code == 0:
        ## could be deleted - now clone it
        error_code = insert_submission_details_clonefrom_submission(addtodoctype=todoctype, action=action, clonefromdoctype=clonefrom)
        if error_code == 0:
            ## submission inserted
            ## now clone functions:
            error_code = _clone_functions_foraction_doctype(errors=errors, warnings=warnings, user_msg=user_msg, \
                                    fromdoctype=clonefrom, todoctype=todoctype, action=action)
            if error_code in (0, 2):
                ## no serious error - clone parameters:
                error_code = _clone_functionparameters_foraction_fromdoctype_todoctype(errors=errors,
                                                                                       warnings=warnings,
                                                                                       user_msg=user_msg,
                                                                                       fromdoctype=clonefrom,
                                                                                       todoctype=todoctype,
                                                                                       action=action)
            ## now clone pages/elements
            error_code = clone_submissionfields_from_doctypesubmission_to_doctypesubmission(fromsub="%s%s" % (action, clonefrom),
                                                                                            tosub="%s%s" % (action, todoctype))
            if error_code == 1:
                ## could not delete all existing submission fields and therefore could no clone submission fields at all
                ## TODO : LOG ERROR
                user_msg.append("""Unable to delete existing submission fields for Submission "%s" of Document Type "%s" - """ \
                                """cannot clone submission fields!""" % (action, todoctype))
            elif error_code == 2:
                ## could not clone all fields
                ## TODO : LOG ERROR
                user_msg.append("""Unable to clone all submission fields for submission "%s" on Document Type "%s" from Document""" \
                                """ Type "%s" """ % (action, todoctype, clonefrom))
        else:
            ## could not insert submission details!
            user_msg.append("""Unable to successfully insert details of submission "%s" into Document Type "%s" - cannot clone from "%s" """ \
                            % (action, todoctype, clonefrom))
            ## TODO : LOG ERROR
    else:
        ## could not delete details of existing submission (action) from 'todoctype' - cannot clone it as new
        user_msg.append("""Unable to delete details of existing Submission "%s" from Document Type "%s" - cannot clone it from "%s" """ \
                        % (action, todoctype, clonefrom))
        ## TODO : LOG ERROR

def _add_submission_to_doctype_clone(errors, warnings, doctype, action, clonefrom):
    user_msg = []
    ## does action exist?
    numrows_action = get_number_actions_with_actid(actid=action)
    if numrows_action > 0:
        ## The action exists, but is it already implemented as a submission by doctype?
        numrows_submission_doctype = get_number_submissions_doctype_action(doctype=doctype, action=action)
        if numrows_submission_doctype > 0:
            ## this submission already exists for this document type - unable to add it again
            user_msg.append("""The Submission "%s" already exists for Document Type "%s" - cannot add it again""" \
                            %(action, doctype))
            ## TODO : LOG ERROR
        else:
            ## clone the submission
            _clone_submission_fromdoctype_todoctype(errors=errors, warnings=errors, user_msg=user_msg,
                                                    todoctype=doctype, action=action, clonefrom=clonefrom)
            user_msg.append("""Cloning of Submission "%s" from Document Type "%s" has been carried out. You should not""" \
                           """ ignore any warnings that you may have seen.""" % (action, clonefrom))
            ## TODO : LOG WARNING OF NEW SUBMISSION CREATION BY CLONING
    else:
        ## this action doesn't exist! cannot add a submission based upon it!
        user_msg.append("The Action '%s' does not seem to exist in WebSubmit. Cannot add it as a Submission!" \
                        % (action))
        ## TODO : LOG ERROR
    (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
    return (title, body)

def _add_submission_to_doctype(errors, warnings, doctype, action, displayed, buttonorder,
                               statustext, level, score, stpage, endtxt):
    user_msg = []
    ## does "action" exist?
    numrows_action = get_number_actions_with_actid(actid=action)
    if numrows_action < 1:
        ## this action does not exist! Can't add a submission based upon it!
        user_msg.append("'%s' does not exist in WebSubmit as an Action! Unable to add this submission."\
                        % (action,))
        ## TODO : LOG ERROR
        (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
        return (title, body)
    ## Insert the new submission
    error_code = insert_submission_details(doctype=doctype, action=action, displayed=displayed,
                                           nbpg="0", buttonorder=buttonorder, statustext=statustext,
                                           level=level, score=score, stpage=stpage, endtext=endtxt)
    if error_code == 0:
        ## successful insert
        user_msg.append("""'%s' Submission Successfully Added to Document Type '%s'""" % (action, doctype))
    else:
        ## could not insert submission into doctype
        user_msg.append("""Unable to Add '%s' Submission to '%s' Document Type""" % (action, doctype))
        ## TODO : LOG ERROR
    (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
    return (title, body)    

def _delete_submission_from_doctype(errors, warnings, doctype, action):
    """Delete a submission (action) from the document type identified by "doctype".
       @param errors:  a list of errors encountered while deleting the submission
       @param warnings: a list of warnings encountered while deleting the submission
       @param doctype: the unique ID of the document type from which the submission is to be deleted
       @param categid: the action ID of the submission to be deleted from doctype
       @return: a tuple containing 2 strings: (page title, page body)
    """
    user_msg = []
    ##numrows_doctypesubmission = get_number_submissions_doctype_action(doctype=doctype, action=action)
    ## delete fields for this submission:
    error_code = delete_all_submissionfields_submission("""%s%s""" % (action, doctype) )
    if error_code != 0:
        ## could not successfully delete all fields - report error
        user_msg.append("""When deleting Submission "%s" from Document Type "%s", it wasn't possible to delete all Submission Fields""" \
                        % (action, doctype))
        ## TODO : LOG ERROR
    ## delete parameters for this submission:
    error_code = delete_functionparameters_doctype_submission(doctype=doctype, action=action)
    if error_code != 0:
        ## could not successfully delete all functions - report error
        user_msg.append("""When deleting Submission "%s" from Document Type "%s", it wasn't possible to delete all Function Parameters""" \
                        % (action, doctype))
        ## TODO : LOG ERROR
    ## delete functions for this submission:
    error_code = delete_all_functions_foraction_doctype(doctype=doctype, action=action)
    if error_code != 0:
        ## could not successfully delete all functions - report error
        user_msg.append("""When deleting Submission "%s" from Document Type "%s", it wasn't possible to delete all Functions""" \
                        % (action, doctype))
        ## TODO : LOG ERROR
    ## delete this submission itself:
    error_code = delete_submissiondetails_doctype(doctype=doctype, action=action)
    if error_code == 0:
        ## successful delete
        user_msg.append("""The "%s" Submission has been deleted from the "%s" Document Type""" % (action, doctype))
    else:
        ## could not delete category
        user_msg.append("""Unable to successfully delete the "%s" Submission from the "%s" Document Type""" % (action, doctype))
        ## TODO : LOG ERROR
    (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
    return (title, body)


def _edit_submission_for_doctype(errors, warnings, doctype, action, displayed, buttonorder,
                                 statustext, level, score, stpage, endtxt):
    """Update the details of a given submission belonging to the document type identified by "doctype".
       @param errors:  a list of errors encountered while updating the submission's details
       @param warnings: a list of warnings encountered while updating the submission's details
       @param doctype: the unique ID of the document type for which the submission is to be updated
       @param action: action name of the submission to be updated
       @param displayed: displayed on main submission page? (Y/N)
       @param buttonorder: button order
       @param statustext: statustext
       @param level: level
       @param score: score
       @param stpage: stpage
       @param endtxt: endtxt
       @return: a tuple of 2 strings: (page title, page body)
    """
    user_msg = []
    error_code = update_submissiondetails_doctype_action(doctype=doctype, action=action, displayed=displayed,
                                                         buttonorder=buttonorder, statustext=statustext, level=level,
                                                         score=score, stpage=stpage, endtxt=endtxt)
    if error_code == 0:
        ## successful update
        user_msg.append("'%s' Submission of '%s' Document Type updated." % (action, doctype) )
    else:
        ## could not update
        user_msg.append("Unable to update '%s' Submission of '%s' Document Type." % (action, doctype) )
        ## TODO : LOG ERROR
    (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
    return (title, body)

def _edit_doctype_details(errors, warnings, doctype, doctypename, doctypedescr):
    """Update the details (name and/or description) of a document type (identified by doctype.)
       @param errors:  a list of errors encountered while updating the doctype's details
       @param warnings: a list of warnings encountered while updating the doctype's details
       @param doctype: the unique ID of the document type to be updated
       @param doctypename: the new/updated name for the doctype
       @param doctypedescr: the new/updated description for the doctype
       @return: a tuple containing 2 strings: (page title, page body)
    """
    user_msg = []
    error_code = update_doctype_details(doctype=doctype, doctypename=doctypename, doctypedescr=doctypedescr)
    if error_code == 0:
        ## successful update
        user_msg.append("""'%s' Document Type Updated""" % (doctype,))
    else:
        ## could not update
        user_msg.append("""Unable to Update Doctype '%s'""" % (doctype,))
        ## TODO : LOG ERROR
    (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
    return (title, body)

def _edit_category_for_doctype(errors, warnings, doctype, categid, categdescr):
    """Edit the description of a given category (identified by categid), belonging to
       the document type identified by doctype.
       @param errors:  a list of errors encountered while modifying the category
       @param warnings: a list of warnings encountered while modifying the category
       @param doctype: the unique ID of the document type for which the category is to be modified
       @param categid: the unique category ID of the category to be modified
       @param categdescr: the new description for the category
       @return: at tuple containing 2 strings: (page title, page body)
    """
    user_msg = []
    error_code = update_category_description_doctype_categ(doctype=doctype, categ=categid, categdescr=categdescr)
    if error_code == 0:
        ## successful update
        user_msg.append("""'%s' Category Description Successfully Updated""" % (categid,))
    else:
        ## could not update category description
        user_msg.append("""Unable to Description for Category '%s'""" % (categid,))
        ## TODO : LOG ERROR
    (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
    return (title, body)

def _add_category_to_doctype(errors, warnings, doctype, categid, categdescr):
    """Add a new category to the document type identified by "doctype".
       Category ID, and category description are both mandatory.
       @param errors:  a list of errors encountered while adding the category
       @param warnings: a list of warnings encountered while adding the category
       @param doctype: the unique ID of the document type to which the category is to be added
       @param categid: the unique category ID of the category to be added to doctype
       @param categdescr: the description of the category to be added
       @return: at tuple containing 2 strings: (page title, page body)
    """
    user_msg = []
    error_code = insert_category_doctype(doctype=doctype, categ=categid, categdescr=categdescr)
    if error_code == 0:
        ## successful insert
        user_msg.append("""'%s' Category Successfully Added""" % (categid,))
    else:
        ## could not insert category into doctype
        user_msg.append("""Unable to Add '%s' Category""" % (categid,))
        ## TODO : LOG ERROR
    (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
    return (title, body)

def perform_request_configure_doctype(doctype,
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
                                      doctypesubmissionadddetailscommit="",
                                      doctypesubmissioneditdetailscommit="",
                                      categid="",
                                      categdescr="",
                                      action="",
                                      doctype_cloneactionfrom="",
                                      displayed="",
                                      buttonorder="",
                                      statustext="",
                                      level="",
                                      score="",
                                      stpage="",
                                      endtxt="",
                                      doctyperefereedelete=""
                                     ):
    errors = []
    warnings = []
    body = ""
    ## ensure that there is only one doctype for this doctype ID - simply display all doctypes with warning if not
    numrows_doctype = get_number_doctypes_docid(docid=doctype)
    if numrows_doctype > 1:
        ## there are multiple doctypes with this doctype ID:
        ## TODO : LOG ERROR
        user_msg.append("""Multiple document types identified by "%s" exist - cannot configure at this time.""" \
                   % (doctype,))
        all_doctypes = get_docid_docname_alldoctypes()
        body = websubmitadmin_templates.tmpl_display_alldoctypes(doctypes=all_doctypes, user_msg=user_msg)
        title = "Available WebSubmit Document Types"
        return (title, body, errors, warnings)
    elif numrows_doctype == 0:
        ## this doctype does not seem to exist:
        user_msg.append("""The document type identified by "%s" doesn't exist - cannot configure at this time.""" \
                   % (doctype,))
        ## TODO : LOG ERROR
        all_doctypes = get_docid_docname_alldoctypes()
        body = websubmitadmin_templates.tmpl_display_alldoctypes(doctypes=all_doctypes, user_msg=user_msg)
        title = "Available WebSubmit Document Types"
        return (title, body, errors, warnings)

    ## since doctype ID is OK, process doctype configuration request:
    if doctypedetailsedit not in ("", None):
        (title, body) = _create_edit_doctype_details_form(errors=errors, warnings=warnings, doctype=doctype)
    elif doctypedetailscommit not in ("", None):
        ## commit updated document type details
        (title, body) = _edit_doctype_details(errors=errors, warnings=warnings, doctype=doctype,
                                              doctypename=doctypename, doctypedescr=doctypedescr)
    elif doctypecategoryadd not in ("", None):
        ## add new category:
        (title, body) = _add_category_to_doctype(errors=errors, warnings=warnings,
                                                 doctype=doctype, categid=categid, categdescr=categdescr)
    elif doctypecategoryedit not in ("", None):
        ## create form to update category description:
        (title, body) = _create_edit_category_form(errors=errors, warnings=warnings, doctype=doctype,
                                                   categid=categid)
    elif doctypecategoryeditcommit not in ("", None):
        ## commit updated category description:
        (title, body) = _edit_category_for_doctype(errors=errors, warnings=warnings,
                                                   doctype=doctype, categid=categid, categdescr=categdescr)
    elif doctypecategorydelete not in ("", None):
        ## delete a category
        (title, body) = _delete_category_from_doctype(errors=errors, warnings=warnings,
                                                      doctype=doctype, categid=categid)
    elif doctypesubmissionadd not in ("", None):
        ## form displaying option of adding doctype:
        (title, body) = _create_add_submission_choose_clonefrom_form(errors=errors, warnings=warnings, doctype=doctype, action=action)
    elif doctypesubmissionaddclonechosen not in ("", None):
        ## add a submission. if there is a document type to be cloned from, then process clone;
        ## otherwise, present form with details of doctype
        if doctype_cloneactionfrom in ("", None, "None"):
            ## no clone - present form into which details of new submission should be entered
            (title, body) = _create_add_submission_form(errors=errors, warnings=warnings, doctype=doctype, action=action)
        else:
            ## new submission should be cloned from doctype_cloneactionfrom
            (title, body) = _add_submission_to_doctype_clone(errors=errors, warnings=warnings,
                                                             doctype=doctype, action=action, clonefrom=doctype_cloneactionfrom)
    elif doctypesubmissiondelete not in ("", None):
        ## create form to prompt for confirmation of deletion of a submission:
        (title, body) = _create_delete_submission_form(errors=errors, warnings=warnings, doctype=doctype, action=action)
    elif doctypesubmissiondeleteconfirm not in ("", None):
        ## process the deletion of a submission from the doctype concerned:
        (title, body) = _delete_submission_from_doctype(errors=errors, warnings=warnings,
                                                        doctype=doctype, action=action)
    elif doctypesubmissionedit not in ("", None):
        ## create form to update details of a submission
        (title, body) = _create_edit_submission_form(errors=errors, warnings=warnings, doctype=doctype, action=action)
    elif doctypesubmissioneditdetailscommit not in ("", None):
        ## commit updated submission details:
        (title, body) = _edit_submission_for_doctype(errors=errors, warnings=warnings, doctype=doctype, action=action,
                                                     displayed=displayed, buttonorder=buttonorder, statustext=statustext,
                                                     level=level, score=score, stpage=stpage, endtxt=endtxt)
    elif doctypesubmissionadddetailscommit not in ("", None):
        ## commit new submission to doctype (not by cloning)
        (title, body) = _add_submission_to_doctype(errors=errors, warnings=warnings, doctype=doctype, action=action,
                                                   displayed=displayed, buttonorder=buttonorder, statustext=statustext,
                                                   level=level, score=score, stpage=stpage, endtxt=endtxt)
    else:
        ## default - display root of edit doctype
        (title, body) = _create_configure_doctype_form(doctype)
    return (title, body, errors, warnings)

def _create_configure_doctype_submission_functions_form(doctype,
                                                        action,
                                                        movefromfunctionname="",
                                                        movefromfunctionstep="",
                                                        movefromfunctionscore="",
                                                        user_msg=""
                                                       ):
    title = """Functions of the "%s" Submission of the "%s" Document Type:""" % (action, doctype)
    submission_functions = get_functionname_step_score_allfunctions_doctypesubmission(doctype=doctype, action=action)
    all_websubmit_functions = get_funcname_allfunctions()
    body = websubmitadmin_templates.tmpl_configuredoctype_display_submissionfunctions(doctype=doctype,
                                                                                      action=action,
                                                                                      movefromfunctionname=movefromfunctionname,
                                                                                      movefromfunctionstep=movefromfunctionstep,
                                                                                      movefromfunctionscore=movefromfunctionscore,
                                                                                      submissionfunctions=submission_functions,
                                                                                      allWSfunctions=all_websubmit_functions,
                                                                                      user_msg=user_msg
                                                                                     )
    return (title, body)

def perform_request_configure_doctype_submissionfunctions(doctype,
                                                          action,
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
                                                          deletefunctionscore=""
                                                         ):

    errors = []
    warnings = []
    body = ""
    user_msg = []
    ## ensure that there is only one doctype for this doctype ID - simply display all doctypes with warning if not
    if doctype in ("", None):
        user_msg.append("""Unknown Document Type""")
        ## TODO : LOG ERROR
        all_doctypes = get_docid_docname_alldoctypes()
        body = websubmitadmin_templates.tmpl_display_alldoctypes(doctypes=all_doctypes, user_msg=user_msg)
        title = "Available WebSubmit Document Types"
        return (title, body, errors, warnings)

    numrows_doctype = get_number_doctypes_docid(docid=doctype)
    if numrows_doctype > 1:
        ## there are multiple doctypes with this doctype ID:
        ## TODO : LOG ERROR
        user_msg.append("""Multiple document types identified by "%s" exist - cannot configure at this time.""" \
                   % (doctype,))
        all_doctypes = get_docid_docname_alldoctypes()
        body = websubmitadmin_templates.tmpl_display_alldoctypes(doctypes=all_doctypes, user_msg=user_msg)
        title = "Available WebSubmit Document Types"
        return (title, body, errors, warnings)
    elif numrows_doctype == 0:
        ## this doctype does not seem to exist:
        user_msg.append("""The document type identified by "%s" doesn't exist - cannot configure at this time.""" \
                   % (doctype,))
        ## TODO : LOG ERROR
        all_doctypes = get_docid_docname_alldoctypes()
        body = websubmitadmin_templates.tmpl_display_alldoctypes(doctypes=all_doctypes, user_msg=user_msg)
        title = "Available WebSubmit Document Types"
        return (title, body, errors, warnings)

    ## ensure that this submission exists for this doctype:
    numrows_submission = get_number_submissions_doctype_action(doctype=doctype, action=action)
    if numrows_submission > 1:
        ## there are multiple submissions for this doctype/action ID:
        ## TODO : LOG ERROR
        user_msg.append("""The Submission "%s" seems to exist multiple times for the Document Type "%s" - cannot configure at this time.""" \
                   % (action, doctype))
        all_doctypes = get_docid_docname_alldoctypes()
        body = websubmitadmin_templates.tmpl_display_alldoctypes(doctypes=all_doctypes, user_msg=user_msg)
        (title, body) = _create_configure_doctype_form(doctype)
        return (title, body, errors, warnings)
    elif numrows_submission == 0:
        ## this submission does not seem to exist for this doctype:
        user_msg.append("""The Submission "%s" doesn't exist for the "%s" Document Type - cannot configure at this time.""" \
                   % (action, doctype))
        ## TODO : LOG ERROR
        (title, body) = _create_configure_doctype_form(doctype, user_msg=user_msg)
        return (title, body, errors, warnings)
        

    ## submission valid
    if movefromfunctionname != "" and movefromfunctionstep != "" and movefromfunctionscore != "" and \
       movetofunctionname != "" and movetofunctionstep != "" and movetofunctionscore != "":
        ## process moving the function by jumping it to another position
        error_code = move_position_submissionfunction_fromposn_toposn(doctype=doctype,
                                                                      action=action,
                                                                      movefuncname=movefromfunctionname,
                                                                      movefuncfromstep=movefromfunctionstep,
                                                                      movefuncfromscore=movefromfunctionscore,
                                                                      movefunctoname=movetofunctionname,
                                                                      movefunctostep=movetofunctionstep,
                                                                      movefunctoscore=movetofunctionscore)
        if error_code == 0:
            ## success
            user_msg.append("""The Function "%s" that was located at step %s, score %s, has been moved""" \
                             % (movefromfunctionname, movefromfunctionstep, movefromfunctionscore))
        else:
            ## could not move it
            user_msg.append("""Unable to move the Function "%s" that is located at step %s, score %s""" \
                                % (movefromfunctionname, movefromfunctionstep, movefromfunctionscore))
        (title, body) = _create_configure_doctype_submission_functions_form(doctype=doctype,
                                                                            action=action,
                                                                            user_msg=user_msg)
    elif moveupfunctionname != "" and moveupfunctionstep != "" and moveupfunctionscore != "":
        ## process moving the function up one position
        error_code = move_position_submissionfunction_up(doctype=doctype,
                                                         action=action,
                                                         function=moveupfunctionname,
                                                         funccurstep=moveupfunctionstep,
                                                         funccurscore=moveupfunctionscore)
        if error_code == 0:
            ## success
            user_msg.append("""The Function "%s" that was located at step %s, score %s, has been moved upwards""" \
                             % (moveupfunctionname, moveupfunctionstep, moveupfunctionscore))
        else:
            ## could not move it
            user_msg.append("""Unable to move the Function "%s" that is located at step %s, score %s""" \
                                % (moveupfunctionname, moveupfunctionstep, moveupfunctionscore))
        (title, body) = _create_configure_doctype_submission_functions_form(doctype=doctype,
                                                                            action=action,
                                                                            user_msg=user_msg)
    elif movedownfunctionname != "" and movedownfunctionstep != "" and movedownfunctionscore != "":
        ## process moving the function down one position
        error_code = move_position_submissionfunction_down(doctype=doctype,
                                                           action=action,
                                                           function=movedownfunctionname,
                                                           funccurstep=movedownfunctionstep,
                                                           funccurscore=movedownfunctionscore)
        if error_code == 0:
            ## success
            user_msg.append("""The Function "%s" that was located at step %s, score %s, has been moved downwards""" \
                             % (movedownfunctionname, movedownfunctionstep, movedownfunctionscore))
        else:
            ## could not move it
            user_msg.append("""Unable to move the Function "%s" that is located at step %s, score %s""" \
                                % (movedownfunctionname, movedownfunctionstep, movedownfunctionscore))
        (title, body) = _create_configure_doctype_submission_functions_form(doctype=doctype,
                                                                            action=action,
                                                                            user_msg=user_msg)
    elif deletefunctionname != "" and deletefunctionstep != "" and deletefunctionscore != "":
        ## process deletion of function from the given position
        (title, body) = ("", "")
    else:
        ## default - display functions for this submission
        (title, body) = _create_configure_doctype_submission_functions_form(doctype=doctype,
                                                                            action=action,
                                                                            movefromfunctionname=movefromfunctionname,
                                                                            movefromfunctionstep=movefromfunctionstep,
                                                                            movefromfunctionscore=movefromfunctionscore
                                                                           )

##         title = """Functions of the "%s" Submission of the "%s" Document Type:""" % (action, doctype)
##         submission_functions = get_functionname_step_score_allfunctions_doctypesubmission(doctype=doctype, action=action)
##         all_websubmit_functions = get_funcname_allfunctions()
##         body = websubmitadmin_templates.tmpl_configuredoctype_display_submissionfunctions(doctype=doctype,
##                                                                                           action=action,
##                                                                                           movefromfunctionname=movefromfunctionname,
##                                                                                           movefromfunctionstep=movefromfunctionstep,
##                                                                                           movefromfunctionscore=movefromfunctionscore,
##                                                                                           submissionfunctions=submission_functions,
##                                                                                           allWSfunctions=all_websubmit_functions
##                                                                                          )
    return (title, body, errors, warnings)
