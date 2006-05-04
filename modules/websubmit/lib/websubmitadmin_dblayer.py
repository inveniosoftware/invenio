# -*- coding: utf-8 -*-

from invenio.dbquery import run_sql
from MySQLdb import escape

## Functions relating to WebSubmit ACTIONS, their addition, and their modification:

def update_action_details(actid, actname, working_dir, status_text):
    """Update the details of an action in the websubmit database IF there was only one action
       with that actid (sactname).
       @param actid: unique action id (sactname)
       @param actname: action name (lactname)
       @param working_dir: directory action works from (dir)
       @param status_text: text string indicating action status (statustext)
       @return 0 (ZERO) if update is performed; 1 (ONE) if insert not performed due to rows existing for
                 given action name.
   """
    # Check record with code 'actid' does not already exist:
    numrows_actid = get_number_actions_with_actid(actid)
    if numrows_actid == 1:
        q ="""UPDATE sbmACTION SET lactname=%s, dir=%s, statustext=%s, md=CURDATE() WHERE sactname=%s"""
        run_sql(q, (actname, working_dir, status_text, actid))
        return 0 # Everything is OK
    else:
        return 1 # Everything not OK: Either no rows or more than one row for action "actid"

def get_action_details(actid):
    """Get and return a tuple of tuples for all actions with the sactname "actid".
       @param actid: Action Identifier Code (sactname).
       @return: tuple of tuples (one tuple per action row): (sactname,lactname,dir,statustext,cd,md).
    """
    q = """SELECT act.sactname, act.lactname, act.dir, act.statustext, act.cd, act.md FROM sbmACTION AS act WHERE act.sactname=%s"""
    return run_sql(q, (actid,))

def get_actid_actname_allactions():
    """Get and return a tuple of tuples containing the "action id" and "action name" for each action
       in the WebSubmit database.
       @return: tuple of tuples: (actid,actname)
    """
    q = """SELECT sactname,lactname FROM sbmACTION ORDER BY sactname ASC"""
    return run_sql(q)

def get_number_actions_with_actid(actid):
    """Return the number of actions found for a given action id.
       @param actid: action id (sactname) to query for
       @return an integer count of the number of actions in the websubmit database for this actid.
    """
    q = """SELECT COUNT(sactname) FROM sbmACTION WHERE sactname=%s"""
    return int(run_sql(q, (actid,))[0][0])

def insert_action_details(actid, actname, working_dir, status_text):
    """Insert details of a new action into the websubmit database IF there are not already actions
       with the same actid (sactname).
       @param actid: unique action id (sactname)
       @param actname: action name (lactname)
       @param working_dir: directory action works from (dir)
       @param status_text: text string indicating action status (statustext)
       @return 0 (ZERO) if insert is performed; 1 (ONE) if insert not performed due to rows existing for
                 given action name.
   """
    # Check record with code 'actid' does not already exist:
    numrows_actid = get_number_actions_with_actid(actid)
    if numrows_actid == 0:
        # insert new action:
        q = """INSERT INTO sbmACTION (lactname,sactname,dir,cd,md,actionbutton,statustext) VALUES (%s,%s,%s,CURDATE(),CURDATE(),NULL,%s)"""
        run_sql(q, (actname, actid, working_dir, status_text))
        return 0 # Everything is OK
    else:
        return 1 # Everything not OK: rows may already exist for action with 'actid'


## Functions relating to WebSubmit Form Element JavaScript CHECKING FUNCTIONS, their addition, and their
## modification:

def get_number_jschecks_with_chname(chname):
    """Return the number of Checks found for a given check name/id.
       @param chname: Check name/id (chname) to query for
       @return an integer count of the number of Checks in the WebSubmit database for this chname.
    """
    q = """SELECT COUNT(chname) FROM sbmCHECKS where chname=%s"""
    return int(run_sql(q, (chname,))[0][0])

def get_chname_alljschecks():
    """Get and return a tuple of tuples containing the "check name" (chname) for each JavaScript Check
       in the WebSubmit database.
       @return: tuple of tuples: (chname)
    """
    q = """SELECT chname FROM sbmCHECKS ORDER BY chname ASC"""
    return run_sql(q)

def get_jscheck_details(chname):
    """Get and return a tuple of tuples for all Checks with the check id/name "chname".
       @param chname: Check name/Identifier Code (chname).
       @return: tuple of tuples (one tuple per check row): (chname,chdesc,cd,md).
    """
    q = """SELECT ch.chname, ch.chdesc, ch.cd, ch.md FROM sbmCHECKS AS ch WHERE ch.chname=%s"""
    return run_sql(q, (chname,))

def insert_jscheck_details(chname, chdesc):
    """Insert details of a new JavaScript Check into the WebSubmit database IF there are not already Checks
       with the same Check-name (chname).
       @param chname: unique check id/name (chname)
       @param chdesc: Check description (the JavaScript code body that is the Check) (chdesc)
       @return 0 (ZERO) if insert is performed; 1 (ONE) if insert not performed due to rows existing for
                 given Check name/id.
   """
    # Check record with code 'chname' does not already exist:
    numrows_chname = get_number_jschecks_with_chname(chname)
    if numrows_chname == 0:
        # insert new Check:
        q = """INSERT INTO sbmCHECKS (chname,chdesc,cd,md,chefi1,chefi2) VALUES (%s,%s,CURDATE(),CURDATE(),NULL,NULL)"""
        run_sql(q, (chname, chdesc))
        return 0 # Everything is OK
    else:
        return 1 # Everything not OK: rows may already exist for Check with 'chname'

def update_jscheck_details(chname, chdesc):
    """Update the details of a Check in the WebSubmit database IF there was only one Check
       with that check id/name (chname).
       @param chname: unique Check id/name (chname)
       @param chdesc: Check description (the JavaScript code body that is the Check) (chdesc)
       @return 0 (ZERO) if update is performed; 1 (ONE) if insert not performed due to rows existing for
                 given Check.
    """
    # Check record with code 'chname' does not already exist:
    numrows_chname = get_number_jschecks_with_chname(chname)
    if numrows_chname == 1:
        q = """UPDATE sbmCHECKS SET chdesc=%s, md=CURDATE() WHERE chname=%s"""
        run_sql(q, (chdesc, chname))
        return 0 # Everything is OK
    else:
        return 1 # Everything not OK: Either no rows or more than one row for check "chname"


## Functions relating to WebSubmit FUNCTIONS, their addition, and their modification:

def get_function_description(function):
    """Get and return a tuple containing the function description (description) for
       the function with the name held in the "function" parameter.
       @return: tuple of tuple (for one function): ((description,))
    """
    q = """SELECT description FROM sbmALLFUNCDESCR where function=%s"""
    return run_sql(q, (function,))

def get_function_parameters(function):
    """Get the list of paremeters for a given function
       @param function: the function name
       @return: tuple of tuple ((param,))
    """
    q = """SELECT param FROM sbmFUNDESC WHERE function=%s ORDER BY param ASC"""
    return run_sql(q, (function,))

def get_number_parameters_with_paramname_funcname(funcname, paramname):
    """Return the number of parameters found for a given function name and parameter name. I.e. count the
       number of times a given parameter appears for a given function.
       @param funcname: Function name (function) to query for.
       @param paramname: name of the parameter whose instances for the given function are to be counted.
       @return an integer count of the number of parameters matching the criteria.
    """
    q = """SELECT COUNT(param) FROM sbmFUNDESC WHERE function=%s AND param=%s"""
    return int(run_sql(q, (funcname, paramname))[0][0])

def get_distinct_paramname_all_function_parameters():
    """Get the names of all function parameters.
       @return: tuple of tuples: (param,)
    """
    q = """SELECT DISTINCT(param) FROM sbmFUNDESC ORDER BY param ASC"""
    return run_sql(q)

def get_distinct_paramname_all_websubmit_parameters():
    """Get the names of all WEBSUBMIT parameters (i.e. parameters that are used somewhere by WebSubmit actions.
       @return: tuple of tuples (param,)
    """
    q = """SELECT DISTINCT(name) FROM sbmPARAMETERS ORDER BY name ASC"""
    return run_sql(q)

def get_distinct_paramname_all_websubmit_function_parameters():
    """Get and return a tuple of tuples containing the names of all parameters in the WebSubmit system.
       @return: tuple of tuples: ((param,),(param,))
    """
    param_names = {}
    all_params_list = []
    all_function_params = get_distinct_paramname_all_function_parameters()
    all_websubmit_params = get_distinct_paramname_all_websubmit_parameters()
    for func_param in all_function_params:
        param_names[func_param[0]] = None
    for websubmit_param in all_websubmit_params:
        param_names[websubmit_param[0]] = None
    all_params_names = param_names.keys()
    all_params_names.sort()
    for param in all_params_names:
        all_params_list.append((param,))
    return all_params_list

def get_funcname_funcdesc_allfunctions():
    """Get and return a tuple of tuples containing the "function name" (function) and function textual
       description (description) for each WebSubmit function in the WebSubmit database.
       @return: tuple of tuples: (function,description)
    """
    q = """SELECT function,description FROM sbmALLFUNCDESCR ORDER BY function ASC"""
    return run_sql(q)

def get_doctype_docnam_actid_actnam_fstep_fscore_function(function):
    """Get the details of a function's usage.
       @param function: The name of the function whose WebSubmit usage is to be examined.
       @return: tuple of tuples: (doctype, docname, action id, action name, function-step, function-score)
    """
    q = """SELECT fun.doctype, dt.ldocname, fun.action, actn.lactname, fun.step, fun.score """ +\
        """FROM sbmDOCTYPE AS dt LEFT JOIN sbmFUNCTIONS AS fun ON (fun.doctype=dt.sdocname) """ +\
        """LEFT JOIN sbmIMPLEMENT as imp ON (fun.action=imp.actname AND fun.doctype=imp.docname) """ +\
        """LEFT JOIN sbmACTION AS actn ON (actn.sactname=imp.actname) WHERE fun.function=%s """ +\
        """ORDER BY dt.sdocname ASC, fun.action ASC, fun.step ASC, fun.score ASC"""
    return run_sql(q, (function,))

def get_number_functions_with_funcname(funcname):
    """Return the number of Functions found for a given function name.
       @param funcname: Function name (function) to query for
       @return an integer count of the number of Functions in the WebSubmit database for this function name.
    """
    q = """SELECT COUNT(function) FROM sbmALLFUNCDESCR where function=%s"""
    return int(run_sql(q, (funcname,))[0][0])

def insert_function_details(function, fundescr):
    """"""
    numrows_function = get_number_functions_with_funcname(function)
    if numrows_function == 0:
        ## Insert new function
        q = """INSERT INTO sbmALLFUNCDESCR (function, description) VALUES (%s, %s)"""
        run_sql(q, (function, fundescr))
        return 0 # Everything is OK
    else:
        return 1 # Everything not OK: rows may already exist for function with name 'function'

def update_function_description(funcname, funcdescr):
    """Update the description of function "funcname", with string contained in "funcdescr".
       Function description will be updated only if one row was found for the function in the DB.
       @param funcname: the unique function name of the function whose description is to be updated
       @param funcdescr: the new, updated description of the function
       @return: error code (0 is OK, 1 is BAD insert)
    """
    numrows_function = get_number_functions_with_funcname(funcname)
    if numrows_function == 1:
        ## perform update of description
        q = """UPDATE sbmALLFUNCDESCR SET description=%s WHERE function=%s"""
        run_sql(q, ( (funcdescr != "" and funcdescr) or (None), funcname ) )
        return 0 ## Everything OK
    else:
        return 1 ## Everything not OK: either no rows, or more than 1 row for function "funcname"

def delete_function_parameter(function, parameter_name):
    """Delete a given parameter from a from a given function.
       @param function: name of the function from which the parameter is to be deleted.
       @param parameter_name: name of the parameter to be deleted from the function.
       @return: error-code.  0 means successful deletion of the parameter; 1 means deletion failed because
        the parameter did not exist for the given function.
    """
    numrows_function_parameter = get_number_parameters_with_paramname_funcname(funcname=function, paramname=parameter_name)
    if numrows_function_parameter >= 1:
        ## perform deletion of parameter(s)
        q = """DELETE FROM sbmFUNDESC WHERE function=%s AND param=%s"""
        run_sql(q, (function, parameter_name))
        return 0 ## Everything OK
    else:
        return 1 ## Everything not OK: no rows  - this parameter doesn't exist for this function

def add_function_parameter(function, parameter_name):
    """Add a parameter (parameter_name) to a given function.
       @param function: name of the function from which the parameter is to be deleted.
       @param parameter_name: name of the parameter to be deleted from the function.
       @return: error-code.  0 means successful addition of the parameter; 1 means addition failed because
        the parameter already existed for the given function.
    """
    numrows_function_parameter = get_number_parameters_with_paramname_funcname(funcname=function, paramname=parameter_name)
    if numrows_function_parameter == 0:
        ## perform addition of parameter
        q = """INSERT INTO sbmFUNDESC (function, param) VALUES (%s, %s)"""
        run_sql(q, (function, parameter_name))
        return 0 ## Everything OK
    else:
        return 1 ## Everything NOT OK: parameter already exists for function

## Functions relating to WebSubmit ELEMENTS, their addition, and their modification:

def get_number_elements_with_elname(elname):
    """Return the number of Elements found for a given element name/id.
       @param elname: Element name/id (name) to query for
       @return an integer count of the number of Elements in the WebSubmit database for this elname.
    """
    q = """SELECT COUNT(name) FROM sbmFIELDDESC where name=%s"""
    return int(run_sql(q, (elname,))[0][0])

def get_subname_pagenb_element_use(elname):
    """Get and return a tuple of tuples containing the "submission name" (subname) and the
       page number (pagenb) for the instances of use of the element identified by "elname".
       I.e. get the information about which submission pages the element is used on.
       @param elname: The unique identifier for an element ("name" in "sbmFIELDDESC",
                      "fidesc" in "sbmFIELD").
       @return: tuple of tuples (subname, pagenb)
    """
    q = """SELECT sf.subname, sf.pagenb FROM sbmFIELD AS sf WHERE sf.fidesc=%s ORDER BY sf.subname ASC, sf.pagenb ASC"""
    return run_sql(q, (elname,))

def get_elename_allelements():
    """Get and return a tuple of tuples containing the "element name" (name) for each WebSubmit
       element in the WebSubmit database.
       @return: tuple of tuples: (name)
    """
    q = """SELECT name FROM sbmFIELDDESC ORDER BY name"""
    return run_sql(q)

def get_element_details(elname):
    """Get and return a tuple of tuples for all ELEMENTS with the element name "elname".
       @param elname: ELEMENT name (elname).
       @return: tuple of tuples (one tuple per check row): (marccode,type,size,rows,cols,maxlength,
                                                            val,fidesc,cd,md,modifytext,cookie)
    """
    q = "SELECT el.marccode, el.type, el.size, el.rows, el.cols, el.maxlength, " + \
           "el.val, el.fidesc, el.cd, el.md, el.modifytext, el.cookie FROM sbmFIELDDESC AS el WHERE el.name=%s"
    return run_sql(q, (elname,))

def update_element_details(elname, elmarccode, eltype, elsize, elrows, elcols, elmaxlength, \
                           elval, elfidesc, elmodifytext, elcookie):
    """Update the details of an ELEMENT in the WebSubmit database IF there was only one Element
       with that element id/name (name).
       @param elname: unique Element id/name (name)
       @param elmarccode: element's MARC code
       @param eltype: type of element
       @param elsize: size of element
       @param elrows: number of rows in element
       @param elcols: number of columns in element
       @param elmaxlength: element maximum length
       @param elval: element default value
       @param elfidesc: element description
       @param elmodifytext: element's modification text
       @param elcookie: does this element set a cookie?
       @return 0 (ZERO) if update is performed; 1 (ONE) if update not performed due to rows existing for
                 given Element.
    """
    # Check record with code 'elname' does not already exist:
    numrows_elname = get_number_elements_with_elname(elname)
    if numrows_elname == 1:
        q = """UPDATE sbmFIELDDESC SET marccode=%s, type=%s, size=%s, rows=%s, cols=%s, maxlength=%s, """ +\
            """val=%s, fidesc=%s, modifytext=%s, cookie=%s, md=CURDATE() WHERE name=%s"""
        run_sql(q, ( elmarccode,
                     (eltype != "" and eltype) or (None),
                     (elsize != "" and elsize) or (None),
                     (elrows != "" and elrows) or (None),
                     (elcols != "" and elcols) or (None),
                     (elmaxlength != "" and elmaxlength) or (None),
                     (elval != "" and elval) or (None),
                     (elfidesc != "" and elfidesc) or (None),
                     (elmodifytext != "" and elmodifytext) or (None),
                     (elcookie != "" and elcookie) or ("0"),
                     elname
                   ) )
        return 0 # Everything is OK
    else:
        return 1 # Everything not OK: Either no rows or more than one row for element "elname"


def insert_element_details(elname, elmarccode, eltype, elsize, elrows, elcols, \
                           elmaxlength, elval, elfidesc, elmodifytext, elcookie):
    """Insert details of a new Element into the WebSubmit database IF there are not already elements
       with the same element name (name).
       @param elname: unique Element id/name (name)
       @param elmarccode: element's MARC code
       @param eltype: type of element
       @param elsize: size of element
       @param elrows: number of rows in element
       @param elcols: number of columns in element
       @param elmaxlength: element maximum length
       @param elval: element default value
       @param elfidesc: element description
       @param elmodifytext: element's modification text
       @param elcookie: does this element set a cookie?
       @return 0 (ZERO) if insert is performed; 1 (ONE) if insert not performed due to rows existing for
                 given Element.
    """
    # Check element record with code 'elname' does not already exist:
    numrows_elname = get_number_elements_with_elname(elname)
    if numrows_elname == 0:
        # insert new Check:
        q = """INSERT INTO sbmFIELDDESC (name, alephcode, marccode, type, size, rows, cols, """ +\
            """maxlength, val, fidesc, cd, md, modifytext, fddfi2, cookie) VALUES(%s, NULL, """ +\
            """%s, %s, %s, %s, %s, %s, %s, %s, CURDATE(), CURDATE(), %s, NULL, %s)"""
        run_sql(q, ( elname,
                     elmarccode,
                     (eltype != "" and eltype) or (None),
                     (elsize != "" and elsize) or (None),
                     (elrows != "" and elrows) or (None),
                     (elcols != "" and elcols) or (None),
                     (elmaxlength != "" and elmaxlength) or (None),
                     (elval != "" and elval) or (None),
                     (elfidesc != "" and elfidesc) or (None),
                     (elmodifytext != "" and elmodifytext) or (None),
                     (elcookie != "" and elcookie) or ("0")
                   ) )
        return 0 # Everything is OK
    else:
        return 1 # Everything not OK: rows may already exist for Element with 'elname'


# Functions relating to WebSubmit DOCUMENT TYPES:

def get_docid_docname_alldoctypes():
    """Get and return a tuple of tuples containing the "doctype id" (sdocname) and
       "doctype name" (ldocname) for each action in the WebSubmit database.
       @return: tuple of tuples: (docid,docname)
    """
    q = """SELECT sdocname, ldocname FROM sbmDOCTYPE ORDER BY ldocname ASC"""
    return run_sql(q)

def get_docid_docname_and_docid_alldoctypes():
    """Get and return a tuple of tuples containing the "doctype id" (sdocname) and
       "doctype name" (ldocname) for each action in the WebSubmit database.
       @return: tuple of tuples: (docid,docname)
    """
    q = """SELECT sdocname, CONCAT(ldocname, " [", sdocname, "]") FROM sbmDOCTYPE ORDER BY ldocname ASC"""
    return run_sql(q)

def get_number_doctypes_docid(docid):
    """Return the number of DOCUMENT TYPES found for a given document type id (sdocname).
       @param docid: unique ID of document type whose instances are to be counted.
       @return an integer count of the number of document types in the WebSubmit database for this doctype id.
    """
    q = """SELECT COUNT(sdocname) FROM sbmDOCTYPE where sdocname=%s"""
    return int(run_sql(q, (docid,))[0][0])

def get_number_functions_doctype(doctype):
    """Return the number of FUNCTIONS found for a given DOCUMENT TYPE.
       @param doctype: unique ID of doctype for which the number of functions are to be counted
       @return an integer count of the number of functions in the WebSubmit database for this doctype.
    """
    q = """SELECT COUNT(doctype) FROM sbmFUNCTIONS where doctype=%s"""
    return int(run_sql(q, (doctype,))[0][0])

def get_number_functions_action_doctype(doctype, action):
    """Return the number of FUNCTIONS found for a given ACTION of a given DOCUMENT TYPE.
       @param doctype: unique ID of doctype for which the number of functions are to be counted
       @param action: the action (of the document type "doctype") that owns the functions to be counted
       @return an integer count of the number of functions in the WebSubmit database for this doctype/action.
    """
    q = """SELECT COUNT(doctype) FROM sbmFUNCTIONS where doctype=%s AND action=%s"""
    return int(run_sql(q, (doctype,action))[0][0])

def get_number_categories_doctype(doctype):
    """Return the number of CATEGORIES (used to distinguish between submissions) found for a given DOCUMENT TYPE.
       @param doctype: unique ID of doctype for which submission categories are to be counted
       @return an integer count of the number of categories in the WebSubmit database for this doctype.
    """
    q = """SELECT COUNT(doctype) FROM sbmCATEGORIES where doctype=%s"""
    return int(run_sql(q, (doctype,))[0][0])

def get_number_categories_doctype_category(doctype, categ):
    """Return the number of CATEGORIES (used to distinguish between submissions) found for a given
        DOCUMENT TYPE/CATEGORY NAME. Basically, test to see whether a given category already exists
        for a given document type.
       @param doctype: unique ID of doctype for which the submission category is to be tested
       @param categ: the category ID of the category to be tested for
       @return an integer count of the number of categories in the WebSubmit database for this doctype.
    """
    q = """SELECT COUNT(sname) FROM sbmCATEGORIES where doctype=%s and sname=%s"""
    return int(run_sql(q, (doctype, categ))[0][0])

def get_number_parameters_doctype(doctype):
    """Return the number of PARAMETERS (used by functions) found for a given DOCUMENT TYPE.
       @param doctype: unique ID of doctype whose parameters are to be counted
       @return an integer count of the number of parameters in the WebSubmit database for this doctype.
    """
    q = """SELECT COUNT(name) FROM sbmPARAMETERS where doctype=%s"""
    return int(run_sql(q, (doctype,))[0][0])

def get_number_submissionfields_submissionnames(submission_names):
    """Return the number of SUBMISSION FIELDS found for a given list of submissions.
       A doctype can have several submissions, and each submission can have many fields making up
       its interface. Using this function, the fields owned by several submissions can be counted.
       If the submissions in the list are all owned by one doctype, then it is possible to count the
       submission fields owned by one doctype.
       @param submission_names: unique IDs of all submissions whose fields are to be counted.  If this
        value is a string, it will be classed as a single submission name. Otherwise, a list/tuple of
        strings must be passed - where each string is a submission name.
       @return an integer count of the number of fields in the WebSubmit database for these submission(s)
    """
    q = """SELECT COUNT(subname) FROM sbmFIELD WHERE subname=%s"""
    if type(submission_names) in (str, unicode):
        submission_names = (submission_names,)
    number_submissionnames = len(submission_names)
    if number_submissionnames == 0:
        return 0
    if number_submissionnames > 1:
        for i in range(1,number_submissionnames):
            ## Ensure that we delete all elements used by all submissions for the doctype in question:
            q += """ OR subname=%s"""
    return int(run_sql(q, map(lambda x: str(x), submission_names))[0][0])

def get_doctypeid_doctypes_implementing_action(action):
    q = """SELECT doc.sdocname, CONCAT("[", doc.sdocname, "] ", doc.ldocname) FROM sbmDOCTYPE AS doc """\
        """LEFT JOIN sbmIMPLEMENT AS subm ON """\
        """subm.docname = doc.sdocname """\
        """WHERE subm.actname=%s """\
        """ORDER BY doc.sdocname ASC"""
    return run_sql(q, (action,))


def get_number_submissions_doctype(doctype):
    """Return the number of SUBMISSIONS found for a given document type
       @param doctype: the unique ID of the document type for which submissions are to be counted
       @return: an integer count of the number of submissions owned by this doctype
    """
    q = """SELECT COUNT(subname) FROM sbmIMPLEMENT WHERE docname=%s"""
    return int(run_sql(q, (doctype,))[0][0])

def get_number_submissions_doctype_action(doctype, action):
    """Return the number of SUBMISSIONS found for a given document type/action
       @param doctype: the unique ID of the document type for which submissions are to be counted
       @param actname: the unique ID of the action that the submission implements, that is to be counted
       @return: an integer count of the number of submissions owned by this doctype
    """
    q = """SELECT COUNT(subname) FROM sbmIMPLEMENT WHERE docname=%s and actname=%s"""
    return int(run_sql(q, (doctype, action))[0][0])

def get_number_collection_doctype_entries_doctype(doctype):
    """Return the number of collection_doctype entries found for a given doctype
       @param doctype: the document type for which the collection-doctypes are to be counted
       @return: an integer count of the number of collection-doctype entries found for the
        given document type
    """
    q = """SELECT COUNT(id_father) FROM sbmCOLLECTION_sbmDOCTYPE WHERE id_son=%s"""
    return int(run_sql(q, (doctype,))[0][0])

def get_all_categories_sname_lname_doctype(doctype):
    """Return the short and long names of all CATEGORIES found for a given DOCUMENT TYPE.
       @param doctype: unique ID of doctype for which submission categories are to be counted
       @return a tuple of tuples: (sname, lname)
    """
    q = """SELECT sname, lname FROM sbmCATEGORIES where doctype=%s"""
    return run_sql(q, (doctype,))

def get_all_categories_sname_lname_for_doctype_categsname(doctype, categsname):
    """Return the short and long names of all CATEGORIES found for a given DOCUMENT TYPE.
       @param doctype: unique ID of doctype for which submission categories are to be counted
       @return a tuple of tuples: (sname, lname)
    """
    q = """SELECT sname, lname FROM sbmCATEGORIES where doctype=%s AND sname=%s"""
    return run_sql(q, (doctype, categsname) )

def get_all_submissionnames_doctype(doctype):
    """Get and return a tuple of tuples containing the "submission name" (subname) of all
       submissions for the document type identified by "doctype".
       In other words, get a list of the submissions that document type "doctype" has.
       @param doctype: unique ID of the document type whose submissions are to be retrieved
       @return: tuple of tuples (subname,)
    """
    q = """SELECT subname FROM sbmIMPLEMENT WHERE docname=%s ORDER BY subname ASC"""
    return run_sql(q, (doctype,))

def get_actname_all_submissions_doctype(doctype):
    """Get and return a tuple of tuples containing the "action name" (actname) of all
       submissions for the document type identified by "doctype".
       In other words, get a list of the action IDs of the submissions implemented by document type "doctype".
       @param doctype: unique ID of the document type whose actions are to be retrieved
       @return: tuple of tuples (actname,)
    """
    q = """SELECT actname FROM sbmIMPLEMENT WHERE docname=%s ORDER BY actname ASC"""
    return run_sql(q, (doctype,))

def get_submissiondetails_doctype_action(doctype, action):
    """Get the details of all submissions for a given document type, ordered by the action name.
       @param doctype: details of the document type for which the details of all submissions are to be
        retrieved.
       @return: a tuple containing the details of a submission:
        (subname, docname, actname, displayed, nbpg, cd, md, buttonorder, statustext, level, score,
         stpage, endtext)
    """
    q = """SELECT subname, docname, actname, displayed, nbpg, cd, md, buttonorder, statustext, level, """ \
        """score, stpage, endtxt FROM sbmIMPLEMENT WHERE docname=%s AND actname=%s"""
    return run_sql(q, (doctype, action))

def update_submissiondetails_doctype_action(doctype, action, displayed, buttonorder,
                                            statustext, level, score, stpage, endtxt):
    """Update the details of a submission.
       @param doctype: the document type for which the submission details are to be updated
       @param action: the action ID of the submission to be modified
       @param displayed: displayed on main submission page? (Y/N)
       @param buttonorder: button order
       @param statustext: statustext
       @param level: level
       @param score: score
       @param stpage: stpage
       @param endtxt: endtxt
       @return: an integer error code: 0 for successful update; 1 for update failure.
    """
    numrows_submission = get_number_submissions_doctype_action(doctype, action)
    if numrows_submission == 1:
        ## there is only one row for this submission - can update
        q = """UPDATE sbmIMPLEMENT SET md=CURDATE(), displayed=%s, buttonorder=%s, statustext=%s, level=%s, """\
            """score=%s, stpage=%s, endtxt=%s WHERE docname=%s AND actname=%s"""
        run_sql(q, (displayed,
                    ((str(buttonorder).isdigit() and int(buttonorder) >= 0) and buttonorder) or (None),
                    statustext,
                    level,
                    ((str(score).isdigit() and int(score) >= 0) and score) or (""),
                    ((str(stpage).isdigit() and int(stpage) >= 0) and stpage) or (""),
                    endtxt,
                    doctype,
                    action
                   ) )
        return 0 ## Everything OK
    else:
        ## Everything NOT OK - either multiple rows exist for submission, or submission doesn't exist
        return 1

def update_doctype_details(doctype, doctypename, doctypedescr):
    """Update a document type's details.  In effect the document type name (ldocname) and the description
       are updated, as is the last modification date (md).
       @param doctype: the ID of the document type to be updated
       @param doctypename: the new/updated name of the document type
       @param doctypedescr: the new/updated description of the document type
       @return: Integer error code: 0 = update successful; 1 = update failed
    """
    numrows_doctype = get_number_doctypes_docid(docid=doctype)
    if numrows_doctype == 1:
        ## doctype exists - perform update
        q = """UPDATE sbmDOCTYPE SET ldocname=%s, description=%s, md=CURDATE() WHERE sdocname=%s"""
        run_sql(q, (doctypename, doctypedescr, doctype))
        return 0  ## Everything OK
    else:
        ## Everything NOT OK - either doctype does not exists, or key is duplicated
        return 1


def get_submissiondetails_all_submissions_doctype(doctype):
    """Get the details of all submissions for a given document type, ordered by the action name.
       @param doctype: details of the document type for which the details of all submissions are to be
        retrieved.
       @return: a tuple of tuples, each tuple containing the details of a submission:
        (subname, docname, actname, displayed, nbpg, cd, md, buttonorder, statustext, level, score,
         stpage, endtext)
    """
    q = """SELECT subname, docname, actname, displayed, nbpg, cd, md, buttonorder, statustext, level, """ \
        """score, stpage, endtxt FROM sbmIMPLEMENT WHERE docname=%s ORDER BY actname ASC"""
    return run_sql(q, (doctype,))

def delete_doctype(doctype):
    """Delete a document type's details from the document types table (sbmDOCTYPE).
       Effectively, this means that the document type has been deleted, but this function
       should be called after other functions that delete all of the other components of a
       document type (such as "delete_all_submissions_doctype" to delete the doctype's submissions,
       "delete_all_functions_doctype" to delete its functions, etc.
       @param doctype: the unique ID of the document type to be deleted.
       @return: 0 (ZERO) if doctype was deleted successfully; 1 (ONE) if doctype remains after the
        deletion attempt.
    """
    q = """DELETE FROM sbmDOCTYPE WHERE sdocname=%s"""
    run_sql(q, (doctype,))
    numrows_doctype = get_number_doctypes_docid(doctype)
    if numrows_doctype == 0:
        ## everything OK - deleted this doctype
        return 0
    else:
        ## everything NOT OK - could not delete all entries for this doctype
        ## make a last attempt:
        run_sql(q, (doctype,))
        if get_number_doctypes_docid(doctype) == 0:
            ## everything OK this time - could delete doctype
            return 0
        else:
            ## everything still NOT OK - could not delete the doctype
            return 1

def delete_collection_doctype_entry_doctype(doctype):
    """Delete a document type's entry from the collection-doctype list
       @param doctype: the unique ID of the document type to be deleted from the
        collection-doctypes list
       @return: 0 (ZERO) if doctype was deleted successfully from collection-doctypes list;
        1 (ONE) if doctype remains in the collection-doctypes list after the deletion attempt
    """
    q = """DELETE FROM sbmCOLLECTION_sbmDOCTYPE WHERE id_son=%s"""
    run_sql(q, (doctype,))
    numrows_coll_doctype_doctype = get_number_collection_doctype_entries_doctype(doctype)
    if numrows_coll_doctype_doctype == 0:
        ## everything OK - deleted the document type from the collection-doctype list
        return 0
    else:
        ## everything NOT OK - could not delete the doctype from the collection-doctype list
        ## try once more
        run_sql(q, (doctype,))
        if get_number_collection_doctype_entries_doctype(doctype) == 0:
            ## everything now OK - could delete this time
            return 0
        else:
            ## everything still NOT OK - could not delete
            return 1

def delete_all_submissions_doctype(doctype):
    """Delete all SUBMISSIONS (actions) for a given document type
       @param doctype: the doument type from which the submissions are to be deleted
       @return: 0 (ZERO) if all submissions are deleted successfully; 1 (ONE) if submissions remain after the
        delete has been performed (i.e. all submissions could not be deleted for some reason)
    """
    q = """DELETE FROM sbmIMPLEMENT WHERE docname=%s"""
    run_sql(q, (doctype,))
    numrows_submissionsdoctype = get_number_submissions_doctype(doctype)
    if numrows_submissionsdoctype == 0:
        ## everything OK - no submissions remain for this doctype
        return 0
    else:
        ## everything NOT OK - still submissions remaining for this doctype
        ## make a last attempt to delete them:
        run_sql(q, (doctype,))
        ## last check to see whether submissions remain:
        if get_number_submissions_doctype(doctype) == 0:
            ## Everything OK - all submissions deleted this time
            return 0
        else:
            ## Everything NOT OK - still could not delete the submissions
            return 1

def delete_all_parameters_doctype(doctype):
    """Delete all PARAMETERS (as used by functions) for a given document type
       @param doctype: the doctype for which all function-parameters are to be deleted
       @return: 0 (ZERO) if all parameters are deleted successfully; 1 (ONE) if parameters remain after the
        delete has been performed (i.e. all parameters could not be deleted for some reason)
    """
    q = """DELETE FROM sbmPARAMETERS WHERE doctype=%s"""
    run_sql(q, (doctype,))
    numrows_paramsdoctype = get_number_parameters_doctype(doctype)
    if numrows_paramsdoctype == 0:
        ## Everything OK - no parameters remain for this doctype
        return 0
    else:
        ## Everything NOT OK - still some parameters remaining for doctype
        ## make a last attempt to delete them:
        run_sql(q, (doctype,))
        ## check once more to see if parameters remain:
        if get_number_parameters_doctype(doctype) == 0:
            ## Everything OK - all parameters were deleted successfully this time
            return 0
        else:
            ## still unable to recover - could not delete all parameters
            return 1

def delete_all_functions_foraction_doctype(doctype, action):
    """Delete all FUNCTIONS for a given action, belonging to a given doctype.
       @param doctype: the document type for which the functions are to be deleted
       @param action: the action that owns the functions to be deleted
       @return: 0 (ZERO) if all functions for the doctype/action are deleted successfully;
        1 (ONE) if functions for the doctype/action remain after the delete has been performed (i.e.
        the functions could not be deleted for some reason)
    """
    q = """DELETE FROM sbmFUNCTIONS WHERE doctype=%s AND action=%s"""
    run_sql(q, (doctype,action))
    numrows_functions_actiondoctype = get_number_functions_action_doctype(doctype=doctype, action=action)
    if numrows_functions_actiondoctype == 0:
        ## Everything OK - no functions remain for this doctype/action
        return 0
    else:
        ## Everything NOT OK - still some functions remaining for doctype/action
        ## make a last attempt to delete them:
        run_sql(q, (doctype,action))
        ## check once more to see if functions remain:
        if get_number_functions_action_doctype(doctype) == 0:
            ## Everything OK - all functions for this doctype/action were deleted successfully this time
            return 0
        else:
            ## still unable to recover - could not delete all functions for this doctype/action
            return 1
    

def delete_all_functions_doctype(doctype):
    """Delete all FUNCTIONS for a given document type.
       @param doctype: the document type for which all functions are to be deleted
       @return: 0 (ZERO) if all functions are deleted successfully; 1 (ONE) if functions remain after the
        delete has been performed (i.e. all functions could not be deleted for some reason)
    """
    q = """DELETE FROM sbmFUNCTIONS WHERE doctype=%s"""
    run_sql(q, (doctype,))
    numrows_functionsdoctype = get_number_functions_doctype(doctype)
    if numrows_functionsdoctype == 0:
        ## Everything OK - no functions remain for this doctype
        return 0
    else:
        ## Everything NOT OK - still some functions remaining for doctype
        ## make a last attempt to delete them:
        run_sql(q, (doctype,))
        ## check once more to see if functions remain:
        if get_number_functions_doctype(doctype) == 0:
            ## Everything OK - all functions were deleted successfully this time
            return 0
        else:
            ## still unable to recover - could not delete all functions
            return 1

def clone_submissionfields_from_doctypesubmission_to_doctypesubmission(fromsub, tosub):
    """
    """
    error_code = delete_all_submissionfields_submission(tosub)
    if error_code == 0:
        ## there are no fields for the submission "tosubm" - clone from "fromsub"
        q = """INSERT INTO sbmFIELD (subname, pagenb, fieldnb, fidesc, fitext, level, sdesc, checkn, cd, md, """ \
            """fiefi1, fiefi2) """\
            """(SELECT %s, pagenb, fieldnb, fidesc, fitext, level, sdesc, checkn, CURDATE(), CURDATE(), NULL, NULL """ \
            """FROM sbmFIELD WHERE subname=%s)"""
        ## get number of submission fields for submission fromsub:
        numfields_fromsub = get_number_submissionfields_submissionnames(submission_names=fromsub)
        run_sql(q, (tosub, fromsub))
        ## get number of submission fields for submission tosub (after cloning):
        numfields_tosub = get_number_submissionfields_submissionnames(submission_names=tosub)
        if numfields_fromsub == numfields_tosub:
            ## successful clone
            return 0
        else:
            ## didn't manage to clone all fields - return 2
            return 2
    else:
        ## cannot delete "tosub"s fields - cannot clone - return 1 to signal this
        return 1

def clone_categories_fromdoctype_todoctype(fromdoctype, todoctype):
    """ TODO : docstring
    """
    ## first, if categories exist for "todoctype", delete them
    error_code = delete_all_categories_doctype(todoctype)
    if error_code == 0:
        ## all categories were deleted - now clone those of "fromdoctype"
        ## first, count "fromdoctype"s categories:
        numcategs_fromdoctype = get_number_categories_doctype(fromdoctype)
        ## now perform the cloning:
        q = """INSERT INTO sbmCATEGORIES (doctype, sname, lname) (SELECT %s, sname, lname FROM sbmCATEGORIES WHERE doctype=%s)"""
        run_sql(q, (todoctype, fromdoctype))
        ## get number categories for "todoctype" (should be the same as "fromdoctype" if the cloning was successful):
        numcategs_todoctype = get_number_categories_doctype(todoctype)
        if numcategs_fromdoctype == numcategs_todoctype:
            ## successful clone
            return 0
        else:
            ## did not manage to clone all categories - return 2 to indicate this
            return 2
    else:
        ## cannot delete "todoctype"s categories - return error code of 1 to signal this
        return 1

def clone_functions_foraction_fromdoctype_todoctype(fromdoctype, todoctype, action):
    ## delete all functions that 
    error_code = delete_all_functions_foraction_doctype(doctype=todoctype, action=action)
    if error_code == 0:
        ## all functions for todoctype/action deleted - no clone those of "fromdoctype"
        ## count fromdoctype's functions for the given action
        numrows_functions_action_fromdoctype = get_number_functions_action_doctype(doctype=fromdoctype, action=action)
        ## perform the cloning:
        q = """INSERT INTO sbmFUNCTIONS (doctype, action, function, score, step) (SELECT %s, action, function, """ \
            """score, step FROM sbmFUNCTIONS WHERE doctype=%s AND action=%s)"""
        run_sql(q, (todoctype, fromdoctype, action))
        ## get number of functions for todoctype/action (these have just been cloned these from fromdoctype/action, so
        ## the counts should be the same)
        numrows_functions_action_todoctype = get_number_functions_action_doctype(doctype=todoctype, action=action)
        if numrows_functions_action_fromdoctype == numrows_functions_action_todoctype:
            ## successful clone:
            return 0
        else:
            ## could not clone all functions from fromdoctype/action for todoctype/action
            return 2
    else:
        ## unable to delete "todoctype"'s functions for action
        return 1
    
def get_number_functionparameters_for_action_doctype(action, doctype):
    """Get the number of parameters associated with a given action of a given document type.
       @param action: the action of the doctype, with which the parameters are associated
       @param doctype: the doctype with which the parameters are associated.
       @return: an integer count of the number of parameters associated with the given action
        of the given document type
    """
    q = """SELECT COUNT(DISTINCT(par.name)) FROM sbmFUNDESC AS fundesc """ \
           """LEFT JOIN sbmPARAMETERS AS par ON fundesc.param = par.name """ \
           """LEFT JOIN sbmFUNCTIONS AS func ON par.doctype = func.doctype AND fundesc.function = func.function """ \
           """WHERE par.doctype=%s AND func.action=%s"""
    return int(run_sql(q, (doctype, action))[0][0])

def get_functionparameters_for_action_doctype(action, doctype):
    """Get the details of all function parameter values for a given action of a given doctype.
       @param doctype: the document type with which the parameter values are associated
       @param action: the action (of "doctype") with which the parameter values are associated
       @return: a tuple of tuples, where each tuple represents a parameter/value:
        (parameter name, parameter value, doctype)
    """
    q = """SELECT DISTINCT(par.name), par.value, par.doctype FROM sbmFUNDESC AS fundesc """ \
           """LEFT JOIN sbmPARAMETERS AS par ON fundesc.param = par.name """ \
           """LEFT JOIN sbmFUNCTIONS AS func ON par.doctype = func.doctype AND fundesc.function = func.function """ \
           """WHERE par.doctype=%s AND func.action=%s """\
           """GROUP BY par.name """ \
           """ORDER BY fundesc.function ASC, par.name ASC"""
    return run_sql(q, (doctype, action))

def get_numberparams_doctype_paramname(doctype, paramname):
    """Return a count of the number of rows found for a given parameter of a given doctype.
       @param doctype: the doctype with which the parameter is associated
       @param paramname: the parameter to be counted
       @return: an integer count of the number of times this parameter is found for the document type
        "doctype"
    """
    q = """SELECT COUNT(name) FROM sbmPARAMETERS WHERE doctype=%s AND name=%s"""
    return int(run_sql(q, (doctype, paramname))[0][0])

def get_doctype_docname_descr_cd_md_fordoctype(doctype):
    q = """SELECT sdocname, ldocname, description, cd, md FROM sbmDOCTYPE WHERE sdocname=%s"""
    return run_sql(q, (doctype,))

def get_actions_sname_lname_not_linked_to_doctype(doctype):
    q = """SELECT actn.sactname, CONCAT("[", actn.sactname, "] ", actn.lactname) FROM sbmACTION AS actn """ \
        """LEFT JOIN sbmIMPLEMENT AS subm ON subm.docname=%s AND actn.sactname=subm.actname """ \
        """WHERE subm.actname IS NULL"""
    return run_sql(q, (doctype,))



def insert_parameter_doctype(doctype, paramname, paramval):
    """Insert a new parameter and its value into the parameters table (sbmPARAMETERS) for a given
       document type.
       @param doctype: the document type for which the parameter is to be inserted
       @param paramname:
       @param paramval:
       @return:
    """
    q = """INSERT INTO sbmPARAMETERS (doctype, name, value) VALUES (%s, %s, %s)"""
    numrows_paramdoctype = get_numberparams_doctype_paramname(doctype=doctype, paramname=paramname)
    if numrows_paramdoctype == 0:
        ## go ahead and insert
        run_sql(q, (doctype, paramname, paramval))
        return 0 ## Everything is OK
    else:
        return 1 ## Everything NOT OK - this param already exists, so not inserted
        

def clone_functionparameters_foraction_fromdoctype_todoctype(fromdoctype, todoctype, action):
    ## get a list of all function-parameters/values for fromdoctype/action
    functionparams_action_fromdoctype = get_functionparameters_for_action_doctype(action=action, doctype=fromdoctype)
    numrows_functionparams_action_fromdoctype = len(functionparams_action_fromdoctype)
    ## for each param, test whether "todoctype" already has a value for it, and if not, clone it:
    for docparam in functionparams_action_fromdoctype:
        docparam_name = docparam[0]
        docparam_val = docparam[1]
        insert_parameter_doctype(doctype=todoctype, paramname=docparam_name, paramval=docparam_val)
    numrows_functionparams_action_todoctype = get_number_functionparameters_for_action_doctype(action=action, doctype=todoctype)
    if numrows_functionparams_action_fromdoctype == numrows_functionparams_action_todoctype:
        ## All is OK - the action on both document types has the same number of parameters
        return 0
    else:
        ## everything NOT OK - the action on both document types has a different number of parameters
        ## probably some could not be cloned. return 2 to signal that cloning not 100% successful
        return 2

def update_doctype_details(doctype, doctypename, doctypedescr):
    """Update a document type's details.  In effect the document type name (ldocname) and the description
       are updated, as is the last modification date (md).
       @param doctype: the ID of the document type to be updated
       @param doctypename: the new/updated name of the document type
       @param doctypedescr: the new/updated description of the document type
       @return: Integer error code: 0 = update successful; 1 = update failed
    """
    numrows_doctype = get_number_doctypes_docid(docid=doctype)
    if numrows_doctype == 1:
        ## doctype exists - perform update
        q = """UPDATE sbmDOCTYPE SET ldocname=%s, description=%s, md=CURDATE() WHERE sdocname=%s"""
        run_sql(q, (doctypename, doctypedescr, doctype))
        return 0  ## Everything OK
    else:
        ## Everything NOT OK - either doctype does not exists, or key is duplicated
        return 1

def update_category_description_doctype_categ(doctype, categ, categdescr):
    """Update the description of the category "categ", belonging to the document type "doctype".
        Set the description of this category equal to "categdescr".
       @param doctype: the document type for which the given category description is to be updated
       @param categ: the name/ID of the category whose description is to be updated
       @param categdescr: the new description for the category
       @return: integer error code (0 is OK, 1 is BAD update)
    """
    numrows_category_doctype = get_number_categories_doctype_category(doctype=doctype, categ=categ)
    if numrows_category_doctype == 1:
        ## perform update of description
        q = """UPDATE sbmCATEGORIES SET lname=%s WHERE doctype=%s AND sname=%s"""
        run_sql(q, (categdescr, doctype, categ))
        return 0 ## Everything OK
    else:
        return 1 ## Everything not OK: either no rows, or more than 1 row for category

def insert_category_doctype(doctype, categ, categdescr):
    q = """INSERT INTO sbmCATEGORIES (doctype, sname, lname) VALUES (%s, %s, %s)"""
    ## get count of rows for "doctype"/"categ"
    numrows_category_doctype = get_number_categories_doctype_category(doctype=doctype, categ=categ)
    if numrows_category_doctype == 0:
        ## "categ" does not exist for "doctype" - can insert:
        run_sql(q, (doctype, categ, categdescr))
        return 0  ## everything OK
    else:
        ## category already exists - cannot insert
        return 1

def delete_category_doctype(doctype, categ):
    """Delete a given CATEGORY from a document type.
       @param doctype: the document type from which the category is to be deleted
       @param categ: the name/ID of the category to be deleted from doctype
       @return: 0 (ZERO) if the category was successfully deleted from this doctype; 1 (ONE) not;
    """
    q = """DELETE FROM sbmCATEGORIES WHERE doctype=%s and sname=%s"""
    run_sql(q, (doctype, categ))
    ## check to see whether this category still exists for the doctype:
    numrows_categorydoctype = get_number_categories_doctype_category(doctype=doctype, categ=categ)
    if numrows_categorydoctype == 0:
        ## Everything OK - category deleted
        return 0
    else:
        ## Everything NOT OK - category still present
        ## make a last attempt to delete it:
        run_sql(q, (doctype, categ))
        ## check once more to see if category remains:
        if get_number_categories_doctype_category(doctype=doctype, categ=categ) == 0:
            ## Everything OK - category was deleted successfully this time
            return 0
        else:
            ## still unable to recover - could not delete category
            return 1

def delete_all_categories_doctype(doctype):
    """Delete all CATEGORIES for a given document type.
       @param doctype: the document type for which all submission-categories are to be deleted
       @return: 0 (ZERO) if all categories for this doctype are deleted successfully; 1 (ONE) if categories
        remain after the delete has been performed (i.e. all categories could not be deleted for some reason)
    """
    q = """DELETE FROM sbmCATEGORIES WHERE doctype=%s"""
    run_sql(q, (doctype,))
    numrows_categoriesdoctype = get_number_categories_doctype(doctype)
    if numrows_categoriesdoctype == 0:
        ## Everything OK - no submission categories remain for this doctype
        return 0
    else:
        ## Everything NOT OK - still some submission categories remaining for doctype
        ## make a last attempt to delete them:
        run_sql(q, (doctype,))
        ## check once more to see if categories remain:
        if get_number_categories_doctype(doctype) == 0:
            ## Everything OK - all categories were deleted successfully this time
            return 0
        else:
            ## still unable to recover - could not delete all categories
            return 1

def delete_all_submissionfields_submission(subname):
    """Delete all FIELDS (i.e. field elements used on a document type's submission pages - these are the
       instances of WebSubmit elements throughout the system) for a given submission. This means delete all
       fields used by a given action of a given doctype.
       @param subname: the unique name/ID of the submission from which all field elements are to be deleted.
       @return: 0 (ZERO) if all submission fields could be deleted for the given submission; 1 (ONE) if some
        fields remain after the deletion was performed (i.e. for some reason it was not possible to delete
        all fields for the submission).
    """
    q = """DELETE FROM sbmFIELD WHERE subname=%s"""
    run_sql(q, (subname,))
    numrows_submissionfields_subname = get_number_submissionfields_submissionnames(subname)
    if numrows_submissionfields_subname == 0:
        ## all submission fields have been deleted for this submission
        return 0
    else:
        ## all fields not deleted. try once more:
        run_sql(q, (subname,))
        numrows_submissionfields_subname = get_number_submissionfields_submissionnames(subname)
        if numrows_submissionfields_subname == 0:
            ## OK this time - all deleted
            return 0
        else:
            ## still unable to delete all submission fields for this submission - give up
            return 1

def delete_all_submissionfields_doctype(doctype):
    """Delete all FIELDS (i.e. field elements used on a document type's submission pages - these are the instances
       of "WebSubmit Elements" throughout the system).
       @param doctype: the document type for which all submission fields are to be deleted
       @return: 0 (ZERO) if all submission fields for this doctype are deleted successfully; 1 (ONE) if submission-
        fields remain after the delete has been performed (i.e. all fields could not be deleted for some reason)
    """
    all_submissions_doctype = get_all_submissionnames_doctype(doctype=doctype)
    number_submissions_doctype = len(all_submissions_doctype)
    if number_submissions_doctype > 0:
        ## for each of the submissions, delete the submission fields
        q = """DELETE FROM sbmFIELD WHERE subname=%s"""
        if number_submissions_doctype > 1:
            for i in range(1,number_submissions_doctype):
                ## Ensure that we delete all elements used by all submissions for the doctype in question:
                q += """ OR subname=%s"""
        run_sql(q, map(lambda x: str(x[0]), all_submissions_doctype))
        ## get a count of the number of fields remaining for these submissions after deletion.
        numrows_submissions = get_number_submissionfields_submissionnames(submission_names=map(lambda x: str(x[0]), all_submissions_doctype))
        if numrows_submissions == 0:
            ## Everything is OK - no submission fields left for this doctype
            return 0
        else:
            ## Everything is NOT OK - some submission fields remain for this doctype - try one more time to delete them:
            run_sql(q, map(lambda x: str(x[0]), all_submissions_doctype))
            numrows_submissions = get_number_submissionfields_submissionnames(submission_names=map(lambda x: str(x[0]), all_submissions_doctype))
            if numrows_submissions == 0:
                ## everything OK this time
                return 0
            else:
                ## still could not delete all fields
                return 1
    else:
        ## there were no submissions to delete - therefore there should be no submission fields
        ## cannot check, so just return OK
        return 0

def delete_submissiondetails_doctype(doctype, action):
    """Delete a SUBMISSION (action) for a given document type
       @param doctype: the doument type from which the submission is to be deleted
       @param action: the action name for the submission that is to be deleted
       @return: 0 (ZERO) if all submissions are deleted successfully; 1 (ONE) if submissions remain after the
        delete has been performed (i.e. all submissions could not be deleted for some reason)
    """
    q = """DELETE FROM sbmIMPLEMENT WHERE docname=%s AND actname=%s"""
    run_sql(q, (doctype, action))
    numrows_submissiondoctype = get_number_submissions_doctype_action(doctype, action)
    if numrows_submissiondoctype == 0:
        ## everything OK - the submission has been deleted
        return 0
    else:
        ## everything NOT OK - could not delete submission. retry.
        run_sql(q, (doctype, action))
        if get_number_submissions_doctype_action(doctype, action) == 0:
            return 0  ## success this time
        else:
            return 1  ## still unable to delete doctype

def insert_doctype_details(doctype, doctypename, doctypedescr):
    """Insert the details of a new document type into WebSubmit.
       @param doctype: the ID code of the new document type
       @param doctypename: the name of the new document type
       @param doctypedescr: the description of the new document type
       @return: integer (0/1). 0 when insert performed; 1 when doctype already existed, so no insert performed.
    """
    numrows_doctype = get_number_doctypes_docid(doctype)
    if numrows_doctype == 0:
        # insert new document type:
        q = """INSERT INTO sbmDOCTYPE (ldocname, sdocname, cd, md, description) VALUES (%s, %s, CURDATE(), CURDATE(), %s)"""
        run_sql(q, (doctypename, doctype, (doctypedescr != "" and doctypedescr) or (None)))
        return 0 # Everything is OK
    else:
        return 1 # Everything not OK: rows may already exist for document type doctype

def insert_submission_details_clonefrom_submission(addtodoctype, action, clonefromdoctype):
    numrows_submission_addtodoctype = get_number_submissions_doctype_action(addtodoctype, action)
    if numrows_submission_addtodoctype == 0:
        ## submission does not exist for "addtodoctype" - insert it
        q = """INSERT INTO sbmIMPLEMENT (docname, actname, displayed, subname, nbpg, cd, md, buttonorder, statustext, level, """ \
            """score, stpage, endtxt) (SELECT %s, %s, displayed, %s, nbpg, CURDATE(), CURDATE(), IFNULL(buttonorder, 100), statustext, level, """ \
            """score, stpage, endtxt FROM sbmIMPLEMENT WHERE docname=%s AND actname=%s LIMIT 1)"""
        run_sql(q, (addtodoctype, action, "%s%s" % (action, addtodoctype), clonefromdoctype, action))
        return 0 ## cloning executed - everything OK
    else:
        ## submission already exists for "addtodoctype" - cannot insert it again!
        return 1

def insert_submission_details(doctype, action, displayed, nbpg, buttonorder, statustext, level, score, stpage, endtext):
    """Insert the details of a new submission of a given document type into WebSubmit.
       @param doctype: the doctype ID (string)
       @param action: the action ID (string)
       @param displayed: the value of displayed (char)
       @param nbpg: the value of nbpg (integer)
       @param buttonorder: the value of buttonorder (integer)
       @param statustext: the value of statustext (string)
       @param level: the value of level (char)
       @param score: the value of score (integer)
       @param stpage: the value of stpage (integer)
       @param endtext: the value of endtext (string)
       @return: integer (0/1). 0 when insert performed; 1 when submission already existed for doctype, so no insert performed.
    """
    numrows_submission = get_number_submissions_doctype_action(doctype, action)
    if numrows_submission == 0:
        ## this submission does not exist for doctype - insert it
        q = """INSERT INTO sbmIMPLEMENT (docname, actname, displayed, subname, nbpg, cd, md, buttonorder, statustext, level, """ \
            """score, stpage, endtxt) VALUES(%s, %s, %s, %s, %s, CURDATE(), CURDATE(), %s, %s, %s, %s, %s, %s)"""
        run_sql(q, (doctype,
                    action,
                    displayed,
                    "%s%s" % (action, doctype),
                    ((str(nbpg).isdigit() and int(nbpg) >= 0) and nbpg) or ("0"),
                    ((str(buttonorder).isdigit() and int(buttonorder) >= 0) and buttonorder) or (None),
                    statustext,
                    level,
                    ((str(score).isdigit() and int(score) >= 0) and score) or (""),
                    ((str(stpage).isdigit() and int(stpage) >= 0) and stpage) or (""),
                    endtext
                   ) )
        return 0  ## insert performed
    else:
        ## this submission already exists for the doctype - do not insert it
        return 1



