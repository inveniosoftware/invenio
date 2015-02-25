# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2009, 2010, 2011 CERN.
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

"""The Data Base layer for the WebSubmit module"""

__revision__ = "$Id$"

from invenio.legacy.dbquery import run_sql


def get_storage_directory_of_action(action):
    """Given the (short) name of an action (e.g. SBI, MBI, etc), query
       the database to retrieve the name of the directory used by this
       action for the storage of files during submissions.
       @param action: (string) - the (short) name of the action.
       @return: (string -OR- None) - In the case that the action exists,
        return the directory name as a string; In the case that the
        action does not exist, return a None value.
    """
    ## Initialise directory to None for case in which action doesn't exist:
    directory = None
    ## Query the DB:
    qstr = """SELECT dir FROM sbmACTION WHERE sactname=%s LIMIT 1"""
    qres = run_sql(qstr, (action,))
    if len(qres) > 0:
        ## The action exists - set the correct value of directory:
        directory = qres[0][0]
    ## return the directory name (or None, if no action was found)
    return directory

def get_longname_of_doctype(doctype):
    """Given the ID of a document type (doctype), query the database to
       retrieve the doctype's long name.
       @param doctype: (string) - the ID of the document type.
       @return: (string -OR- None) - In the case that the document type exists,
        return the name as a string; In the case that the document type does
        not exist, return a None value.
    """
    ## Initialise the document-type's long-name to None for case in which
    ## document-type doesn't exist:
    ldocname = None
    ## Query the DB:
    qstr = """SELECT ldocname FROM sbmDOCTYPE WHERE sdocname=%s LIMIT 1"""
    qres = run_sql(qstr, (doctype,))
    if len(qres) > 0:
        ## The doctype exists - get the doctype long-name:
        ldocname = qres[0][0]
    ## return the doctype long-name (or None if no doctype was found):
    return ldocname


def get_longname_of_action(action):
    """Given the (short) name of an action (e.g. SBI, MBI, etc), query
       the database to retrieve the action's long name.
       @param action: (string) - the ID of the document type.
       @return: (string -OR- None) - In the case that the action exists,
        return the name as a string; In the case that the action does
        not exist, return a None value.
    """
    ## Initialise the action's long-name to None for case in which
    ## action doesn't exist:
    lactname = None
    ## Query the DB:
    qstr = """SELECT lactname FROM sbmACTION WHERE sactname=%s LIMIT 1"""
    qres = run_sql(qstr, (action,))
    if len(qres) > 0:
        ## The action exists - get its long-name:
        lactname = qres[0][0]
    ## return the action long-name (or None, if no action was found)
    return lactname


def doctype_has_submission(doctype, action):
    """Determine whether or not a doctype has a given submission.
       A submission (i.e. an action of a document type) is identified
       by the document type ID and the action ID.
       @param doctype: (string) - the ID of the document type.
       @param action:  (string) - the ID of the action.
       @return: (integer) - 0 if the given submission does not exist
        in WebSubmit; 1 if the submission exists.
    """
    exists = 0 ## Flag indicating the submission's existence

    ## Execute the query to count the number of rows for this submission:
    qstr = """SELECT count(docname) FROM sbmIMPLEMENT """ \
           """WHERE docname=%s AND actname=%s"""
    qres = run_sql(qstr, (doctype, action))

    if len(qres) > 0:
        ## Get the number of rows found for this submission:
        num_submissions = qres[0][0]
        try:
            num_submissions = int(num_submissions)
        except (ValueError, TypeError):
            ## Unexpected result. Assume that the submission doesn't exist
            ## for this document type:
            num_submissions = 0

        if num_submissions > 0:
            ## The submission exists for this document type.
            ## Set the return-flag.
            exists = 1

    ## return submission-exists flag:
    return exists


def get_num_pages_of_submission(submission):
    """Given the ID of a submission (e.g. SBITEXT, MBIPICT, etc), query
       the database to retrieve the number of pages making up the
       submission.
       @param submission: (string) - the ID of the submission.
       @return: (integer -OR- None) - In the case that the submission
        exists, and the number of pages stored for it is a valid integer,
        return the number of pages as an integer; In the case that the
        submission doesn't exist, or that the number of pages for a
        submission is not a valid integer (could be NULL, for example),
        return None.
    """
    ## Initialise the number of pages to None
    numpages = None
    ## Query the DB:
    qstr = """SELECT nbpg FROM sbmIMPLEMENT WHERE subname=%s LIMIT 1"""
    qres = run_sql(qstr, (submission,))
    if len(qres) > 0:
        ## The submission exists - set the correct value of directory:
        numpages = qres[0][0]
        try:
            numpages = int(qres[0][0])
        except (ValueError, TypeError):
            ## The number of pages was not an integer
            numpages = None
    ## return the number of pages (or None, if no submission was found or
    ## the number of pages was not a valid integer):
    return numpages


def get_parameter_value_for_doctype(doctype, paramname):
    """Get the value for a given parameter for a given document type.
       @param doctype: (string) - the ID of the document type.
       @param paramname: (string) - the name of the parameter for
        which the value is to be retrieved.
       @return: (string -OR- None) - The value of the parameter if it
        could be found in the sbmPARAMETERS table for this document-
        type; None if there was no value.
    """
    param_value = None
    qstr = """SELECT value FROM sbmPARAMETERS """ \
           """WHERE doctype=%s and name=%s """ \
           """LIMIT 1"""
    qres = run_sql(qstr, (doctype, paramname))
    if len(qres) > 0:
        ## The parameter exists for this doctype - get its value:
        param_value = qres[0][0]
    return param_value


def submission_exists_in_log(doctype, action, subm_id, email):
    """Given a doctype, action, submission-id and email-address,
       check the submission-log in the database to determine
       whether or not the submission actually exists.
       If it does (i.e. 1 or more rows are found in the log for
       it, return 1; else return 0.
       @param doctype: (string) - the ID of the document type on
        which the submission is performed.
       @param action: (string) - the ID of the action for this
        submission.
       @param subm_id: (string) - the ID of the submission. Also
        sometimes referred to as the access-number for the
        submission.
       @param email: (string) - the email address of the owner
        of the submission (i.e. the 'submitter').
       @return: (integer) - 1 if the submission exists in the
        submission log; 0 if it does not exist.
    """
    ## reset flag indicating whether or not a submission exists:
    subm_exists = 0
    ## Get the number of rows existing in the submission-log
    ## for this submission:
    qstr = """SELECT count(id) FROM sbmSUBMISSIONS """ \
           """WHERE doctype=%s AND action=%s """ \
           """AND id=%s AND email=%s"""
    qres = run_sql(qstr, (doctype, action, subm_id, email))
    if len(qres) > 0:
        num_submissions = qres[0][0]
        try:
            num_submissions = int(num_submissions)
        except (ValueError, TypeError):
            ## Bad value for number of submissions, set as 0
            num_submissions = 0
        if num_submissions > 0:
            ## The submission exists in the log:
            subm_exists = 1
    ## return submission-exists flag:
    return subm_exists


def log_new_pending_submission(doctype, action, subm_id, email):
    """Insert a new submission into the submission-log.
       The submission record in the log is identified by:
         + doctype
         + action
         + access-number (submission ID)
         + email (of submitter)
       @param doctype: (string) - the ID of the document type.
       @param action: (string) - the ID of the type of action performed.
       @param subm_id: (string) - the access-number (or submission-
        instance ID).
       @param email: (string) - the email address of the submitter.
       @return: (integer) - the number of rows inserted by the query.
    """
    ## Insert the details of the new submission into the DB:
    qstr = """INSERT INTO sbmSUBMISSIONS """ \
           """(email, doctype, action, status, id, reference, cd, md) """ \
           """VALUES (%s, %s, %s, 'pending', %s, '', NOW(), NOW())"""
    qres = run_sql(qstr, (email, doctype, action, subm_id))
    ## return the number of rows inserted:
    if qres is None:
        ## Database in real only mode?
        return 0
    return int(qres)


def log_new_completed_submission(doctype, action, subm_id, email, reportnum):
    """Insert a new submission into the submission-log.
       The submission record in the log is identified by:
         + doctype
         + action
         + access-number (submission ID)
         + email (of submitter)
       @param doctype: (string) - the ID of the document type.
       @param action: (string) - the ID of the type of action performed.
       @param subm_id: (string) - the access-number (or submission-
        instance ID).
       @param email: (string) - the email address of the submitter.
       @param reportnum: (string) - the report number associated with
        the submission.
       @return: (integer) - the number of rows inserted by the query.
    """
    ## Insert the details of the new submission into the DB:
    qstr = """INSERT INTO sbmSUBMISSIONS """ \
           """(email, doctype, action, status, id, reference, cd, md) """ \
           """VALUES (%s, %s, %s, 'finished', %s, %s, NOW(), NOW())"""
    qres = run_sql(qstr, (email, doctype, action, subm_id, reportnum))
    ## return the number of rows inserted:
    return int(qres)


def update_submission_modified_date_in_log(doctype, action, subm_id, email):
    """Update the modification date of a submission in the log.
       The date is set equal to the current-date and time.
       @param doctype: (string) - the ID of the document type.
       @param action: (string) - the ID of the type of action performed.
       @param subm_id: (string) - the access-number (or submission-
        instance ID).
       @param email: (string) - the email address of the submitter.
       @return: None
    """
    ## Update the modification date to NOW() in the log for the submission:
    qstr = """UPDATE sbmSUBMISSIONS SET md=NOW() """ \
           """WHERE doctype=%s AND action=%s AND id=%s AND email=%s"""
    run_sql(qstr, (doctype, action, subm_id, email))


def update_submission_reference_in_log(doctype, subm_id, email, reference):
    """Update the reference number for a submission in the submission-log.
       @param doctype: (string) - the ID of the document type.
       @param subm_id: (string) - the access-number (or submission-
        instance ID).
       @param email: (string) - the email address of the submitter.
       @param reference: (string) - the new value for the submission's reference.
       @return: None
    """
    ## Update the reference for the submission in the log:
    qstr = """UPDATE sbmSUBMISSIONS SET reference=%s """ \
           """WHERE doctype=%s AND id=%s AND email=%s"""
    run_sql(qstr, (reference, doctype, subm_id, email))


def update_submission_reference_and_status_in_log(doctype,
                                                  action,
                                                  subm_id,
                                                  email,
                                                  reference,
                                                  status="finished"):
    """Update the modification date (to NOW()), the reference, and the
       status of a submission in the log.
       @param doctype: (string) - the ID of the document type.
       @param action: (string) - the ID of the type of action performed.
       @param subm_id: (string) - the access-number (or submission-
        instance ID).
       @param email: (string) - the email address of the submitter.
       @param reference: (string) - the new value for the submission's reference.
       @param status: (string) - the new status for the submission. NOTE:
        DEFAULTS TO 'finished'.
       @return: None
    """
    qstr = """UPDATE sbmSUBMISSIONS """ \
           """SET md=NOW(), reference=%s, status=%s """ \
           """WHERE doctype=%s AND action=%s AND id=%s AND email=%s"""
    run_sql(qstr, (reference, status, doctype, action, subm_id, email))


def get_form_fields_on_submission_page(subname, pagenum):
    """Get the details of all form fields as they appear on the
       current page of the current submission.
       @param subname: (string) - the name of the submission (e.g.
        SBITEXT).
       @param pagenum: (string) - the page-number of the submission
        for which the field details are to be retrieved.
       @return: (tuple of tuples) - each tuple is a row giving
        details of a submission form-field:
        (subname, pagenb, fieldnb, fidesc, fitext, level, sdesc,
         checkn, cd, md, fiefi1, fiefi2)
    """
    qstr = """SELECT subname, pagenb, fieldnb, fidesc, fitext, """ \
           """level, sdesc, checkn, cd, md, fiefi1, fiefi2 """ \
           """FROM sbmFIELD WHERE subname=%s AND pagenb=%s """ \
           """ORDER BY fieldnb"""
    qres = run_sql(qstr, (subname, pagenum))
    return qres


def get_element_description(element):
    """Get the description details of a particular submission
       form element.
       @param element: (string) - the name of the element.
       @return: (tuple -OR- None) - containing the details of the
        element. (name, alephcode, marccode, type, size, rows, cols,
         maxlength, val, fidesc, cd, md, modifytext, fddfi2);
         OR None if the field cannot be found.
    """
    element_descr = None
    qstr = """SELECT name, alephcode, marccode, type, size, """ \
           """rows, cols, maxlength, val, fidesc, cd, md, """ \
           """modifytext, fddfi2 """ \
           """FROM sbmFIELDDESC """ \
           """WHERE name=%s LIMIT 1"""
    qres = run_sql(qstr, (element,))
    if len(qres) > 0:
        ## Element was found - get the first row:
        element_descr = qres[0]
    ## Return the tuple of details of the form-element
    return element_descr


def get_element_check_description(check):
    """Get the desciption of a given JavaScript form-field check.
       @param check: (string) - the name of the check for which the
        description is to be retrieved.
       @return: (string -OR- None) - if the check exists, its
        description will be returned; If not, None is returned.
    """
    check_descr = None
    qstr = """SELECT chdesc FROM sbmCHECKS WHERE chname=%s LIMIT 1"""
    qres = run_sql(qstr, (check,))
    if len(qres) > 0:
        ## Check exists:
        check_descr = qres[0][0]
    ## Return the check description:
    return check_descr


def get_form_fields_not_on_submission_page(subname, pagenum):
    """Get the details of all form fields (for the current submission)
       that are NOT on the current submission page.
       @param subname: (string) - the name of the submission (e.g.
        SBITEXT).
       @param pagenum: (string) - the page-number of the submission
        for which the field details are to be retrieved.
       @return: (tuple of tuples) - each tuple is a row giving
        details of a submission form-field:
        (subname, pagenb, fieldnb, fidesc, fitext, level, sdesc,
         checkn, cd, md, fiefi1, fiefi2)
    """
    qstr = """SELECT subname, pagenb, fieldnb, fidesc, fitext, """ \
           """level, sdesc, checkn, cd, md, fiefi1, fiefi2 """ \
           """FROM sbmFIELD WHERE subname=%s AND pagenb !=%s"""
    qres = run_sql(qstr, (subname, pagenum))
    return qres


def function_step_is_last(doctype, action, step):
    """Given a function step, determine whether it is the last step
       for the functions of a given submission.
       @param doctype: (string) - the ID of the document type.
       @param action: (string) - the ID of the action.
       @param step: (integer) - the step number to be tested
        for.
       @return: (integer) - 1 if this is the last step for the
        functions of the submission; 0 if not.
    """
    last_step = 1
    qstr = """SELECT step FROM sbmFUNCTIONS """ \
           """WHERE action=%s AND doctype=%s AND step > %s"""
    qres = run_sql(qstr, (action, doctype, step))
    if len(qres) > 0:
        ## Rows were returned. This means that this is not the last-step:
        last_step = 0
    return last_step


def get_collection_children_of_submission_collection(collection_id):
    """Get the collection IDs of all 'collection' children of a
       given collection.
       @param collection_id: (integer) the ID of the parent collection
        for which collection-children are to be retrieved.
       @return: (tuple) of tuples. Each tuple is a row containing the collection
        ID of a 'collection' child of the given parent collection.
    """
    ## query to retrieve IDs of collections attached to a given collection:
    qstr = """SELECT id_son FROM sbmCOLLECTION_sbmCOLLECTION """ \
           """WHERE id_father=%s ORDER BY catalogue_order ASC"""
    qres = run_sql(qstr, (collection_id,))
    return qres


def get_submission_collection_name(collection_id):
    """Get the name of a given submission-collection.
       @param collection_id: (string) - the ID of the collection
        for which the details are to be retrieved.
       @return: (string -OR- None) - If a collection exists for
        the given collection-id, the name of that collection will be
        returned as a string; otherwise, None is returned.
    """
    collection_name = None
    qstr = """SELECT name FROM sbmCOLLECTION """ \
           """WHERE id=%s LIMIT 1"""
    qres  = run_sql(qstr, (collection_id,))
    if len(qres) > 0:
        ## Get the name:
        collection_name = qres[0][0]
    return collection_name


def get_doctype_children_of_submission_collection(collection_id):
    """Get the doctype IDs of all 'doctype' children of
       a given collection.
       @param collection_id: (integer) the ID of the parent collection
        for which doctype-children are to be retrieved.
       @return: (tuple) of tuples. Each tuple is a row containing the collection
        ID of a 'doctype' child of the given parent collection.
    """
    qstr = """SELECT id_son """ \
           """FROM sbmCOLLECTION_sbmDOCTYPE """ \
           """WHERE id_father=%s """ \
           """ORDER BY catalogue_order ASC"""
    qres = run_sql(qstr, (collection_id,))
    return qres


def get_categories_of_doctype(doctype):
    """Get the categories of a given document type, ordered
       by score and long-name.
       @param doctype: (string) - the ID of the document type for which
        the categories are to be retrieved.
       @return: (tuple) of tuples, where each tuple contains the details
        of a given category: (sname, lname, score).
    """
    qstr = """SELECT sname, lname, score FROM sbmCATEGORIES """ \
           """WHERE doctype=%s """ \
           """ORDER BY score ASC, lname ASC"""
    qres = run_sql(qstr, (doctype,))
    return qres


def get_doctype_details(doctype):
    """Get the details of a given document type.
       @param doctype: (string) - the document type for which details
        are to be retrieved.
       @return: (tuple -OR- None) - If the document type exists, a tuple
        containing its details is returned:
          (ldocname, sdocname, cd, md, description); if not, None is
        returned.
    """
    doctype_details = None
    qstr = """SELECT ldocname, sdocname, cd, md, description """ \
           """FROM sbmDOCTYPE """ \
           """WHERE sdocname=%s """ \
           """LIMIT 1"""
    qres = run_sql(qstr, (doctype,))
    if len(qres) > 0:
        doctype_details = qres[0]
    return doctype_details


def get_actions_on_submission_page_for_doctype(doctype):
    """Given a document-type ID, get a list of the actions
       (action-IDs) that are on that document-type's
       submission page, ordered by the button-order.
       @param doctype: (string) - the ID of the document type.
       @return: (tuple) of tuples, each containing the action ID
        of an action that should appear as a button on the
        document type's submission page.
    """
    qstr = """SELECT actname FROM sbmIMPLEMENT """ \
           """WHERE docname=%s AND displayed='Y' """ \
           """ORDER BY buttonorder"""
    qres = run_sql(qstr, (doctype,))
    return qres


def get_action_details(action):
    """Get the details of a given action.
       @param action: (string) - the ID of the given action.
       @return: (tuple -OR- None) - If the action exists in the DB,
        a tuple containing its details is returned:
        (lactname, dir, cd, md, actionbutton, statustext); If no
        details were found for the action, None is returned.
    """
    action_details = None
    qstr = """SELECT lactname, dir, cd, md, actionbutton, statustext """ \
           """FROM sbmACTION """ \
           """WHERE sactname=%s"""
    qres = run_sql(qstr, (action,))
    if len(qres) > 0:
        action_details = qres[0]
    return action_details


def get_parameters_of_function(function):
    """Get the names of all parameters of a given function.
       @param function: (string) - the name of the function.
       @return: (tuple) of tuples - each tuple containing the
        name of a given parameter.
    """
    qstr = """SELECT param FROM sbmFUNDESC """ \
           """WHERE function=%s"""
    qres = run_sql(qstr, (function,))
    return qres


def get_details_of_submission(doctype, action):
    """Get the details of a given submission for a given
       document type.
       @param doctype: (string) - the ID of the document type.
       @param action: (string) - the ID of the given action.
       @return: (tuple -OR- None) - in the case that the
        submission exists for the given document type, return
        a tuple containing its details:
        (docname, actname, displayed, subname, nbpg, cd, md,
         buttonorder, statustext, level, score, stpage, endtxt);
        In the case that the submission could not be found in
        the DB, return None.
    """
    submission_details = None
    qstr = """SELECT docname, actname, displayed, subname, """ \
           """nbpg, cd, md, buttonorder, statustext, level, """ \
           """score, stpage, endtxt """ \
           """FROM sbmIMPLEMENT """ \
           """WHERE docname=%s AND actname=%s LIMIT 1"""
    qres = run_sql(qstr, (doctype, action))
    if len(qres) > 0:
        submission_details = qres[0]
    return submission_details


def get_functions_for_submission_step(doctype, action, step):
    """Get the function names and scores of all functions within a
       given step of a given submission of a given document-type.
       The functions are returned in ascending order of score.
       @param doctype: (string) - the document type ID.
       @param action: (string) - the action ID.
       @param step: (integer) - the step number.
       @return: (tuple) - the details of each function within the
        given step: (function-name, score)
    """
    qstr = """SELECT function, score """ \
           """FROM sbmFUNCTIONS """ \
           """WHERE action=%s AND doctype=%s AND step=%s """ \
           """ORDER BY score ASC"""
    qres = run_sql(qstr, (action, doctype, step))
    return qres


def get_submissions_at_level_X_with_score_above_N(doctype, level, score_N):
    """Get the details of a given submission for a given
       document type.
       @param doctype: (string) - the ID of the document type.
       @return: (tuple) of tuples - each tuple containing the
        details of a given submission:
        (docname, actname, displayed, subname, nbpg, cd, md,
         buttonorder, statustext, level, score, stpage, endtxt);
    """
    qstr = """SELECT docname, actname, displayed, subname, """ \
           """nbpg, cd, md, buttonorder, statustext, level, """ \
           """score, stpage, endtxt """ \
           """FROM sbmIMPLEMENT """ \
           """WHERE docname=%s AND level !='0' AND level=%s AND score > %s """ \
           """ORDER BY score ASC"""
    qres = run_sql(qstr, (doctype, level, score_N))
    return qres


def submission_is_finished(doctype, action, subm_id, email):
    """Determine whether a submission is finished. This is done
       by checking in the submission log for a submission with
       the id of the current submission, and the status
       'finished'.
       @param doctype: (string) - the ID of the document type.
       @param action: (string) - the ID of the action.
       @param subm_id: (string) - the ID of the submission in the
        submission log (i.e. its access-number).
       @param email: (string) - the email address of the submitter.
       @return: (integer) - 0 if the submission is not found with
        a status of 'finished' in the log; 1 if it is (and is therefore
        a finished submission).
    """
    submission_finished = 0
    qstr = """SELECT id FROM sbmSUBMISSIONS """ \
           """WHERE doctype=%s AND action=%s AND id=%s """ \
           """AND email=%s AND status='finished'"""
    qres = run_sql(qstr, (doctype, action, subm_id, email))
    if len(qres) > 0:
        ## At least one row was returned - this
        ## submission is finished:
        submission_finished = 1
    return submission_finished


######
# Functions relating to approval stuff:
######

def get_approval_request_notes(doctype, reportnumber):
    """Get any notes relating to an approval request.
       An approval request in the database has a "note" field for notes or
       comments relating to the request. This function will return the value
       stored in that field.
       @param doctype: (string) - the document type of the document for
        which the approval request notes are to be retrieved.
       @param reportnumber: (string) - the report number of the document
        for which the approval request notes are to be retrieved.
       @return: (string or None) - String if there was a row for this approval
        request; None if not.
    """
    qstr = """SELECT note FROM sbmAPPROVAL """ \
           """WHERE doctype=%s AND rn=%s"""
    qres = run_sql(qstr, (doctype, reportnumber))
    try:
        return str(qres[0][0])
    except IndexError:
        ## No row for this approval request?
        return None


def get_simple_approval_status(doctype, reportnumber):
    """Get the (simple) approval "status" of a given document.
       Using this function, Register_Approval_Request can determine whether
       or not a docunent has already been approved or rejected at request time.
       @param doctype: (string) - the document type of the document for
        which the approval status is being requested.
       @param reportnumber: (string) - the report number of the document
        for which the approval status is being requested.
       @return: (string or None) - None if there is no approval request row
        for the document; else the value of the approval status.
    """
    approval_status = None
    qstr = """SELECT status FROM sbmAPPROVAL """ \
           """WHERE doctype=%s AND rn=%s"""
    qres = run_sql(qstr, (doctype, reportnumber))
    if len(qres) > 0:
        approval_status = qres[0][0]
    return approval_status


def register_new_approval_request(doctype, category, reportnumber, note=""):
    """Register a new approval request by inserting a row into the
       WebSubmit sbmAPPROVAL database table for it.
       @param doctype: (string) - the document type of the document for
        which the new approval request is being registered.
       @param category: (string) - the category of the document for which
        the new approval request is being registered.
       @param reportnumber: (string) - the report number of the document
        for which the new approval request is being registered.
       @param note: (string) - a "note" containing details about the approval
        request. (defaults to an empty string.)
       @return: None
    """
    qstr = """INSERT INTO sbmAPPROVAL """ \
           """(doctype, categ, rn, status, """ \
           """dFirstReq, dLastReq, dAction, access, note) VALUES """ \
           """(%s, %s, %s, 'waiting', NOW(), NOW(), '', '', %s)"""
    run_sql(qstr, (doctype, category, reportnumber, note))


def update_approval_request_status(doctype, \
                                   reportnumber, \
                                   note="",
                                   status="waiting"):
    """Update the status of an approval request and either the date of last
       request if it's simply an update, or the date of action if it's an
       approval/rejection.
       @param doctype: (string) - the document type of the document for
        which the approval request is being updated.
       @param reportnumber: (string) - the report number of the document
        for which the approval request is being updated.
       @param note: (string) - a "note" containing details about the approval
        request. This note will be prepended to any existing value for the
        note (with no separator, so include one if you don't want it to
        directly run into the existing value.) (defaults to an empty
        string.)
       @status: (string) - the new status of the document - defaults to
        waiting.
    """
    status = status.lower()
    qstr = """UPDATE sbmAPPROVAL """ \
           """SET status=%s, """
    if status in ("approved", "rejected"):
        ## If this is the "final" approval or rejection update, set the
        ## date of action:
        qstr += """dAction=NOW()"""
    else:
        ## Otherwise, update the date of "last request"
        qstr += """dLastReq=NOW()"""
    qstr += """, note=CONCAT(%s, note) """ \
            """WHERE doctype=%s AND rn=%s"""
    run_sql(qstr, (status, note, doctype, reportnumber))


def get_approval_request_category(reportnumber):
    """Given the report number of a document for which an approval request
       has been made, retrieve the category.
       @param reportnumber: (string) - the report number of the document
        for which the approval request has been made and the category is to
        be retrieved.
       @return: (string or None) - String if there was a row for this approval
        request; None if not.
    """
    qstr = """SELECT categ FROM sbmAPPROVAL """ \
           """WHERE rn=%s"""
    qres = run_sql(qstr, (reportnumber,))
    try:
        return str(qres[0][0])
    except IndexError:
        ## No row for this approval request?
        return None

def get_approval_url_parameters(access):
    """Given an access ID the function will return the appropriate URL parameters,
       as a dictionary, needed to generate an URL to the applicable approval form.

       Note: does not add the 'ln' parameter, which may be needed.
       @param access: (string) - the access id of the document
        for which the approval request has been made.
       @return: (dict or None) - dictionary if there was a row for this approval
        request; None if not.
    """
    res = run_sql("select doctype,rn from sbmAPPROVAL where access=%s",(access,))
    if len(res) == 0:
        return None
    doctype = res[0][0]
    rn = res[0][1]

    res = run_sql("select value from sbmPARAMETERS where name='edsrn' and doctype=%s",(doctype,))
    if len(res) == 0:
        return None
    edsrn = res[0][0]
    params = {
             edsrn: rn,
             'access' : access,
             'sub' : 'APP%s' % doctype,
             }
    return params
