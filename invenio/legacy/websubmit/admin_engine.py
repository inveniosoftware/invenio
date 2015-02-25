# -*- coding: utf-8 -*-
#
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

import re
from os.path import split, basename, isfile
from os import access, F_OK, R_OK, getpid, rename, unlink
from time import strftime, localtime
from invenio.legacy.websubmit.admin_dblayer import *
from invenio.legacy.websubmit.admin_config import *
from invenio.legacy.websubmit.config import CFG_RESERVED_SUBMISSION_FILENAMES
from invenio.modules.access.control import acc_get_all_roles, acc_get_role_users, acc_delete_user_role
from invenio.config import CFG_SITE_LANG, CFG_WEBSUBMIT_BIBCONVERTCONFIGDIR
from invenio.modules.access.engine import acc_authorize_action
from invenio.ext.logging import register_exception
from invenio.legacy.websubmit.admin_config import InvenioWebSubmitWarning
from invenio.base.i18n import gettext_set_language

import invenio.legacy.template

try:
    websubmitadmin_templates = invenio.legacy.template.load('websubmit', 'admin_')
except:
    pass


# utility functions:

def is_adminuser(req, role):
    """check if user is a registered administrator. """
    return acc_authorize_action(req, role)

def check_user(req, role, adminarea=2, authorized=0):
    (auth_code, auth_message) = is_adminuser(req, role)
    if not authorized and auth_code != 0:
        return ("false", auth_message)
    return ("", auth_message)

def get_navtrail(ln=CFG_SITE_LANG):
    """gets the navtrail for title...
       @param title: title of the page
       @param ln: language
       @return: HTML output
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

def save_update_to_file(filepath, filecontent, notruncate=0, appendmode=0):
    """Save a string value to a file.
       Save will create a new file if the file does not exist. Mode can be set to truncate an older file
       or to refuse to create the file if it already exists.  There is also a mode to "append" the string value
       to a file.
       @param filepath: (string) the full path to the file
       @param filecontent: (string) the content to be written to the file
       @param notruncate: (integer) should be 1 or 0, defaults to 0 (ZERO). If 0, existing file will be truncated;
        if 1, file will not be written if it already exists
       @param appendmode: (integer) should be 1 or 0, defaults to 0 (ZERO). If 1, data will be appended to the file
        if it exists; if 0, file will be truncated (or not, depending on the notruncate mode) by new data.
       @return: None
       @exceptions raised:
             - InvenioWebSubmitAdminWarningIOError: when operations involving writing to file failed.
    """
    ## sanity checking:
    if notruncate not in (0, 1):
        notruncate = 0
    if appendmode not in (0, 1):
        appendmode = 0

    (fpath, fname) = split(filepath)
    if fname == "":
        ## error opening file
        msg = """Unable to open filepath [%s] - couldn't determine a valid filename""" % (filepath,)
        raise InvenioWebSubmitAdminWarningIOError(msg)

    ## if fpath is not empty, append the trailing "/":
    if fpath != "":
        fpath += "/"

    if appendmode == 0:
        if notruncate != 0 and access("%s%s" % (fpath, fname), F_OK):
            ## in no-truncate mode, but file already exists!
            msg = """Unable to write to file [%s] in "no-truncate mode" because file already exists"""\
                  % (fname,)
            raise InvenioWebSubmitAdminWarningIOError(msg)

        ## file already exists, make temporary file first, then move it later
        tmpfname = "%s_%s_%s" % (fname, strftime("%Y%m%d%H%M%S", localtime()), getpid())

        ## open temp file for writing:
        try:
            fp = open("%s%s" % (fpath, tmpfname), "w")
        except IOError as e:
            ## cannot open file
            msg = """Unable to write to file [%s%s] - cannot open file for writing""" % (fpath, fname)
            raise InvenioWebSubmitAdminWarningIOError(msg)
        ## write contents to temp file:
        try:
            fp.write(filecontent)
            fp.flush()
            fp.close()
        except IOError as e:
            ## could not write to temp file
            msg = """Unable to write to file [%s]""" % (tmpfname,)
            ## remove the "temp file"
            try:
                fp.close()
                unlink("%s%s" % (fpath, tmpfname))
            except IOError:
                pass
            raise InvenioWebSubmitAdminWarningIOError(msg)

        ## rename temp file to final filename:
        try:
            rename("%s%s" % (fpath, tmpfname), "%s%s" % (fpath, fname))
        except OSError:
            ## couldnt rename the tmp file to final file name
            msg = """Unable to write to file [%s] - created temporary file [%s], but could not then rename it to [%s]"""\
                  % (fname, tmpfname, fname)
            raise InvenioWebSubmitAdminWarningIOError(msg)
    else:
        ## append mode:
        try:
            fp = open("%s%s" % (fpath, fname), "a")
        except IOError as e:
            ## cannot open file
            msg = """Unable to write to file [%s] - cannot open file for writing in append mode""" % (fname,)
            raise InvenioWebSubmitAdminWarningIOError(msg)

        ## write contents to temp file:
        try:
            fp.write(filecontent)
            fp.flush()
            fp.close()
        except IOError as e:
            ## could not write to temp file
            msg = """Unable to write to file [%s] in append mode""" % (fname,)
            ## close the file
            try:
                fp.close()
            except IOError:
                pass
            raise InvenioWebSubmitAdminWarningIOError(msg)
    return

def string_is_alphanumeric_including_underscore(txtstring):
    p_txtstring = re.compile(r'^\w*$')
    m_txtstring = p_txtstring.search(txtstring)
    if m_txtstring is not None:
        return 1
    else:
        return 0

def function_name_is_valid(fname):
    p_fname = re.compile(r'^(_|[a-zA-Z])\w*$')
    m_fname = p_fname.search(fname)
    if m_fname is not None:
        return 1
    else:
        return 0

def wash_single_urlarg(urlarg, argreqdtype, argdefault, maxstrlen=None, minstrlen=None, truncatestr=0):
    """Wash a single argument according to some specifications.
       @param urlarg: the argument to be tested, as passed from the form/url, etc
       @param argreqdtype: (a python type) the type that the argument should conform to (argument required
        type)
       @argdefault: the default value that should be returned for the argument in the case that it
        doesn't comply with the washing specifications
       @param maxstrlen: (integer) the maximum length for a string argument; defaults to None, which means
        that no maximum length is forced upon the string
       @param minstrlen: (integer) the minimum length for a string argument; defaults to None, which means
        that no minimum length is forced upon the string
       @truncatestr: (integer) should be 1 or 0 (ZERO). A flag used to determine whether or not a string
        argument that overstretches the maximum length (if one if provided) should be truncated, or reset
        to the default for the argument. 0, means don't truncate and reset the argument; 1 means truncate
        the string.
       @return: the washed argument
       @exceptions raised:
            - ValueError: when it is not possible to cast an argument to the type passed as argreqdtype
    """
    ## sanity checking:
    if maxstrlen is not None and type(maxstrlen) is not int:
        maxstrlen = None
    elif maxstrlen is int and maxstrlen < 1:
        maxstrlen = None
    if minstrlen is not None and type(minstrlen) is not int:
        minstrlen = None
    elif minstrlen is int and minstrlen < 1:
        minstrlen = None

    result = ""
    arg_dst_type = argreqdtype

    ## if no urlarg, return the default for that argument:
    if urlarg is None:
        result = argdefault
        return result

    ## get the type of the argument passed:
    arg_src_type = type(urlarg)
    value = urlarg

    # First, handle the case where we want all the results. In
    # this case, we need to ensure all the elements are strings,
    # and not Field instances.
    if arg_src_type in (list, tuple):
        if arg_dst_type is list:
            result = [str(x) for x in value]
            return result

        if arg_dst_type is tuple:
            result = tuple([str(x) for x in value])
            return result

        # in all the other cases, we are only interested in the
        # first value.
        value = value[0]

    # Maybe we already have what is expected? Then don't change
    # anything.
    if arg_src_type is arg_dst_type:
        result = value
        if arg_dst_type is str and maxstrlen is not None and len(result) > maxstrlen:
            if truncatestr != 0:
                result = result[0:maxstrlen]
            else:
                result = argdefault
        elif arg_dst_type is str and minstrlen is not None and len(result) < minstrlen:
            result = argdefault
        return result

    if arg_dst_type in (str, int):
        try:
            result = arg_dst_type(value)

            if arg_dst_type is str and maxstrlen is not None and len(result) > maxstrlen:
                if truncatestr != 0:
                    result = result[0:maxstrlen]
                else:
                    result = argdefault
            elif arg_dst_type is str and minstrlen is not None and len(result) < minstrlen:
                result = argdefault
        except:
            result = argdefault
    elif arg_dst_type is tuple:
        result = (value,)

    elif arg_dst_type is list:
        result = [value]

    elif arg_dst_type is dict:
        result = {0: str(value)}

    else:
        raise ValueError('cannot cast form argument into type %r' % (arg_dst_type,))

    return result


# Internal Business-Logic functions

# Functions for managing collection order, etc:

def build_submission_collection_tree(collection_id, has_brother_above=0, has_brother_below=0):
    ## get the name of this collection:
    collection_name = get_collection_name(collection_id)
    if collection_name is None:
        collection_name = "Unknown Collection"

    ## make a data-structure containing the details of the collection:
    collection_node = { 'collection_id'       : collection_id,         ## collection ID
                        'collection_name'     : collection_name,   ## collection Name
                        'collection_children' : [],                ## list of 'collection' children nodes
                        'doctype_children'    : [],                ## list of 'doctype' children
                        'has_brother_above'   : has_brother_above, ## has a sibling collection above in score
                        'has_brother_below'   : has_brother_below, ## has a sibling collection below in score
                      }

    ## get the IDs and names of all doctypes attached to this collection:
    res_doctype_children = get_doctype_children_of_collection(collection_id)
    ## for each child, add its details to the list of doctype children for this node:
    for doctype in res_doctype_children:
        doctype_node = { 'doctype_id'      : doctype[0],
                         'doctype_lname'   : doctype[1],
                         'catalogue_order' : doctype[2],
                       }
        collection_node['doctype_children'].append(doctype_node)

    ## now get details of all collections attached to this one:
    res_collection_children = get_collection_children_of_collection(collection_id)

    num_collection_children = len(res_collection_children)
    for child_num in xrange(0, num_collection_children):
        brother_below = brother_above = 0
        if child_num > 0:
            ## this is not the first brother - it has a brother above
            brother_above = 1
        if child_num < num_collection_children - 1:
            ## this is not the last brother - it has a brother below
            brother_below = 1
        collection_node['collection_children'].append(\
            build_submission_collection_tree(collection_id=res_collection_children[child_num][0],
                                  has_brother_above=brother_above,
                                  has_brother_below=brother_below))


    ## return the built collection tree:
    return collection_node

def _organise_submission_page_display_submission_tree(user_msg=""):
    title = "Organise WebSubmit Main Page"
    body = ""
    if user_msg == "" or type(user_msg) not in (list, tuple, str, unicode):
        user_msg = []
    ## Get the submissions tree:
    submission_collection_tree = build_submission_collection_tree(0)
    ## Get all 'submission collections':
    submission_collections = get_details_of_all_submission_collections()
    sub_col = [('0', 'Top Level')]
    for collection in submission_collections:
        sub_col.append((str(collection[0]), str(collection[1])))
    ## Get all document types:
    doctypes = get_docid_docname_and_docid_alldoctypes()

    ## build the page:
    body = websubmitadmin_templates.tmpl_display_submission_page_organisation(submission_collection_tree=submission_collection_tree,
                                                                              submission_collections=sub_col,
                                                                              doctypes=doctypes,
                                                                              user_msg=user_msg)
    return (title, body)

def _delete_submission_collection(sbmcolid):
    """Recursively calls itself to delete a submission-collection and all of its
       attached children (and their children, etc) from the submission-tree.
       @param sbmcolid: (integer) - the ID of the submission-collection to be deleted.
       @return: None
       @Exceptions raised: InvenioWebSubmitAdminWarningDeleteFailed when it was not
        possible to delete the submission-collection or some of its children.
    """
    ## Get the collection-children of this submission-collection:
    collection_children = get_collection_children_of_collection(sbmcolid)

    ## recursively move through each collection-child:
    for collection_child in collection_children:
        _delete_submission_collection(collection_child[0])

    ## delete all document-types attached to this submission-collection:
    error_code = delete_doctype_children_from_submission_collection(sbmcolid)
    if error_code != 0:
        ## Unable to delete all doctype-children:
        err_msg = "Unable to delete doctype children of submission-collection [%s]" % sbmcolid
        raise InvenioWebSubmitAdminWarningDeleteFailed(err_msg)

    ## delete this submission-collection's entry from the sbmCOLLECTION_sbmCOLLECTION table:
    error_code = delete_submission_collection_from_submission_tree(sbmcolid)
    if error_code != 0:
        ## Unable to delete submission-collection from the submission-tree:
        err_msg = "Unable to delete submission-collection [%s] from submission-tree" % sbmcolid
        raise InvenioWebSubmitAdminWarningDeleteFailed(err_msg)

    ## Now delete this submission-collection's details:
    error_code = delete_submission_collection_details(sbmcolid)
    if error_code != 0:
        ## Unable to delete the details of the submission-collection:
        err_msg = "Unable to delete details of submission-collection [%s]" % sbmcolid
        raise InvenioWebSubmitAdminWarningDeleteFailed(err_msg)

    ## return
    return


def perform_request_organise_submission_page(doctype="",
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
                                             movedoctypedowninsbmcollection=""):
    user_msg = []
    body = ""
    if "" not in (deletedoctypefromsbmcollection, sbmcolid, catscore, doctype):
        ## delete a document type from it's position in the tree
        error_code = delete_doctype_from_position_on_submission_page(doctype, sbmcolid, catscore)
        if error_code == 0:
            ## doctype deleted - now normalize scores of remaining doctypes:
            normalize_scores_of_doctype_children_for_submission_collection(sbmcolid)
            user_msg.append("Document type successfully deleted from submissions tree")
        else:
            user_msg.append("Unable to delete document type from submission-collection")
        ## display submission-collections:
        (title, body) = _organise_submission_page_display_submission_tree(user_msg=user_msg)
    elif "" not in (deletesbmcollection, sbmcolid):
        ## try to delete the submission-collection from the tree:
        try:
            _delete_submission_collection(sbmcolid)
            user_msg.append("Submission-collection successfully deleted from submissions tree")
        except InvenioWebSubmitAdminWarningDeleteFailed as excptn:
            user_msg.append(str(excptn))
        ## re-display submission-collections:
        (title, body) = _organise_submission_page_display_submission_tree(user_msg=user_msg)
    elif "" not in (movedoctypedowninsbmcollection, sbmcolid, doctype, catscore):
        ## move a doctype down in order for a submission-collection:
        ## normalize scores of all doctype-children of the submission-collection:
        normalize_scores_of_doctype_children_for_submission_collection(sbmcolid)
        ## swap this doctype with that below it:
        ## Get score of doctype to move:
        score_doctype_to_move = get_catalogue_score_of_doctype_child_of_submission_collection(sbmcolid, doctype)
        ## Get score of the doctype brother directly below the doctype to be moved:
        score_brother_below = get_score_of_next_doctype_child_below(sbmcolid, score_doctype_to_move)
        if None in (score_doctype_to_move, score_brother_below):
            user_msg.append("Unable to move document type down")
        else:
            ## update the brother below the doctype to be moved to have a score the same as the doctype to be moved:
            update_score_of_doctype_child_of_submission_collection_at_scorex(sbmcolid, score_brother_below, score_doctype_to_move)
            ## Update the doctype to be moved to have a score of the brother directly below it:
            update_score_of_doctype_child_of_submission_collection_with_doctypeid_and_scorex(sbmcolid,
                                                                                             doctype,
                                                                                             score_doctype_to_move,
                                                                                             score_brother_below)
            user_msg.append("Document type moved down")
        (title, body) = _organise_submission_page_display_submission_tree(user_msg=user_msg)
    elif "" not in (movedoctypeupinsbmcollection, sbmcolid, doctype, catscore):
        ## move a doctype up in order for a submission-collection:
        ## normalize scores of all doctype-children of the submission-collection:
        normalize_scores_of_doctype_children_for_submission_collection(sbmcolid)
        ## swap this doctype with that above it:
        ## Get score of doctype to move:
        score_doctype_to_move = get_catalogue_score_of_doctype_child_of_submission_collection(sbmcolid, doctype)
        ## Get score of the doctype brother directly above the doctype to be moved:
        score_brother_above = get_score_of_previous_doctype_child_above(sbmcolid, score_doctype_to_move)
        if None in (score_doctype_to_move, score_brother_above):
            user_msg.append("Unable to move document type up")
        else:
            ## update the brother above the doctype to be moved to have a score the same as the doctype to be moved:
            update_score_of_doctype_child_of_submission_collection_at_scorex(sbmcolid, score_brother_above, score_doctype_to_move)
            ## Update the doctype to be moved to have a score of the brother directly above it:
            update_score_of_doctype_child_of_submission_collection_with_doctypeid_and_scorex(sbmcolid,
                                                                                             doctype,
                                                                                             score_doctype_to_move,
                                                                                             score_brother_above)
            user_msg.append("Document type moved up")
        (title, body) = _organise_submission_page_display_submission_tree(user_msg=user_msg)
    elif "" not in (movesbmcollectiondown, sbmcolid):
        ## move a submission-collection down in order:

        ## Sanity checking:
        try:
            int(sbmcolid)
        except ValueError:
            sbmcolid = 0

        if int(sbmcolid) != 0:
            ## Get father ID of submission-collection:
            sbmcolidfather = get_id_father_of_collection(sbmcolid)
            if sbmcolidfather is None:
                user_msg.append("Unable to move submission-collection downwards")
            else:
                ## normalize scores of all collection-children of the father submission-collection:
                normalize_scores_of_collection_children_of_collection(sbmcolidfather)
                ## swap this collection with the one above it:
                ## get the score of the collection to move:
                score_col_to_move = get_score_of_collection_child_of_submission_collection(sbmcolidfather, sbmcolid)
                ## get the score of the collection brother directly below the collection to be moved:
                score_brother_below = get_score_of_next_collection_child_below(sbmcolidfather, score_col_to_move)
                if None in (score_col_to_move, score_brother_below):
                    ## Invalid movement
                    user_msg.append("Unable to move submission collection downwards")
                else:
                    ## update the brother below the collection to be moved to have a score the same as the collection to be moved:
                    update_score_of_collection_child_of_submission_collection_at_scorex(sbmcolidfather,
                                                                                        score_brother_below,
                                                                                        score_col_to_move)
                    ## Update the collection to be moved to have a score of the brother directly below it:
                    update_score_of_collection_child_of_submission_collection_with_colid_and_scorex(sbmcolidfather,
                                                                                                    sbmcolid,
                                                                                                    score_col_to_move,
                                                                                                    score_brother_below)
                    user_msg.append("Submission-collection moved downwards")

        else:
            ## cannot move the master (0) collection
            user_msg.append("Unable to move submission-collection downwards")
        (title, body) = _organise_submission_page_display_submission_tree(user_msg=user_msg)
    elif "" not in (movesbmcollectionup, sbmcolid):
        ## move a submission-collection up in order:

        ## Sanity checking:
        try:
            int(sbmcolid)
        except ValueError:
            sbmcolid = 0

        if int(sbmcolid) != 0:
            ## Get father ID of submission-collection:
            sbmcolidfather = get_id_father_of_collection(sbmcolid)
            if sbmcolidfather is None:
                user_msg.append("Unable to move submission-collection upwards")
            else:
                ## normalize scores of all collection-children of the father submission-collection:
                normalize_scores_of_collection_children_of_collection(sbmcolidfather)
                ## swap this collection with the one above it:
                ## get the score of the collection to move:
                score_col_to_move = get_score_of_collection_child_of_submission_collection(sbmcolidfather, sbmcolid)
                ## get the score of the collection brother directly above the collection to be moved:
                score_brother_above = get_score_of_previous_collection_child_above(sbmcolidfather, score_col_to_move)
                if None in (score_col_to_move, score_brother_above):
                    ## Invalid movement
                    user_msg.append("Unable to move submission collection upwards")
                else:
                    ## update the brother above the collection to be moved to have a score the same as the collection to be moved:
                    update_score_of_collection_child_of_submission_collection_at_scorex(sbmcolidfather,
                                                                                        score_brother_above,
                                                                                        score_col_to_move)
                    ## Update the collection to be moved to have a score of the brother directly above it:
                    update_score_of_collection_child_of_submission_collection_with_colid_and_scorex(sbmcolidfather,
                                                                                                    sbmcolid,
                                                                                                    score_col_to_move,
                                                                                                    score_brother_above)
                    user_msg.append("Submission-collection moved upwards")
        else:
            ## cannot move the master (0) collection
            user_msg.append("Unable to move submission-collection upwards")
        (title, body) = _organise_submission_page_display_submission_tree(user_msg=user_msg)
    elif "" not in (addsbmcollection, addtosbmcollection):
        ## Add a submission-collection, attached to a submission-collection:
        ## check that the collection to attach to exists:
        parent_ok = 0
        if int(addtosbmcollection) != 0:
            parent_name = get_collection_name(addtosbmcollection)
            if parent_name is not None:
                parent_ok = 1
        else:
            parent_ok = 1
        if parent_ok != 0:
            ## create the new collection:
            id_son = insert_submission_collection(addsbmcollection)
            ## get the maximum catalogue score of the existing collection children:
            max_child_score = \
               get_maximum_catalogue_score_of_collection_children_of_submission_collection(addtosbmcollection)
            ## add it to the collection, at a higher score than the others have:
            new_score = max_child_score + 1
            insert_collection_child_for_submission_collection(addtosbmcollection, id_son, new_score)
            user_msg.append("Submission-collection added to submissions tree")
        else:
            ## Parent submission-collection does not exist:
            user_msg.append("Unable to add submission-collection - parent unknown")
        (title, body) = _organise_submission_page_display_submission_tree(user_msg=user_msg)
    elif "" not in (adddoctypes, addtosbmcollection):
        ## Add document type(s) to a submission-collection:
        if type(adddoctypes) == str:
            adddoctypes = [adddoctypes,]
        ## Does submission-collection exist?
        num_collections_sbmcolid = get_number_of_rows_for_submission_collection(addtosbmcollection)
        if num_collections_sbmcolid > 0:
            for doctypeid in adddoctypes:
                ## Check that Doctype exists:
                num_doctypes_doctypeid = get_number_doctypes_docid(doctypeid)

                if num_doctypes_doctypeid < 1:
                    ## Cannot connect an unknown doctype:
                    user_msg.append("Unable to connect unknown document-type [%s] to a submission-collection" \
                                    % doctypeid)
                    continue
                else:
                    ## insert the submission-collection/doctype link:
                    ## get the maximum catalogue score of the existing doctype children:
                    max_child_score = \
                       get_maximum_catalogue_score_of_doctype_children_of_submission_collection(addtosbmcollection)
                    ## add it to the new doctype, at a higher score than the others have:
                    new_score = max_child_score + 1
                    insert_doctype_child_for_submission_collection(addtosbmcollection, doctypeid, new_score)
                    user_msg.append("Document-type added to submissions tree")
        else:
            ## submission-collection didn't exist
            user_msg.append("The selected submission-collection doesn't seem to exist")
        ## Check that submission-collection exists:
        ## insert
        (title, body) = _organise_submission_page_display_submission_tree(user_msg=user_msg)
    else:
        ## default action - display submission-collections:
        (title, body) = _organise_submission_page_display_submission_tree(user_msg=user_msg)
    return (title, body)



# Functions for adding new catalgue to DB:
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

def perform_request_add_function(funcname=None, funcdescr=None, funcaddcommit=""):
    user_msg = []
    body = ""
    title = "Create New WebSubmit Function"
    commit_error=0

    ## wash args:
    if funcname is not None:
        try:
            funcname = wash_single_urlarg(urlarg=funcname, argreqdtype=str, argdefault="", maxstrlen=40, minstrlen=1)
            if function_name_is_valid(fname=funcname) == 0:
                funcname = ""
        except ValueError as e:
            funcname = ""
    else:
        funcname = ""
    if funcdescr is not None:
        try:
            funcdescr = wash_single_urlarg(urlarg=funcdescr, argreqdtype=str, argdefault="")
        except ValueError as e:
            funcdescr = ""
    else:
        funcdescr = ""

    ## process request:
    if funcaddcommit != "" and funcaddcommit is not None:
        if funcname == "":
            funcname = ""
            user_msg.append("""Function name is mandatory and must be a string with no more than 40 characters""")
            user_msg.append("""It must contain only alpha-numeric and underscore characters, beginning with a """\
                            """letter or underscore""")
            commit_error = 1

        if commit_error != 0:
            ## don't commit - just re-display page with message to user
            body = websubmitadmin_templates.tmpl_display_addfunctionform(funcdescr=funcdescr, user_msg=user_msg)
            return (title, body)

        ## Add a new function definition - IF it is not already present
        err_code = insert_function_details(funcname, funcdescr)

        ## Handle error code - redisplay form with warning about no DB commit, or display with options
        ## to edit function:
        if err_code == 0:
            user_msg.append("""'%s' Function Added to WebSubmit""" % (funcname,))
            all_function_parameters = get_distinct_paramname_all_websubmit_function_parameters()
            body = websubmitadmin_templates.tmpl_display_addfunctionform(funcname=funcname,
                                                                         funcdescr=funcdescr,
                                                                         all_websubmit_func_parameters=all_function_parameters,
                                                                         perform_act="functionedit",
                                                                         user_msg=user_msg)
        else:
            ## Could not commit function to WebSubmit DB - redisplay form with function description:
            user_msg.append("""Could Not Add '%s' Function to WebSubmit""" % (funcname,))
            body = websubmitadmin_templates.tmpl_display_addfunctionform(funcdescr=funcdescr, user_msg=user_msg)

    else:
        ## Display Web form for new function addition:
        body = websubmitadmin_templates.tmpl_display_addfunctionform()

    return (title, body)

def perform_request_add_action(actid=None, actname=None, working_dir=None, status_text=None, actcommit=""):
    """An interface for the addition of a new WebSubmit action.
       If form fields filled, will insert new action into WebSubmit database, else will display
       web form prompting for action details.
       @param actid:       unique id for new action
       @param actname:     name of new action
       @param working_dir: action working directory for WebSubmit core
       @param status_text: status text displayed at end of action
       @return: tuple containing "title" (title of page), body (page body).
    """
    user_msg = []
    body = ""
    title = "Create New WebSubmit Action"
    commit_error=0

    ## wash args:
    if actid is not None:
        try:
            actid = wash_single_urlarg(urlarg=actid, argreqdtype=str, argdefault="", maxstrlen=3, minstrlen=3)
            if string_is_alphanumeric_including_underscore(txtstring=actid) == 0:
                actid = ""
        except ValueError as e:
            actid = ""
    else:
        actid = ""
    if actname is not None:
        try:
            actname = wash_single_urlarg(urlarg=actname, argreqdtype=str, argdefault="")
        except ValueError as e:
            actname = ""
    else:
        actname = ""
    if working_dir is not None:
        try:
            working_dir = wash_single_urlarg(urlarg=working_dir, argreqdtype=str, argdefault="")
        except ValueError as e:
            working_dir = ""
    else:
        working_dir = ""
    if status_text is not None:
        try:
            status_text = wash_single_urlarg(urlarg=status_text, argreqdtype=str, argdefault="")
        except ValueError as e:
            status_text = ""
    else:
        status_text = ""

    ## process request:
    if actcommit != "" and actcommit is not None:
        if actid in ("", None):
            actid = ""
            user_msg.append("""Action ID is mandatory and must be a 3 letter string""")
            commit_error = 1
        if actname in ("", None):
            actname = ""
            user_msg.append("""Action description is mandatory""")
            commit_error = 1

        if commit_error != 0:
            ## don't commit - just re-display page with message to user
            body = websubmitadmin_templates.tmpl_display_addactionform(actid=actid, actname=actname, working_dir=working_dir,\
                                                                       status_text=status_text, user_msg=user_msg)
            return (title, body)

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
            body = websubmitadmin_templates.tmpl_display_addactionform(actid=actid, actname=actname, working_dir=working_dir, \
                                                                       status_text=status_text, user_msg=user_msg)
    else:
        ## Display Web form for new action details:
        body = websubmitadmin_templates.tmpl_display_addactionform()
    return (title, body)

def perform_request_add_jscheck(chname=None, chdesc=None, chcommit=""):
    """An interface for the addition of a new WebSubmit JavaScript Check, as used on form elements.
       If form fields filled, will insert new Check into WebSubmit database, else will display
       Web form prompting for Check details.
       @param chname:       unique id/name for new Check
       @param chdesc:     description (JavaScript code body) of new Check
       @return: tuple containing "title" (title of page), body (page body).
    """
    user_msg = []
    body = ""
    title = "Create New WebSubmit Checking Function"
    commit_error=0

    ## wash args:
    if chname is not None:
        try:
            chname = wash_single_urlarg(urlarg=chname, argreqdtype=str, argdefault="", maxstrlen=15, minstrlen=1)
            if function_name_is_valid(fname=chname) == 0:
                chname = ""
        except ValueError as e:
            chname = ""
    else:
        chname = ""
    if chdesc is not None:
        try:
            chdesc = wash_single_urlarg(urlarg=chdesc, argreqdtype=str, argdefault="")
        except ValueError as e:
            chdesc = ""
    else:
        chdesc = ""

    ## process request:
    if chcommit != "" and chcommit is not None:
        if chname in ("", None):
            chname = ""
            user_msg.append("""Check name is mandatory and must be a string with no more than 15 characters""")
            user_msg.append("""It must contain only alpha-numeric and underscore characters, beginning with a """\
                            """letter or underscore""")
            commit_error = 1

        if commit_error != 0:
            ## don't commit - just re-display page with message to user
            body = websubmitadmin_templates.tmpl_display_addjscheckform(chname=chname, chdesc=chdesc, user_msg=user_msg)
            return (title, body)

        ## Commit new check to WebSubmit DB:
        err_code = insert_jscheck_details(chname, chdesc)

        ## Handle error code - redisplay form wih warning about no DB commit, or move to list
        ## of checks
        if err_code == 0:
            ## Check added: show page listing WebSubmit JS Checks
            user_msg.append("""'%s' Checking Function Added to WebSubmit""" % (chname,))
            all_jschecks = get_chname_alljschecks()
            body = websubmitadmin_templates.tmpl_display_alljschecks(all_jschecks, user_msg=user_msg)
            title = "Available WebSubmit Checking Functions"
        else:
            ## Could not commit Check to WebSubmit DB: redisplay form with completed details and error message
            ## TODO : Warning Message
            user_msg.append("""Could Not Add '%s' Checking Function to WebSubmit""" % (chname,))
            body = websubmitadmin_templates.tmpl_display_addjscheckform(chname=chname, chdesc=chdesc, user_msg=user_msg)
    else:
        ## Display Web form for new check details:
        body = websubmitadmin_templates.tmpl_display_addjscheckform()
    return (title, body)

def perform_request_add_element(elname=None, elmarccode=None, eltype=None, elsize=None, elrows=None, \
                                elcols=None, elmaxlength=None, elval=None, elfidesc=None, \
                                elmodifytext=None, elcommit=""):
    """An interface for adding a new ELEMENT to the WebSubmit DB.
       @param elname: (string) element name.
       @param elmarccode: (string) element's MARC code.
       @param eltype: (character) element type.
       @param elsize: (integer) element size.
       @param elrows: (integer) number of rows in element.
       @param elcols: (integer) number of columns in element.
       @param elmaxlength: (integer) maximum length of element
       @param elval: (string) default value of element
       @param elfidesc: (string) description of element
       @param elmodifytext: (string) modification text of element
       @param elcommit: (string) If this value is not empty, attempt to commit element details to WebSubmit DB
       @return: tuple containing "title" (title of page), body (page body).
    """
    user_msg = []
    body = ""
    title = "Create New WebSubmit Element"
    commit_error=0

    ## wash args:
    if elname is not None:
        try:
            elname = wash_single_urlarg(urlarg=elname, argreqdtype=str, argdefault="", maxstrlen=15, minstrlen=1)
            if string_is_alphanumeric_including_underscore(txtstring=elname) == 0:
                elname = ""
        except ValueError as e:
            elname = ""
    else:
        elname = ""
    if elmarccode is not None:
        try:
            elmarccode = wash_single_urlarg(urlarg=elmarccode, argreqdtype=str, argdefault="")
        except ValueError as e:
            elmarccode = ""
    else:
        elmarccode = ""
    if eltype is not None:
        try:
            eltype = wash_single_urlarg(urlarg=eltype, argreqdtype=str, argdefault="", maxstrlen=1, minstrlen=1)
        except ValueError as e:
            eltype = ""
    else:
        eltype = ""
    if elsize is not None:
        try:
            elsize = wash_single_urlarg(urlarg=elsize, argreqdtype=int, argdefault="")
        except ValueError as e:
            elsize = ""
    else:
        elsize = ""
    if elrows is not None:
        try:
            elrows = wash_single_urlarg(urlarg=elrows, argreqdtype=int, argdefault="")
        except ValueError as e:
            elrows = ""
    else:
        elrows = ""
    if elcols is not None:
        try:
            elcols = wash_single_urlarg(urlarg=elcols, argreqdtype=int, argdefault="")
        except ValueError as e:
            elcols = ""
    else:
        elcols = ""
    if elmaxlength is not None:
        try:
            elmaxlength = wash_single_urlarg(urlarg=elmaxlength, argreqdtype=int, argdefault="")
        except ValueError as e:
            elmaxlength = ""
    else:
        elmaxlength = ""
    if elval is not None:
        try:
            elval = wash_single_urlarg(urlarg=elval, argreqdtype=str, argdefault="")
        except ValueError as e:
            elval = ""
    else:
        elval = ""
    if elfidesc is not None:
        try:
            elfidesc = wash_single_urlarg(urlarg=elfidesc, argreqdtype=str, argdefault="")
        except ValueError as e:
            elfidesc = ""
    else:
        elfidesc = ""
    if elmodifytext is not None:
        try:
            elmodifytext = wash_single_urlarg(urlarg=elmodifytext, argreqdtype=str, argdefault="")
        except ValueError as e:
            elmodifytext = ""
    else:
        elmodifytext = ""

    ## process request:
    if elcommit != "" and elcommit is not None:
        if elname == "":
            elname = ""
            user_msg.append("""The element name is mandatory and must be a string with no more than 15 characters""")
            user_msg.append("""It must contain only alpha-numeric and underscore characters""")
            commit_error = 1
        if eltype == "" or eltype not in ("D", "F", "H", "I", "R", "S", "T"):
            eltype = ""
            user_msg.append("""The element type is mandatory and must be selected from the list""")
            commit_error = 1

        if commit_error != 0:
            ## don't commit - just re-display page with message to user
            body = websubmitadmin_templates.tmpl_display_addelementform(elname=elname,
                                                                        elmarccode=elmarccode,
                                                                        eltype=eltype,
                                                                        elsize=str(elsize),
                                                                        elrows=str(elrows),
                                                                        elcols=str(elcols),
                                                                        elmaxlength=str(elmaxlength),
                                                                        elval=elval,
                                                                        elfidesc=elfidesc,
                                                                        elmodifytext=elmodifytext,
                                                                        user_msg=user_msg,
                                                                       )
            return (title, body)

        ## Commit new element description to WebSubmit DB:
        err_code = insert_element_details(elname=elname, elmarccode=elmarccode, eltype=eltype, \
                                          elsize=elsize, elrows=elrows, elcols=elcols, \
                                          elmaxlength=elmaxlength, elval=elval, elfidesc=elfidesc, \
                                          elmodifytext=elmodifytext)
        if err_code == 0:
            ## Element added: show page listing WebSubmit elements
            user_msg.append("""'%s' Element Added to WebSubmit""" % (elname,))
            if elname in CFG_RESERVED_SUBMISSION_FILENAMES:
                user_msg.append("""WARNING: '%s' is a reserved name. Check WebSubmit admin guide to be aware of possible side-effects.""" % elname)
            title = "Available WebSubmit Elements"
            all_elements = get_elename_allelements()
            body = websubmitadmin_templates.tmpl_display_allelements(all_elements, user_msg=user_msg)
        else:
            ## Could not commit element to WebSubmit DB: redisplay form with completed details and error message
            ## TODO : Warning Message
            user_msg.append("""Could Not Add '%s' Element to WebSubmit""" % (elname,))
            body = websubmitadmin_templates.tmpl_display_addelementform(elname=elname,
                                                                        elmarccode=elmarccode,
                                                                        eltype=eltype,
                                                                        elsize=str(elsize),
                                                                        elrows=str(elrows),
                                                                        elcols=str(elcols),
                                                                        elmaxlength=str(elmaxlength),
                                                                        elval=elval,
                                                                        elfidesc=elfidesc,
                                                                        elmodifytext=elmodifytext,
                                                                        user_msg=user_msg,
                                                                       )
    else:
        ## Display Web form for new element details:
        body = websubmitadmin_templates.tmpl_display_addelementform()
    return (title, body)

def perform_request_edit_element(elname, elmarccode=None, eltype=None, elsize=None, \
                                 elrows=None, elcols=None, elmaxlength=None, elval=None, \
                                 elfidesc=None, elmodifytext=None, elcommit=""):
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
       @param elcommit: If this value is not empty, attempt to commit element details to WebSubmit DB
       @return: tuple containing "title" (title of page), body (page body).
    """
    user_msg = []
    body = ""
    title = "Edit WebSubmit Element"
    commit_error=0

    ## wash args:
    if elname is not None:
        try:
            elname = wash_single_urlarg(urlarg=elname, argreqdtype=str, argdefault="", maxstrlen=15, minstrlen=1)
            if string_is_alphanumeric_including_underscore(txtstring=elname) == 0:
                elname = ""
        except ValueError as e:
            elname = ""
    else:
        elname = ""
    if elmarccode is not None:
        try:
            elmarccode = wash_single_urlarg(urlarg=elmarccode, argreqdtype=str, argdefault="")
        except ValueError as e:
            elmarccode = ""
    else:
        elmarccode = ""
    if eltype is not None:
        try:
            eltype = wash_single_urlarg(urlarg=eltype, argreqdtype=str, argdefault="", maxstrlen=1, minstrlen=1)
        except ValueError as e:
            eltype = ""
    else:
        eltype = ""
    if elsize is not None:
        try:
            elsize = wash_single_urlarg(urlarg=elsize, argreqdtype=int, argdefault="")
        except ValueError as e:
            elsize = ""
    else:
        elsize = ""
    if elrows is not None:
        try:
            elrows = wash_single_urlarg(urlarg=elrows, argreqdtype=int, argdefault="")
        except ValueError as e:
            elrows = ""
    else:
        elrows = ""
    if elcols is not None:
        try:
            elcols = wash_single_urlarg(urlarg=elcols, argreqdtype=int, argdefault="")
        except ValueError as e:
            elcols = ""
    else:
        elcols = ""
    if elmaxlength is not None:
        try:
            elmaxlength = wash_single_urlarg(urlarg=elmaxlength, argreqdtype=int, argdefault="")
        except ValueError as e:
            elmaxlength = ""
    else:
        elmaxlength = ""
    if elval is not None:
        try:
            elval = wash_single_urlarg(urlarg=elval, argreqdtype=str, argdefault="")
        except ValueError as e:
            elval = ""
    else:
        elval = ""
    if elfidesc is not None:
        try:
            elfidesc = wash_single_urlarg(urlarg=elfidesc, argreqdtype=str, argdefault="")
        except ValueError as e:
            elfidesc = ""
    else:
        elfidesc = ""
    if elmodifytext is not None:
        try:
            elmodifytext = wash_single_urlarg(urlarg=elmodifytext, argreqdtype=str, argdefault="")
        except ValueError as e:
            elmodifytext = ""
    else:
        elmodifytext = ""

    ## process request:
    if elcommit != "" and elcommit is not None:
        if elname == "":
            elname = ""
            user_msg.append("""Invalid Element Name!""")
            commit_error = 1
        if eltype == "" or eltype not in ("D", "F", "H", "I", "R", "S", "T"):
            eltype = ""
            user_msg.append("""Invalid Element Type!""")
            commit_error = 1

        if commit_error != 0:
            ## don't commit - just re-display page with message to user
            all_elements = get_elename_allelements()
            user_msg.append("""Could Not Update Element""")
            title = "Available WebSubmit Elements"
            body = websubmitadmin_templates.tmpl_display_allelements(all_elements, user_msg=user_msg)
            return (title, body)

        ## Commit updated element description to WebSubmit DB:
        err_code = update_element_details(elname=elname, elmarccode=elmarccode, eltype=eltype, \
                                          elsize=elsize, elrows=elrows, elcols=elcols, \
                                          elmaxlength=elmaxlength, elval=elval, elfidesc=elfidesc, \
                                          elmodifytext=elmodifytext)
        if err_code == 0:
            ## Element Updated: Show All Element Details Again
            user_msg.append("""'%s' Element Updated""" % (elname,))
            ## Get submission page usage of element:
            el_use = get_doctype_action_pagenb_for_submissions_using_element(elname)
            element_dets = get_element_details(elname)
            element_dets = stringify_listvars(element_dets)
            ## Take elements from results tuple:
            (elmarccode, eltype, elsize, elrows, elcols, elmaxlength, \
             elval, elfidesc, elcd, elmd, elmodifytext) = \
               (element_dets[0][0], element_dets[0][1], element_dets[0][2], element_dets[0][3], \
                element_dets[0][4], element_dets[0][5], element_dets[0][6], element_dets[0][7], \
                element_dets[0][8], element_dets[0][9], element_dets[0][10])
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
                                                                        perform_act="elementedit",
                                                                        user_msg=user_msg,
                                                                        el_use_tuple=el_use
                                                                       )
        else:
            ## Could Not Update Element: Maybe Key Violation, or Invalid elname? Redisplay all elements.
            ## TODO : LOGGING
            all_elements = get_elename_allelements()
            user_msg.append("""Could Not Update Element '%s'""" % (elname,))
            title = "Available WebSubmit Elements"
            body = websubmitadmin_templates.tmpl_display_allelements(all_elements, user_msg=user_msg)
    else:
        ## Display Web form containing existing details of element:
        element_dets = get_element_details(elname)
        ## Get submission page usage of element:
        el_use = get_doctype_action_pagenb_for_submissions_using_element(elname)
        num_rows_ret = len(element_dets)
        element_dets = stringify_listvars(element_dets)
        if num_rows_ret == 1:
            ## Display Element details
            ## Take elements from results tuple:
            (elmarccode, eltype, elsize, elrows, elcols, elmaxlength, \
             elval, elfidesc, elcd, elmd, elmodifytext) = \
               (element_dets[0][0], element_dets[0][1], element_dets[0][2], element_dets[0][3], \
                element_dets[0][4], element_dets[0][5], element_dets[0][6], element_dets[0][7], \
                element_dets[0][8], element_dets[0][9], element_dets[0][10])
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
                user_msg.append("""Found Several Rows for Element with Name '%s' - Inform Administrator""" % (elname,))
                ## LOG MESSAGE
            else:
                ## No rows for ELEMENT
                user_msg.append("""Could Not Find Any Rows for Element with Name '%s'""" % (elname,))
                ## LOG MESSAGE
            body = websubmitadmin_templates.tmpl_display_allelements(all_elements, user_msg=user_msg)
    return (title, body)

def _display_edit_check_form(chname, user_msg=""):
    title = "Edit WebSubmit Checking Function"
    if user_msg == "":
        user_msg = []
    jscheck_dets = get_jscheck_details(chname)
    num_rows_ret = len(jscheck_dets)
    if num_rows_ret == 1:
        ## Display Check details
        body = websubmitadmin_templates.tmpl_display_addjscheckform(chname=jscheck_dets[0][0],
                                                                    chdesc=jscheck_dets[0][1],
                                                                    perform_act="jscheckedit",
                                                                    cd=jscheck_dets[0][2],
                                                                    md=jscheck_dets[0][3],
                                                                    user_msg=user_msg)
    else:
        ## Either no rows, or more than one row for Check: log error, and display all Checks
        ## TODO : LOGGING
        title = "Available WebSubmit Checking Functions"
        all_jschecks = get_chname_alljschecks()
        if num_rows_ret > 1:
            ## Key Error - duplicated chname
            user_msg.append("""Found Several Rows for Checking Function with Name '%s' - Inform Administrator""" % (chname,))
            ## LOG MESSAGE
        else:
            ## No rows for action
            user_msg.append("""Could Not Find Any Rows for Checking Function with Name '%s'""" % (chname,))
            ## LOG MESSAGE
        body = websubmitadmin_templates.tmpl_display_alljschecks(all_jschecks, user_msg=user_msg)
    return (title, body)


def perform_request_edit_jscheck(chname, chdesc=None, chcommit=""):
    """Interface for editing and updating the details of a WebSubmit Check.
       If only "chname" provided, will display the details of a Check in a Web form.
       If "chdesc" not empty, will assume that this is a call to commit update to Check details.
       @param chname: unique id for Check
       @param chdesc: modified value for WebSubmit Check description (code body) - (presence invokes update)
       @return: tuple containing "title" (title of page), body (page body).
    """
    user_msg = []
    body = ""
    title = "Edit WebSubmit Checking Function"
    commit_error=0

    ## wash args:
    if chname is not None:
        try:
            chname = wash_single_urlarg(urlarg=chname, argreqdtype=str, argdefault="", maxstrlen=15, minstrlen=1)
            if function_name_is_valid(fname=chname) == 0:
                chname = ""
        except ValueError as e:
            chname = ""
    else:
        chname = ""
    if chdesc is not None:
        try:
            chdesc = wash_single_urlarg(urlarg=chdesc, argreqdtype=str, argdefault="")
        except ValueError as e:
            chdesc = ""
    else:
        chdesc = ""
    (chname, chdesc) = (str(chname), str(chdesc))

    if chcommit != "" and chcommit is not None:
        if chname in ("", None):
            chname = ""
            user_msg.append("""Check name is mandatory and must be a string with no more than 15 characters""")
            user_msg.append("""It must contain only alpha-numeric and underscore characters, beginning with a """\
                            """letter or underscore""")
            commit_error = 1

        if commit_error != 0:
            ## don't commit - just re-display page with message to user
            all_jschecks = get_chname_alljschecks()
            user_msg.append("""Could Not Update Checking Function""")
            body = websubmitadmin_templates.tmpl_display_alljschecks(all_jschecks, user_msg=user_msg)
            title = "Available WebSubmit Checking Functions"
            return (title, body)

        ## Commit updated Check details to WebSubmit DB:
        err_code = update_jscheck_details(chname, chdesc)
        if err_code == 0:
            ## Check Updated: Show All Check Details Again
            user_msg.append("""'%s' Check Updated""" % (chname,))
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
            user_msg.append("""Could Not Update Checking Function '%s'""" % (chname,))
            body = websubmitadmin_templates.tmpl_display_alljschecks(all_jschecks, user_msg=user_msg)
            title = "Available WebSubmit Checking Functions"
    else:
        ## Display Web form containing existing details of Check:
        (title, body) = _display_edit_check_form(chname=chname)
    return (title, body)

def _display_edit_action_form(actid, user_msg=""):
    title = "Edit WebSubmit Action"
    if user_msg == "":
        user_msg = []
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
                                                                   md=action_dets[0][5],
                                                                   user_msg=user_msg)
    else:
        ## Either no rows, or more than one row for action: log error, and display all actions
        ## TODO : LOGGING
        title = "Available WebSubmit Actions"
        all_actions = get_actid_actname_allactions()
        if num_rows_ret > 1:
            ## Key Error - duplicated actid
            user_msg.append("""Found Several Rows for Action with ID '%s' - Inform Administrator""" % (actid,))
            ## LOG MESSAGE
        else:
            ## No rows for action
            user_msg.append("""Could Not Find Any Rows for Action with ID '%s'""" % (actid,))
            ## LOG MESSAGE
        body = websubmitadmin_templates.tmpl_display_allactions(all_actions, user_msg=user_msg)
    return (title, body)

def perform_request_edit_action(actid, actname=None, working_dir=None, status_text=None, actcommit=""):
    """Interface for editing and updating the details of a WebSubmit action.
       If only "actid" provided, will display the details of an action in a Web form.
       If "actname" not empty, will assume that this is a call to commit update to action details.
       @param actid: unique id for action
       @param actname: modified value for WebSubmit action name/description (presence invokes update)
       @param working_dir: modified value for WebSubmit action working_dir
       @param status_text: modified value for WebSubmit action status text
       @return: tuple containing "title" (title of page), body (page body).
    """
    user_msg = []
    body = ""
    title = "Edit WebSubmit Action"
    commit_error = 0

    ## wash args:
    if actid is not None:
        try:
            actid = wash_single_urlarg(urlarg=actid, argreqdtype=str, argdefault="", maxstrlen=3, minstrlen=3)
            if string_is_alphanumeric_including_underscore(txtstring=actid) == 0:
                actid = ""
        except ValueError as e:
            actid = ""
        actid = actid.upper()
    else:
        actid = ""
    if actname is not None:
        try:
            actname = wash_single_urlarg(urlarg=actname, argreqdtype=str, argdefault="")
        except ValueError as e:
            actname = ""
    else:
        actname = ""
    if working_dir is not None:
        try:
            working_dir = wash_single_urlarg(urlarg=working_dir, argreqdtype=str, argdefault="")
        except ValueError as e:
            working_dir = ""
    else:
        working_dir = ""
    if status_text is not None:
        try:
            status_text = wash_single_urlarg(urlarg=status_text, argreqdtype=str, argdefault="")
        except ValueError as e:
            status_text = ""
    else:
        status_text = ""

    ## process request:
    if actcommit != "" and actcommit is not None:
        if actname in ("", None):
            actname = ""
            user_msg.append("""Action description is mandatory""")
            commit_error = 1

        if commit_error != 0:
            ## don't commit - just re-display page with message to user
            (title, body) = _display_edit_action_form(actid=actid, user_msg=user_msg)
            return (title, body)

        ## Commit updated action details to WebSubmit DB:
        err_code = update_action_details(actid, actname, working_dir, status_text)
        if err_code == 0:
            ## Action Updated: Show Action Details Again
            user_msg.append("""'%s' Action Updated""" % (actid,))
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
            user_msg.append("""Could Not Update Action '%s'""" % (actid,))
            body = websubmitadmin_templates.tmpl_display_allactions(all_actions, user_msg=user_msg)
            title = "Available WebSubmit Actions"
    else:
        ## Display Web form containing existing details of action:
        (title, body) = _display_edit_action_form(actid=actid)
    return (title, body)

def _functionedit_display_function_details(funcname, user_msg=""):
    """Display the details of a function, along with any message to the user that may have been provided.
       @param funcname: unique name of function to be updated
       @param user_msg: Any message to the user that is to be displayed on the page.
       @return: tuple containing (page title, HTML page body).
    """
    if user_msg == "":
        user_msg = []
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

        ## get the docstring of the function. Remove leading empty
        ## lines and remove unnecessary leading whitespaces
        docstring = None
        try:
            websubmit_function = __import__('invenio.legacy.websubmit.functions.%s' % funcname,
                                            globals(), locals(), [funcname])
            if hasattr(websubmit_function, funcname) and getattr(websubmit_function, funcname).__doc__:
                docstring = getattr(websubmit_function, funcname).__doc__
        except Exception as e:
            docstring = '''<span style="color:#f00;font-weight:700">Function documentation could
            not be loaded</span>.<br/>Please check function definition. Error was:<br/>%s''' % str(e)

        if docstring:
            docstring = '<pre style="max-height:500px;overflow: auto;">' + _format_function_docstring(docstring) + '</pre>'

        body = websubmitadmin_templates.tmpl_display_addfunctionform(funcname=funcname,
                                                                     funcdescr=funcdescr,
                                                                     func_parameters=this_function_parameters,
                                                                     all_websubmit_func_parameters=all_function_parameters,
                                                                     perform_act="functionedit",
                                                                     user_msg=user_msg,
                                                                     func_docstring = docstring
                                                                    )

    else:
        ## Either no rows, or more than one row for function: log error, and display all functions
        ## TODO : LOGGING
        title = "Available WebSubmit Functions"
        all_functions = get_funcname_funcdesc_allfunctions()
        if num_rows_ret > 1:
            ## Key Error - duplicated function name
            user_msg.append("""Found Several Rows for Function with Name '%s' - Inform Administrator""" % (funcname,))
            ## LOG MESSAGE
        else:
            ## No rows for function
            user_msg.append("""Could Not Find Any Rows for Function with Name '%s'""" % (funcname,))
            ## LOG MESSAGE
        body = websubmitadmin_templates.tmpl_display_allfunctions(all_functions, user_msg=user_msg)
    return (title, body)

def _format_function_docstring(docstring):
    """
    Remove unnecessary leading and trailing empty lines, as well as
    meaningless leading and trailing whitespaces on every lines

    @param docstring: the input docstring to format
    @type docstring: string
    @return: a formatted docstring
    @rtype: string
    """
    def count_leading_whitespaces(line):
        "Count enumber of leading whitespaces"
        line_length = len(line)
        pos = 0
        while pos < line_length and line[pos] == " ":
            pos += 1
        return pos

    new_docstring_list = []
    min_nb_leading_whitespace = len(docstring) # this is really the max possible

    # First count min number of leading whitespaces of all lines. Also
    # remove leading empty lines.
    docstring_has_started_p = False
    for line in docstring.splitlines():
        if docstring_has_started_p or line.strip():
            # A non-empty line has been found, or an emtpy line after
            # the beginning of some text was found
            docstring_has_started_p = True
            new_docstring_list.append(line)
            if line.strip():
                # If line has some meaningful char, count leading whitespaces
                line_nb_spaces = count_leading_whitespaces(line)
                if line_nb_spaces < min_nb_leading_whitespace:
                    min_nb_leading_whitespace = line_nb_spaces

    return '\n'.join([line[min_nb_leading_whitespace:] for line in new_docstring_list]).rstrip()

def _functionedit_update_description(funcname, funcdescr):
    """Perform an update of the description for a given function.
       @param funcname: unique name of function to be updated
       @param funcdescr: description to be updated for funcname
       @return: a tuple containing (page title, HTML body content)
    """
    user_msg = []
    err_code = update_function_description(funcname, funcdescr)
    if err_code == 0:
        ## Function updated - redisplay
        user_msg.append("""'%s' Function Description Updated""" % (funcname,))
    else:
        ## Could not update function description
# TODO : ERROR LIBS
        user_msg.append("""Could Not Update Description for Function '%s'""" % (funcname,))
    ## Display function details
    (title, body) = _functionedit_display_function_details(funcname=funcname, user_msg=user_msg)
    return (title, body)

def _functionedit_delete_parameter(funcname, deleteparam):
    """Delete a parameter from a given function.
       Important: if any document types have been using the function from which this parameter will be deleted,
        and therefore have values for this parameter, these values will not be deleted from the WebSubmit DB.
        The deleted parameter therefore may continue to exist in the WebSubmit DB, but will be disassociated
        from this function.
       @param funcname: unique name of the function from which the parameter is to be deleted.
       @param deleteparam: the name of the parameter to be deleted from the function.
       @return: tuple containing (title, HTML body content)
    """
    user_msg = []
    err_code = delete_function_parameter(function=funcname, parameter_name=deleteparam)
    if err_code == 0:
        ## Parameter deleted - redisplay function details
        user_msg.append("""'%s' Parameter Deleted from '%s' Function""" % (deleteparam, funcname))
    else:
        ## could not delete param - it does not exist for this function
# TODO : ERROR LIBS
        user_msg.append("""'%s' Parameter Does not Seem to Exist for Function '%s' - Could not Delete""" \
                   % (deleteparam, funcname))
    ## Display function details
    (title, body) = _functionedit_display_function_details(funcname=funcname, user_msg=user_msg)
    return (title, body)

def _functionedit_add_parameter(funcname, funceditaddparam="", funceditaddparamfree=""):
    """Add (connect) a parameter to a given WebSubmit function.
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
    user_msg = []
    if funceditaddparam in ("", None, "NO_VALUE") and funceditaddparamfree in ("", None):
        ## no parameter chosen
# TODO : ERROR LIBS
        user_msg.append("""Unable to Find the Parameter to be Added to Function '%s' - Could not Add""" % (funcname,))
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
            user_msg.append("""'%s' Parameter Added to '%s' Function""" % (add_parameter, funcname))
        else:
            ## could not add param - perhaps it already exists for this function
# TODO : ERROR LIBS
            user_msg.append("""Could not Add '%s' Parameter to Function '%s' - It Already Exists for this Function""" \
                       % (add_parameter, funcname))
    ## Display function details
    (title, body) = _functionedit_display_function_details(funcname=funcname, user_msg=user_msg)
    return (title, body)

def perform_request_edit_function(funcname, funcdescr=None, funceditaddparam=None, funceditaddparamfree=None,
                                  funceditdelparam=None, funcdescreditcommit="", funcparamdelcommit="",
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
        @return: tuple containing (page title, HTML page body)
    """
    body = ""
    title = "Edit WebSubmit Function"
    commit_error = 0

    ## wash args:
    if funcname is not None:
        try:
            funcname = wash_single_urlarg(urlarg=funcname, argreqdtype=str, argdefault="")
            if string_is_alphanumeric_including_underscore(txtstring=funcname) == 0:
                funcname = ""
        except ValueError as e:
            funcname = ""
    else:
        funcname = ""
    if funcdescr is not None:
        try:
            funcdescr = wash_single_urlarg(urlarg=funcdescr, argreqdtype=str, argdefault="")
        except ValueError as e:
            funcdescr = ""
    else:
        funcdescr = ""
    if funceditaddparam is not None:
        try:
            funceditaddparam = wash_single_urlarg(urlarg=funceditaddparam, argreqdtype=str, argdefault="")
            if string_is_alphanumeric_including_underscore(txtstring=funceditaddparam) == 0:
                funceditaddparam = ""
        except ValueError as e:
            funceditaddparam = ""
    else:
        funceditaddparam = ""
    if funceditaddparamfree is not None:
        try:
            funceditaddparamfree = wash_single_urlarg(urlarg=funceditaddparamfree, argreqdtype=str, argdefault="")
            if string_is_alphanumeric_including_underscore(txtstring=funceditaddparamfree) == 0:
                funceditaddparamfree = ""
        except ValueError as e:
            funceditaddparamfree = ""
    else:
        funceditaddparamfree = ""
    if funceditdelparam is not None:
        try:
            funceditdelparam = wash_single_urlarg(urlarg=funceditdelparam, argreqdtype=str, argdefault="")
        except ValueError as e:
            funceditdelparam = ""
    else:
        funceditdelparam = ""

    if funcname == "":
        (title, body) = _functionedit_display_function_details(funcname=funcname)
        return (title, body)

    if funcdescreditcommit != "" and funcdescreditcommit is not None:
        ## Update the definition of a function:
        (title, body) = _functionedit_update_description(funcname=funcname, funcdescr=funcdescr)
    elif funcparamaddcommit != "" and funcparamaddcommit is not None:
        ## Request to add a new parameter to a function
        (title, body) = _functionedit_add_parameter(funcname=funcname,
                                                    funceditaddparam=funceditaddparam, funceditaddparamfree=funceditaddparamfree)
    elif funcparamdelcommit != "" and funcparamdelcommit is not None:
        ## Request to delete a parameter from a function
        (title, body) = _functionedit_delete_parameter(funcname=funcname, deleteparam=funceditdelparam)
    else:
        ## Display Web form for new function addition:
        (title, body) = _functionedit_display_function_details(funcname=funcname)
    return (title, body)

def perform_request_function_usage(funcname):
    """Display a page containing the usage details of a given function.
       @param funcname: the function name
       @return: page body
    """
    func_usage = get_function_usage_details(function=funcname)
    func_usage = stringify_listvars(func_usage)
    body = websubmitadmin_templates.tmpl_display_function_usage(funcname, func_usage)
    return body

def perform_request_list_actions():
    """Display a list of all WebSubmit actions.
       @return: body where body is a string of HTML, which is a page body.
    """
    body = ""
    all_actions = get_actid_actname_allactions()
    body = websubmitadmin_templates.tmpl_display_allactions(all_actions)
    return body

def perform_request_list_doctypes():
    """Display a list of all WebSubmit document types.
       @return: body where body is a string of HTML, which is a page body.
    """
    body = ""
    all_doctypes = get_docid_docname_alldoctypes()
    body = websubmitadmin_templates.tmpl_display_alldoctypes(all_doctypes)
    return body

def perform_request_list_jschecks():
    """Display a list of all WebSubmit JavaScript element checking functions.
       @return: body, where body is a string of HTML, which is a page body.
    """
    body = ""
    all_jschecks = get_chname_alljschecks()
    body = websubmitadmin_templates.tmpl_display_alljschecks(all_jschecks)
    return body

def perform_request_list_functions():
    """Display a list of all WebSubmit FUNCTIONS.
       @return: body where  body is a string of HTML, which is a page body.
    """
    body = ""
    all_functions = get_funcname_funcdesc_allfunctions()
    body = websubmitadmin_templates.tmpl_display_allfunctions(all_functions)
    return body

def perform_request_list_elements():
    """Display a list of all WebSubmit ELEMENTS.
       @return: body where body is a string of HTML, which is a page body.
    """
    body = ""
    all_elements = get_elename_allelements()
    body = websubmitadmin_templates.tmpl_display_allelements(all_elements)
    return body

def _remove_doctype(doctype):
    """Process removal of a document type.
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
       @return: a tuple (title, body)
    """
    body = ""
    title = "Remove WebSubmit Document Type"
    if doctypedeleteconfirm not in ("", None):
        ## Delete the document type:
        (title, body) = _remove_doctype(doctype=doctype)
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
    return (title, body)

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

def _clone_categories_doctype(user_msg, fromdoctype, todoctype):
    """Clone the categories of one document type, to another document type.
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

def _clone_functions_foraction_doctype(user_msg, fromdoctype, todoctype, action):
    """Clone the functions of a given action of one document type, to the same action on another document type.
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
                        % (action, todoctype, fromdoctype, action))
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

def _clone_functionparameters_foraction_fromdoctype_todoctype(user_msg, fromdoctype, todoctype, action):
    """Clone the parameters/values of a given action of one document type, to the same action on another document type.
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

def _add_doctype(doctype, doctypename, doctypedescr, clonefrom):
    title = ""
    body = ""
    user_msg = []
    commit_error = 0
    if doctype == "":
        user_msg.append("""The Document Type ID is mandatory and must be a string with no more than 10 alpha-numeric characters""")
        commit_error = 1

    if commit_error != 0:
        ## don't commit - just re-display page with message to user
        (title, body) = _create_add_doctype_form(doctypename=doctypename, doctypedescr=doctypedescr, clonefrom=clonefrom, user_msg=user_msg)
        return (title, body)


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
                error_code = _clone_categories_doctype(user_msg=user_msg,
                                                       fromdoctype=clonefrom,
                                                       todoctype=doctype)
                ## get details of clonefrom's submissions
                all_actnames_submissions_clonefrom = get_actname_all_submissions_doctype(doctype=clonefrom)
                if len(all_actnames_submissions_clonefrom) > 0:
                    ## begin cloning
                    for doc_submission_actname in all_actnames_submissions_clonefrom:
                        ## clone submission details:
                        action_name = doc_submission_actname[0]
                        _clone_submission_fromdoctype_todoctype(user_msg=user_msg,
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

def perform_request_add_doctype(doctype=None, doctypename=None, doctypedescr=None, clonefrom=None, doctypedetailscommit=""):
    body = ""

    ## wash args:
    if doctype is not None:
        try:
            doctype = wash_single_urlarg(urlarg=doctype, argreqdtype=str, argdefault="", maxstrlen=10, minstrlen=1)
            if string_is_alphanumeric_including_underscore(txtstring=doctype) == 0:
                doctype = ""
        except ValueError as e:
            doctype = ""
    else:
        doctype = ""
    if doctypename is not None:
        try:
            doctypename = wash_single_urlarg(urlarg=doctypename, argreqdtype=str, argdefault="")
        except ValueError as e:
            doctypename = ""
    else:
        doctypename = ""
    if doctypedescr is not None:
        try:
            doctypedescr = wash_single_urlarg(urlarg=doctypedescr, argreqdtype=str, argdefault="")
        except ValueError as e:
            doctypedescr = ""
    else:
        doctypedescr = ""
    if clonefrom is not None:
        try:
            clonefrom = wash_single_urlarg(urlarg=clonefrom, argreqdtype=str, argdefault="None")
        except ValueError as e:
            clonefrom = "None"
    else:
        clonefrom = "None"

    if doctypedetailscommit not in ("", None):
        (title, body) = _add_doctype(doctype=doctype,
                                     doctypename=doctypename, doctypedescr=doctypedescr, clonefrom=clonefrom)
    else:
        (title, body) = _create_add_doctype_form()
    return (title, body)

def _delete_referee_doctype(doctype, categid, refereeid):
    """Delete a referee from a given category of a document type.
       @param doctype: the document type from whose category the referee is to be removed
       @param categid: the name/ID of the category from which the referee is to be removed
       @param refereeid: the id of the referee to be removed from the given category
       @return: a tuple containing 2 strings: (page title, page body)
    """
    user_msg = []
    role_name = """referee_%s_%s""" % (doctype, categid)
    error_code = acc_delete_user_role(id_user=refereeid, name_role=role_name)
    if error_code > 0:
        ## referee was deleted from category
        user_msg.append(""" "%s".""" % (doctype,))

def _create_list_referees_doctype(doctype):
    referees = {}
    referees_details = {}
    ## get all Invenio roles:
    all_roles = acc_get_all_roles()
    for role in all_roles:
        (roleid, rolename) = (role[0], role[1])
        if re.match("^referee_%s_" % (doctype,), rolename):
            ## this is a "referee" role - get users of this role:
            role_users = acc_get_role_users(roleid)
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

def _create_edit_doctype_details_form(doctype, doctypename="", doctypedescr="", doctypedetailscommit="", user_msg=""):
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

def _create_add_submission_choose_clonefrom_form(doctype, action, user_msg=""):
    if user_msg == "" or type(user_msg) not in (list, tuple, str, unicode):
        user_msg = []
    elif type(user_msg) in (str, unicode):
        user_msg = [user_msg]

    if action in ("", None):
        user_msg.append("""Unknown Submission""")
        (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
        return (title, body)

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

def _create_add_submission_form(doctype, action, displayed="", buttonorder="", statustext="",
                                level="", score="", stpage="", endtxt="", user_msg=""):
    if user_msg == "" or type(user_msg) not in (list, tuple, str, unicode):
        user_msg = []
    elif type(user_msg) in (str, unicode):
        user_msg = [user_msg]

    if action in ("", None):
        user_msg.append("""Unknown Submission""")
        (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
        return (title, body)

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

def _create_delete_submission_form(doctype, action):
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

def _create_edit_submission_form(doctype, action, user_msg=""):
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
        (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
    return (title, body)

def _create_edit_category_form(doctype, categid):
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

def _create_configure_doctype_form(doctype, jumpcategout="", user_msg=""):
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
    doctype_categs = get_all_category_details_for_doctype(doctype=doctype)

    ## get submissions for doctype:
    doctype_submissions = get_submissiondetails_all_submissions_doctype(doctype=doctype)
    ## get list of actions that this doctype doesn't have:
    unlinked_actions = get_actions_sname_lname_not_linked_to_doctype(doctype=doctype)
    ## get referees for doctype:
    referees_dets = _create_list_referees_doctype(doctype=doctype)
    body = websubmitadmin_templates.tmpl_configure_doctype_overview(doctype=doctype, doctypename=docname,
                                                                    doctypedescr=docdescr, doctype_cdate=cd,
                                                                    doctype_mdate=md, doctype_categories=doctype_categs,
                                                                    jumpcategout=jumpcategout,
                                                                    doctype_submissions=doctype_submissions,
                                                                    doctype_referees=referees_dets,
                                                                    add_actions_list=unlinked_actions,
                                                                    user_msg=user_msg)
    return (title, body)

def _clone_submission_fromdoctype_todoctype(user_msg, todoctype, action, clonefrom):
    ## first, delete the submission from todoctype (if it exists):
    error_code = delete_submissiondetails_doctype(doctype=todoctype, action=action)
    if error_code == 0:
        ## could be deleted - now clone it
        error_code = insert_submission_details_clonefrom_submission(addtodoctype=todoctype, action=action, clonefromdoctype=clonefrom)
        if error_code == 0:
            ## submission inserted
            ## now clone functions:
            error_code = _clone_functions_foraction_doctype(user_msg=user_msg, \
                                    fromdoctype=clonefrom, todoctype=todoctype, action=action)
            if error_code in (0, 2):
                ## no serious error - clone parameters:
                error_code = _clone_functionparameters_foraction_fromdoctype_todoctype(user_msg=user_msg,
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

def _add_submission_to_doctype_clone(doctype, action, clonefrom):
    user_msg = []

    if action in ("", None) or clonefrom in ("", None):
        user_msg.append("Unknown action or document type to clone from - cannot add submission")
        (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
        return (title, body)

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
            _clone_submission_fromdoctype_todoctype(user_msg=user_msg,
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

def _add_submission_to_doctype(doctype, action, displayed, buttonorder,
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

def _delete_submission_from_doctype(doctype, action):
    """Delete a submission (action) from the document type identified by "doctype".
       @param doctype: the unique ID of the document type from which the submission is to be deleted
       @param categid: the action ID of the submission to be deleted from doctype
       @return: a tuple containing 2 strings: (page title, page body)
    """
    user_msg = []

    if action in ("", None):
        user_msg.append("Unknown action - cannot delete submission")
        (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
        return (title, body)

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

def _edit_submission_for_doctype(doctype, action, displayed, buttonorder,
                                 statustext, level, score, stpage, endtxt):
    """Update the details of a given submission belonging to the document type identified by "doctype".
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
    commit_error = 0
    if action in ("", None):
        user_msg.append("Unknown Action - cannot update submission")
        (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
        return (title, body)

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

def _edit_doctype_details(doctype, doctypename, doctypedescr):
    """Update the details (name and/or description) of a document type (identified by doctype.)
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

def _edit_category_for_doctype(doctype, categid, categdescr):
    """Edit the description of a given category (identified by categid), belonging to
       the document type identified by doctype.
       @param doctype: the unique ID of the document type for which the category is to be modified
       @param categid: the unique category ID of the category to be modified
       @param categdescr: the new description for the category
       @return: at tuple containing 2 strings: (page title, page body)
    """
    user_msg = []

    if categid in ("", None) or categdescr in ("", None):
        ## cannot edit unknown category!
        user_msg.append("Category ID and Description are both mandatory")
        (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
        return (title, body)

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

def _add_category_to_doctype(doctype, categid, categdescr):
    """Add a new category to the document type identified by "doctype".
       Category ID, and category description are both mandatory.
       @param doctype: the unique ID of the document type to which the category is to be added
       @param categid: the unique category ID of the category to be added to doctype
       @param categdescr: the description of the category to be added
       @return: at tuple containing 2 strings: (page title, page body)
    """
    user_msg = []

    if categid in ("", None) or categdescr in ("", None):
        ## cannot add unknown category!
        user_msg.append("Category ID and Description are both mandatory")
        (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
        return (title, body)

    error_code = insert_category_into_doctype(doctype=doctype, categ=categid, categdescr=categdescr)
    if error_code == 0:
        ## successful insert
        user_msg.append("""'%s' Category Successfully Added""" % (categid,))
    else:
        ## could not insert category into doctype
        user_msg.append("""Unable to Add '%s' Category""" % (categid,))
        ## TODO : LOG ERROR
    (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
    return (title, body)

def _delete_category_from_doctype(doctype, categid):
    """Delete a category (categid) from the document type identified by "doctype".
       @param doctype: the unique ID of the document type from which the category is to be deleted
       @param categid: the unique category ID of the category to be deleted from doctype
       @return: a tuple containing 2 strings: (page title, page body)
    """
    user_msg = []

    if categid in ("", None):
        ## cannot delete unknown category!
        user_msg.append("Category ID is mandatory")
        (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
        return (title, body)

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

def _jump_category_to_new_score(doctype, jumpcategout, jumpcategin):
    user_msg = []
    if jumpcategout in ("", None) or jumpcategin in ("", None):
        ## need both jumpcategout and jumpcategin to move a category:
        user_msg.append("Unable to move category - unknown source and/or destination score(s)")
        (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
        return (title, body)
    ## FIXME TODO:
    error_code = move_category_to_new_score(doctype, jumpcategout, jumpcategin)

    if error_code == 0:
        ## successful jump of category
        user_msg.append("""Successfully Moved [%s] Category""" % (jumpcategout,))
    else:
        ## could not delete category
        user_msg.append("""Unable to Move [%s] Category""" % (jumpcategout,))
        ## TODO : LOG ERROR
    (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
    return (title, body)

def _move_category(doctype, categid, movecategup=""):
    user_msg = []
    if categid in ("", None):
        ## cannot move unknown category!
        user_msg.append("Cannot move an unknown category - category ID is mandatory")
        (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
        return (title, body)

    if movecategup not in ("", None):
        ## move the category up in score:
        error_code = move_category_by_one_place_in_score(doctype=doctype,
                                                         categsname=categid,
                                                         direction="up")
    else:
        ## move the category down in score:
        error_code = move_category_by_one_place_in_score(doctype=doctype,
                                                         categsname=categid,
                                                         direction="down")

    if error_code == 0:
        ## successful move of category
        user_msg.append("""[%s] Category Successfully Moved""" % (categid,))
    else:
        ## could not delete category
        user_msg.append("""Unable to Move [%s] Category""" % (categid,))
        ## TODO : LOG ERROR
    (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
    return (title, body)

def perform_request_configure_doctype(doctype,
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
                                      doctypesubmissionadddetailscommit="",
                                      doctypesubmissioneditdetailscommit="",
                                      categid=None,
                                      categdescr=None,
                                      movecategup=None,
                                      movecategdown=None,
                                      jumpcategout=None,
                                      jumpcategin=None,
                                      action=None,
                                      doctype_cloneactionfrom=None,
                                      displayed=None,
                                      buttonorder=None,
                                      statustext=None,
                                      level=None,
                                      score=None,
                                      stpage=None,
                                      endtxt=None
                                     ):
    user_msg = []
    body = ""

    if doctype is not None:
        try:
            doctype = wash_single_urlarg(urlarg=doctype, argreqdtype=str, argdefault="", maxstrlen=10, minstrlen=1)
            if string_is_alphanumeric_including_underscore(txtstring=doctype) == 0:
                doctype = ""
        except ValueError as e:
            doctype = ""
    else:
        doctype = ""
    if action is not None:
        try:
            action = wash_single_urlarg(urlarg=action, argreqdtype=str, argdefault="", maxstrlen=3, minstrlen=1)
            if string_is_alphanumeric_including_underscore(txtstring=action) == 0:
                action = ""
        except ValueError as e:
            action = ""
    else:
        action = ""
    if doctypename is not None:
        try:
            doctypename = wash_single_urlarg(urlarg=doctypename, argreqdtype=str, argdefault="")
        except ValueError as e:
            doctypename = ""
    else:
        doctypename = ""
    if doctypedescr is not None:
        try:
            doctypedescr = wash_single_urlarg(urlarg=doctypedescr, argreqdtype=str, argdefault="")
        except ValueError as e:
            doctypedescr = ""
    else:
        doctypedescr = ""
    if categid is not None:
        try:
            categid = wash_single_urlarg(urlarg=categid, argreqdtype=str, argdefault="")
        except ValueError as e:
            categid = ""
    else:
        categid = ""
    if categdescr is not None:
        try:
            categdescr = wash_single_urlarg(urlarg=categdescr, argreqdtype=str, argdefault="")
        except ValueError as e:
            categdescr = ""
    else:
        categdescr = ""
    if doctype_cloneactionfrom is not None:
        try:
            doctype_cloneactionfrom = wash_single_urlarg(urlarg=doctype_cloneactionfrom, argreqdtype=str, argdefault="", maxstrlen=10, minstrlen=1)
            if string_is_alphanumeric_including_underscore(txtstring=doctype_cloneactionfrom) == 0:
                doctype_cloneactionfrom = ""
        except ValueError as e:
            doctype_cloneactionfrom = ""
    else:
        doctype_cloneactionfrom = ""
    if displayed is not None:
        try:
            displayed = wash_single_urlarg(urlarg=displayed, argreqdtype=str, argdefault="Y", maxstrlen=1, minstrlen=1)
        except ValueError as e:
            displayed = "Y"
    else:
        displayed = "Y"
    if buttonorder is not None:
        try:
            buttonorder = wash_single_urlarg(urlarg=buttonorder, argreqdtype=int, argdefault="")
        except ValueError as e:
            buttonorder = ""
    else:
        buttonorder = ""
    if level is not None:
        try:
            level = wash_single_urlarg(urlarg=level, argreqdtype=str, argdefault="", maxstrlen=1, minstrlen=1)
        except ValueError as e:
            level = ""
    else:
        level = ""
    if score is not None:
        try:
            score = wash_single_urlarg(urlarg=score, argreqdtype=int, argdefault="")
        except ValueError as e:
            score = ""
    else:
        score = ""
    if stpage is not None:
        try:
            stpage = wash_single_urlarg(urlarg=stpage, argreqdtype=int, argdefault="")
        except ValueError as e:
            stpage = ""
    else:
        stpage = ""
    if statustext is not None:
        try:
            statustext = wash_single_urlarg(urlarg=statustext, argreqdtype=str, argdefault="")
        except ValueError as e:
            statustext = ""
    else:
        statustext = ""
    if endtxt is not None:
        try:
            endtxt = wash_single_urlarg(urlarg=endtxt, argreqdtype=str, argdefault="")
        except ValueError as e:
            endtxt = ""
    else:
        endtxt = ""

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
        return (title, body)
    elif numrows_doctype == 0:
        ## this doctype does not seem to exist:
        user_msg.append("""The document type identified by "%s" doesn't exist - cannot configure at this time.""" \
                   % (doctype,))
        ## TODO : LOG ERROR
        all_doctypes = get_docid_docname_alldoctypes()
        body = websubmitadmin_templates.tmpl_display_alldoctypes(doctypes=all_doctypes, user_msg=user_msg)
        title = "Available WebSubmit Document Types"
        return (title, body)

    ## since doctype ID is OK, process doctype configuration request:
    if doctypedetailsedit not in ("", None):
        (title, body) = _create_edit_doctype_details_form(doctype=doctype)
    elif doctypedetailscommit not in ("", None):
        ## commit updated document type details
        (title, body) = _edit_doctype_details(doctype=doctype,
                                              doctypename=doctypename, doctypedescr=doctypedescr)
    elif doctypecategoryadd not in ("", None):
        ## add new category:
        (title, body) = _add_category_to_doctype(doctype=doctype, categid=categid, categdescr=categdescr)
    elif doctypecategoryedit not in ("", None):
        ## create form to update category description:
        (title, body) = _create_edit_category_form(doctype=doctype,
                                                   categid=categid)
    elif doctypecategoryeditcommit not in ("", None):
        ## commit updated category description:
        (title, body) = _edit_category_for_doctype(doctype=doctype, categid=categid, categdescr=categdescr)
    elif doctypecategorydelete not in ("", None):
        ## delete a category
        (title, body) = _delete_category_from_doctype(doctype=doctype, categid=categid)
    elif movecategup not in ("", None) or movecategdown not in ("", None):
        ## move a category up or down in score:
        (title, body) = _move_category(doctype=doctype, categid=categid,
                                       movecategup=movecategup)
    elif jumpcategout not in ("", None) and jumpcategin not in ("", None):
        ## jump a category from one score to another:
        (title, body) = _jump_category_to_new_score(doctype=doctype, jumpcategout=jumpcategout,
                                                    jumpcategin=jumpcategin)
    elif doctypesubmissionadd not in ("", None):
        ## form displaying option of adding doctype:
        (title, body) = _create_add_submission_choose_clonefrom_form(doctype=doctype, action=action)
    elif doctypesubmissionaddclonechosen not in ("", None):
        ## add a submission. if there is a document type to be cloned from, then process clone;
        ## otherwise, present form with details of doctype
        if doctype_cloneactionfrom in ("", None, "None"):
            ## no clone - present form into which details of new submission should be entered
            (title, body) = _create_add_submission_form(doctype=doctype, action=action)
        else:
            ## new submission should be cloned from doctype_cloneactionfrom
            (title, body) = _add_submission_to_doctype_clone(doctype=doctype, action=action, clonefrom=doctype_cloneactionfrom)
    elif doctypesubmissiondelete not in ("", None):
        ## create form to prompt for confirmation of deletion of a submission:
        (title, body) = _create_delete_submission_form(doctype=doctype, action=action)
    elif doctypesubmissiondeleteconfirm not in ("", None):
        ## process the deletion of a submission from the doctype concerned:
        (title, body) = _delete_submission_from_doctype(doctype=doctype, action=action)
    elif doctypesubmissionedit not in ("", None):
        ## create form to update details of a submission
        (title, body) = _create_edit_submission_form(doctype=doctype, action=action)
    elif doctypesubmissioneditdetailscommit not in ("", None):
        ## commit updated submission details:
        (title, body) = _edit_submission_for_doctype(doctype=doctype, action=action,
                                                     displayed=displayed, buttonorder=buttonorder, statustext=statustext,
                                                     level=level, score=score, stpage=stpage, endtxt=endtxt)
    elif doctypesubmissionadddetailscommit not in ("", None):
        ## commit new submission to doctype (not by cloning)
        (title, body) = _add_submission_to_doctype(doctype=doctype, action=action,
                                                   displayed=displayed, buttonorder=buttonorder, statustext=statustext,
                                                   level=level, score=score, stpage=stpage, endtxt=endtxt)
    else:
        ## default - display root of edit doctype
        (title, body) = _create_configure_doctype_form(doctype=doctype, jumpcategout=jumpcategout)
    return (title, body)

def _create_configure_doctype_submission_functions_form(doctype,
                                                        action,
                                                        movefromfunctionname="",
                                                        movefromfunctionstep="",
                                                        movefromfunctionscore="",
                                                        user_msg=""):
    title = """Functions of the "%s" Submission of the "%s" Document Type:""" % (action, doctype)
    submission_functions = get_functionname_step_score_allfunctions_doctypesubmission(doctype=doctype, action=action)
    body = websubmitadmin_templates.tmpl_configuredoctype_display_submissionfunctions(doctype=doctype,
                                                                                      action=action,
                                                                                      movefromfunctionname=movefromfunctionname,
                                                                                      movefromfunctionstep=movefromfunctionstep,
                                                                                      movefromfunctionscore=movefromfunctionscore,
                                                                                      submissionfunctions=submission_functions,
                                                                                      user_msg=user_msg)
    return (title, body)

def _create_configure_doctype_submission_functions_add_function_form(doctype, action, addfunctionname="",
                                                                     addfunctionstep="", addfunctionscore="", user_msg=""):
    """Create a form that allows a user to add a function a submission.
       @param doctype: (string) the unique ID of a document type
       @param action: (string) the unique ID of an action
       @param addfunctionname: (string) the name of the function to be added to the submission (passed in case of page refresh)
       @param addfunctionstep: (integer) the step of the submission into which the function is to be added (passed in case of
        page refresh)
       @param addfunctionscore: (integer) the score at at which the function is to be added (passed in case of page refresh)
       @param user_msg: (string or list of strings) any message(s) to be displayed to the user
       @return: (tuple) containing 2 strings - (page-title, HTML page-body)
    """
    title = """Add a function to the [%s] submission of the [%s] document type""" % (action, doctype)
    submission_functions = get_functionname_step_score_allfunctions_doctypesubmission(doctype=doctype, action=action)
    ## get names of all WebSubmit functions:
    all_websubmit_functions = get_names_of_all_functions()
    ## put names into a list of single-element tuples, so that template can make HTML select list with them:
    all_websubmit_functions = map(lambda x: (str(x),), all_websubmit_functions)
    ## create page body:
    body = websubmitadmin_templates.tmpl_configuredoctype_add_submissionfunction(doctype=doctype,
                                                                                 action=action,
                                                                                 cursubmissionfunctions=submission_functions,
                                                                                 allWSfunctions=all_websubmit_functions,
                                                                                 addfunctionname=addfunctionname,
                                                                                 addfunctionstep=addfunctionstep,
                                                                                 addfunctionscore=addfunctionscore,
                                                                                 user_msg=user_msg)
    return (title, body)

def _create_configure_doctype_submission_functions_list_parameters_form(doctype,
                                                                        action,
                                                                        functionname,
                                                                        user_msg=""):
    title = """Parameters of the %s function, as used in the %s document type"""\
            % (functionname, doctype)
    funcparams = get_function_parameters(function=functionname)
    if len(funcparams) > 0:
        ## get the values
        paramslist = map(lambda x: str(x[0]), funcparams)
        params = get_function_parameter_vals_doctype(doctype=doctype, paramlist=paramslist)
    else:
        params = ()
#    params = get_parameters_name_and_value_for_function_of_doctype(doctype=doctype, function=functionname)
    body = websubmitadmin_templates.tmpl_configuredoctype_list_functionparameters(doctype=doctype,
                                                                                  action=action,
                                                                                  function=functionname,
                                                                                  params=params,
                                                                                  user_msg=user_msg)
    return (title, body)

def _update_submission_function_parameter_file(doctype, action, functionname,
                                               paramname, paramfilecontent):
    user_msg = []
    ## get the filename:
    paramval_res = get_value_of_parameter_for_doctype(doctype=doctype, parameter=paramname)
    if paramval_res is None:
        ## this parameter doesn't exist for this doctype!
        user_msg.append("The parameter [%s] doesn't exist for the document type [%s]!" % (paramname, doctype))
        (title, body) = _create_configure_doctype_submission_functions_list_parameters_form(doctype=doctype,
                                                                                            action=action,
                                                                                            functionname=functionname,
                                                                                            user_msg=user_msg)
        return (title, body)
    paramval = str(paramval_res)
    filename = basename(paramval)
    if filename == "":
        ## invalid filename
        user_msg.append("[%s] is an invalid filename - cannot save details" % (paramval,))
        (title, body) = _create_configure_doctype_submission_functions_list_parameters_form(doctype=doctype,
                                                                                            action=action,
                                                                                            functionname=functionname,
                                                                                            user_msg=user_msg)
        return (title, body)

    ## save file:
    try:
        save_update_to_file(filepath="%s/%s" % (CFG_WEBSUBMIT_BIBCONVERTCONFIGDIR, filename), filecontent=paramfilecontent)
    except InvenioWebSubmitAdminWarningIOError as e:
        ## could not correctly update the file!
        user_msg.append(str(e))
        (title, body) = _create_configure_doctype_submission_functions_list_parameters_form(doctype=doctype,
                                                                                            action=action,
                                                                                            functionname=functionname,
                                                                                            user_msg=user_msg)
        return (title, body)

    ## redisplay form
    user_msg.append("""[%s] file updated""" % (filename,))
    (title, body) = _create_configure_doctype_submission_functions_edit_parameter_file_form(doctype=doctype,
                                                                                            action=action,
                                                                                            functionname=functionname,
                                                                                            paramname=paramname,
                                                                                            user_msg=user_msg)
    return (title, body)

def _create_configure_doctype_submission_functions_edit_parameter_file_form(doctype,
                                                                            action,
                                                                            functionname,
                                                                            paramname,
                                                                            user_msg=""):
    if type(user_msg) is not list:
        user_msg = []

    paramval_res = get_value_of_parameter_for_doctype(doctype=doctype, parameter=paramname)
    if paramval_res is None:
        ## this parameter doesn't exist for this doctype!
        user_msg.append("The parameter [%s] doesn't exist for the document type [%s]!" % (paramname, doctype))
        (title, body) = _create_configure_doctype_submission_functions_list_parameters_form(doctype=doctype,
                                                                                            action=action,
                                                                                            functionname=functionname)
        return (title, body)
    paramval = str(paramval_res)
    title = "Edit the [%s] file for the [%s] document type" % (paramval, doctype)
    ## get basename of file:
    filecontent = ""
    filename = basename(paramval)
    if filename == "":
        ## invalid filename
        user_msg.append("[%s] is an invalid filename" % (paramval,))
        (title, body) = _create_configure_doctype_submission_functions_list_parameters_form(doctype=doctype,
                                                                                            action=action,
                                                                                            functionname=functionname,
                                                                                            user_msg=user_msg)
        return (title, body)
    ## try to read file contents:
    if access("%s/%s" % (CFG_WEBSUBMIT_BIBCONVERTCONFIGDIR, filename), F_OK):
        ## file exists
        if access("%s/%s" % (CFG_WEBSUBMIT_BIBCONVERTCONFIGDIR, filename), R_OK) and \
               isfile("%s/%s" % (CFG_WEBSUBMIT_BIBCONVERTCONFIGDIR, filename)):
            ## file is a regular file and is readable - get contents
            filecontent = open("%s/%s" % (CFG_WEBSUBMIT_BIBCONVERTCONFIGDIR, filename), "r").read()
        else:
            if not isfile("%s/%s" % (CFG_WEBSUBMIT_BIBCONVERTCONFIGDIR, filename)):
                ## file is not a regular file
                user_msg.append("The parameter file [%s] is not  regular file - unable to read" % (filename,))
            else:
                ## file is not readable - error message
                user_msg.append("The parameter file [%s] could not be read - check permissions" % (filename,))

            ## display page listing the parameters of this function:
            (title, body) = _create_configure_doctype_submission_functions_list_parameters_form(doctype=doctype,
                                                                                                action=action,
                                                                                                functionname=functionname,
                                                                                                user_msg=user_msg)
            return (title, body)
    else:
        ## file does not exist:
        user_msg.append("The parameter file [%s] does not exist - it will be created" % (filename,))

    ## make page body:
    body = websubmitadmin_templates.tmpl_configuredoctype_edit_functionparameter_file(doctype=doctype,
                                                                                      action=action,
                                                                                      function=functionname,
                                                                                      paramname=paramname,
                                                                                      paramfilename=filename,
                                                                                      paramfilecontent=filecontent,
                                                                                      user_msg=user_msg)
    return (title, body)

def _create_configure_doctype_submission_functions_edit_parameter_value_form(doctype,
                                                                             action,
                                                                             functionname,
                                                                             paramname,
                                                                             paramval="",
                                                                             user_msg=""):
    title = """Edit the value of the [%s] Parameter""" % (paramname,)
    ## get the parameter's value from the DB:
    paramval_res = get_value_of_parameter_for_doctype(doctype=doctype, parameter=paramname)
    if paramval_res is None:
        ## this parameter doesn't exist for this doctype!
        (title, body) = _create_configure_doctype_submission_functions_list_parameters_form(doctype=doctype,
                                                                                            action=action,
                                                                                            functionname=functionname)
    if paramval == "":
        ## use whatever retrieved paramval_res contains:
        paramval = str(paramval_res)

    body = websubmitadmin_templates.tmpl_configuredoctype_edit_functionparameter_value(doctype=doctype,
                                                                                           action=action,
                                                                                           function=functionname,
                                                                                           paramname=paramname,
                                                                                           paramval=paramval)
    return (title, body)

def _update_submissionfunction_parameter_value(doctype, action, functionname, paramname, paramval):
    user_msg = []
    try:
        update_value_of_function_parameter_for_doctype(doctype=doctype, paramname=paramname, paramval=paramval)
        user_msg.append("""The value of the parameter [%s] was updated for document type [%s]""" % (paramname, doctype))
    except InvenioWebSubmitAdminWarningTooManyRows as e:
        ## multiple rows found for param - update not carried out
        user_msg.append(str(e))
    except InvenioWebSubmitAdminWarningNoRowsFound as e:
        ## no rows found - parameter does not exist for doctype, therefore no update
        user_msg.append(str(e))
    (title, body) = \
      _create_configure_doctype_submission_functions_list_parameters_form(doctype=doctype, action=action,
                                                                          functionname=functionname, user_msg=user_msg)
    return (title, body)

def perform_request_configure_doctype_submissionfunctions_parameters(doctype,
                                                                     action,
                                                                     functionname,
                                                                     functionstep,
                                                                     functionscore,
                                                                     paramname="",
                                                                     paramval="",
                                                                     editfunctionparametervalue="",
                                                                     editfunctionparametervaluecommit="",
                                                                     editfunctionparameterfile="",
                                                                     editfunctionparameterfilecommit="",
                                                                     paramfilename="",
                                                                     paramfilecontent=""):

    body = ""
    user_msg = []
    ## ensure that there is only one doctype for this doctype ID - simply display all doctypes with warning if not
    if doctype in ("", None):
        user_msg.append("""Unknown Document Type""")
        ## TODO : LOG ERROR
        all_doctypes = get_docid_docname_alldoctypes()
        body = websubmitadmin_templates.tmpl_display_alldoctypes(doctypes=all_doctypes, user_msg=user_msg)
        title = "Available WebSubmit Document Types"
        return (title, body)

    numrows_doctype = get_number_doctypes_docid(docid=doctype)
    if numrows_doctype > 1:
        ## there are multiple doctypes with this doctype ID:
        ## TODO : LOG ERROR
        user_msg.append("""Multiple document types identified by "%s" exist - cannot configure at this time.""" \
                   % (doctype,))
        all_doctypes = get_docid_docname_alldoctypes()
        body = websubmitadmin_templates.tmpl_display_alldoctypes(doctypes=all_doctypes, user_msg=user_msg)
        title = "Available WebSubmit Document Types"
        return (title, body)
    elif numrows_doctype == 0:
        ## this doctype does not seem to exist:
        user_msg.append("""The document type identified by "%s" doesn't exist - cannot configure at this time.""" \
                   % (doctype,))
        ## TODO : LOG ERROR
        all_doctypes = get_docid_docname_alldoctypes()
        body = websubmitadmin_templates.tmpl_display_alldoctypes(doctypes=all_doctypes, user_msg=user_msg)
        title = "Available WebSubmit Document Types"
        return (title, body)

    ## ensure that this submission exists for this doctype:
    numrows_submission = get_number_submissions_doctype_action(doctype=doctype, action=action)
    if numrows_submission > 1:
        ## there are multiple submissions for this doctype/action ID:
        ## TODO : LOG ERROR
        user_msg.append("""The Submission "%s" seems to exist multiple times for the Document Type "%s" - cannot configure at this time.""" \
                   % (action, doctype))
        (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
        return (title, body)
    elif numrows_submission == 0:
        ## this submission does not seem to exist for this doctype:
        user_msg.append("""The Submission "%s" doesn't exist for the "%s" Document Type - cannot configure at this time.""" \
                   % (action, doctype))
        ## TODO : LOG ERROR
        (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
        return (title, body)

    if editfunctionparametervaluecommit not in ("", None):
        ## commit an update to a function parameter:
        (title, body) = _update_submissionfunction_parameter_value(doctype=doctype, action=action, functionname=functionname,
                                                                   paramname=paramname, paramval=paramval)
    elif editfunctionparametervalue not in ("", None):
        ## display a form for editing the value of a parameter:
        (title, body) = _create_configure_doctype_submission_functions_edit_parameter_value_form(doctype=doctype,
                                                                                                 action=action,
                                                                                                 functionname=functionname,
                                                                                                 paramname=paramname,
                                                                                                 paramval=paramval)
    elif editfunctionparameterfile not in ("", None):
        ## display a form for editing the contents of a file, named by the parameter's value:
        (title, body) = _create_configure_doctype_submission_functions_edit_parameter_file_form(doctype=doctype,
                                                                                                action=action,
                                                                                                functionname=functionname,
                                                                                                paramname=paramname)
    elif editfunctionparameterfilecommit not in ("", None):
        (title, body) = _update_submission_function_parameter_file(doctype=doctype, action=action, functionname=functionname,
                                                                    paramname=paramname, paramfilecontent=paramfilecontent)
    else:
        ## default - display list of parameters for function:
        (title, body) = _create_configure_doctype_submission_functions_list_parameters_form(doctype=doctype,
                                                                                            action=action,
                                                                                            functionname=functionname)
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
                                                          deletefunctionscore="",
                                                          configuresubmissionaddfunction="",
                                                          configuresubmissionaddfunctioncommit="",
                                                          addfunctionname="",
                                                          addfunctionstep="",
                                                          addfunctionscore=""):

    body = ""
    user_msg = []

    if addfunctionstep != "":
        try:
            addfunctionstep = str(wash_single_urlarg(urlarg=addfunctionstep, argreqdtype=int, argdefault=""))
        except ValueError as e:
            addfunctionstep = ""
    if addfunctionscore != "":
        try:
            addfunctionscore = str(wash_single_urlarg(urlarg=addfunctionscore, argreqdtype=int, argdefault=""))
        except ValueError as e:
            addfunctionscore = ""
    if deletefunctionstep != "":
        try:
            deletefunctionstep = str(wash_single_urlarg(urlarg=deletefunctionstep, argreqdtype=int, argdefault=""))
        except ValueError as e:
            deletefunctionstep = ""
    if deletefunctionscore != "":
        try:
            deletefunctionscore = str(wash_single_urlarg(urlarg=deletefunctionscore, argreqdtype=int, argdefault=""))
        except ValueError as e:
            deletefunctionscore = ""
    if movetofunctionstep != "":
        try:
            movetofunctionstep = str(wash_single_urlarg(urlarg=movetofunctionstep, argreqdtype=int, argdefault=""))
        except ValueError as e:
            movetofunctionstep = ""
    if movetofunctionscore != "":
        try:
            movetofunctionscore = str(wash_single_urlarg(urlarg=movetofunctionscore, argreqdtype=int, argdefault=""))
        except ValueError as e:
            movetofunctionscore = ""
    if moveupfunctionstep != "":
        try:
            moveupfunctionstep = str(wash_single_urlarg(urlarg=moveupfunctionstep, argreqdtype=int, argdefault=""))
        except ValueError as e:
            moveupfunctionstep = ""
    if moveupfunctionscore != "":
        try:
            moveupfunctionscore = str(wash_single_urlarg(urlarg=moveupfunctionscore, argreqdtype=int, argdefault=""))
        except ValueError as e:
            moveupfunctionscore = ""
    if movedownfunctionstep != "":
        try:
            movedownfunctionstep = str(wash_single_urlarg(urlarg=movedownfunctionstep, argreqdtype=int, argdefault=""))
        except ValueError as e:
            movedownfunctionstep = ""
    if movedownfunctionscore != "":
        try:
            movedownfunctionscore = str(wash_single_urlarg(urlarg=movedownfunctionscore, argreqdtype=int, argdefault=""))
        except ValueError as e:
            movedownfunctionscore = ""


    ## ensure that there is only one doctype for this doctype ID - simply display all doctypes with warning if not
    if doctype in ("", None):
        user_msg.append("""Unknown Document Type""")
        ## TODO : LOG ERROR
        all_doctypes = get_docid_docname_alldoctypes()
        body = websubmitadmin_templates.tmpl_display_alldoctypes(doctypes=all_doctypes, user_msg=user_msg)
        title = "Available WebSubmit Document Types"
        return (title, body)

    numrows_doctype = get_number_doctypes_docid(docid=doctype)
    if numrows_doctype > 1:
        ## there are multiple doctypes with this doctype ID:
        ## TODO : LOG ERROR
        user_msg.append("""Multiple document types identified by "%s" exist - cannot configure at this time.""" \
                   % (doctype,))
        all_doctypes = get_docid_docname_alldoctypes()
        body = websubmitadmin_templates.tmpl_display_alldoctypes(doctypes=all_doctypes, user_msg=user_msg)
        title = "Available WebSubmit Document Types"
        return (title, body)
    elif numrows_doctype == 0:
        ## this doctype does not seem to exist:
        user_msg.append("""The document type identified by "%s" doesn't exist - cannot configure at this time.""" \
                   % (doctype,))
        ## TODO : LOG ERROR
        all_doctypes = get_docid_docname_alldoctypes()
        body = websubmitadmin_templates.tmpl_display_alldoctypes(doctypes=all_doctypes, user_msg=user_msg)
        title = "Available WebSubmit Document Types"
        return (title, body)

    ## ensure that this submission exists for this doctype:
    numrows_submission = get_number_submissions_doctype_action(doctype=doctype, action=action)
    if numrows_submission > 1:
        ## there are multiple submissions for this doctype/action ID:
        ## TODO : LOG ERROR
        user_msg.append("""The Submission "%s" seems to exist multiple times for the Document Type "%s" - cannot configure at this time.""" \
                   % (action, doctype))
        (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
        return (title, body)
    elif numrows_submission == 0:
        ## this submission does not seem to exist for this doctype:
        user_msg.append("""The Submission "%s" doesn't exist for the "%s" Document Type - cannot configure at this time.""" \
                   % (action, doctype))
        ## TODO : LOG ERROR
        (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
        return (title, body)


    ## submission valid
    if movefromfunctionname != "" and movefromfunctionstep != "" and movefromfunctionscore != "" and \
       movetofunctionname != "" and movetofunctionstep != "" and movetofunctionscore != "":
        ## process moving the function by jumping it to another position
        try:
            move_submission_function_from_one_position_to_another_position(doctype=doctype, action=action,
                                                                           movefuncname=movefromfunctionname,
                                                                           movefuncfromstep=movefromfunctionstep,
                                                                           movefuncfromscore=movefromfunctionscore,
                                                                           movefunctostep=movetofunctionstep,
                                                                           movefunctoscore=movetofunctionscore)
            user_msg.append("""The function [%s] at step [%s], score [%s] was successfully moved."""\
                            % (movefromfunctionname, movefromfunctionstep, movefromfunctionscore))
        except Exception as e:
            ## there was a problem
            user_msg.append(str(e))
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
        (title, body) = _delete_submission_function(doctype=doctype, action=action, deletefunctionname=deletefunctionname,
                                                    deletefunctionstep=deletefunctionstep, deletefunctionscore=deletefunctionscore)
    elif configuresubmissionaddfunction != "":
        ## display a form that allows the addition of a new WebSubmit function
        (title, body) = _create_configure_doctype_submission_functions_add_function_form(doctype=doctype,
                                                                                         action=action)
    elif configuresubmissionaddfunctioncommit != "":
        ## process the addition of the new WebSubmit function to the submission:
        (title, body) = _add_function_to_submission(doctype=doctype, action=action, addfunctionname=addfunctionname,
                                                    addfunctionstep=addfunctionstep, addfunctionscore=addfunctionscore)
    else:
        ## default - display functions for this submission
        (title, body) = _create_configure_doctype_submission_functions_form(doctype=doctype,
                                                                            action=action,
                                                                            movefromfunctionname=movefromfunctionname,
                                                                            movefromfunctionstep=movefromfunctionstep,
                                                                            movefromfunctionscore=movefromfunctionscore
                                                                           )
    return (title, body)

def _add_function_to_submission(doctype, action, addfunctionname, addfunctionstep, addfunctionscore):
    """Process the addition of a function to a submission.
       The user can decide in which step and at which score to insert the function.
       @param doctype: (string) the unique ID of a document type
       @param action: (string) the unique ID of an action
       @param addfunctionname: (string) the name of the function to be added to the submission
       @param addfunctionstep: (integer) the step at which the function is to be added
       @param addfunctionscore: (integer) the score at which the function is to be added
       @return: a tuple containing 2 strings: (page-title, page-body)
    """
    user_msg = []
    if addfunctionname == "" or  addfunctionstep == "" or addfunctionscore == "":
        ## invalid details!
        user_msg.append("""Invalid function coordinates supplied!""")
        (title, body) = _create_configure_doctype_submission_functions_add_function_form(doctype=doctype,
                                                                                         action=action,
                                                                                         user_msg=user_msg)
        return (title, body)
    try:
        if int(addfunctionstep) < 1 or int(addfunctionscore) < 1:
            ## invalid details!
            user_msg.append("""Invalid function step and/or score!""")
            (title, body) = _create_configure_doctype_submission_functions_add_function_form(doctype=doctype,
                                                                                             action=action,
                                                                                             user_msg=user_msg)
            return (title, body)
    except ValueError:
        user_msg.append("""Invalid function step and/or score!""")
        (title, body) = _create_configure_doctype_submission_functions_add_function_form(doctype=doctype,
                                                                                         action=action,
                                                                                         user_msg=user_msg)

    try:
        insert_function_into_submission_at_step_and_score_then_regulate_scores_of_functions_in_step(doctype=doctype,
                                                                                                    action=action,
                                                                                                    function=addfunctionname,
                                                                                                    step=addfunctionstep,
                                                                                                    score=addfunctionscore)
    except InvenioWebSubmitAdminWarningReferentialIntegrityViolation as e:
        ## Function didn't exist in WebSubmit! Not added to submission.
        user_msg.append(str(e))
        ## TODO : LOG ERROR
        (title, body) = _create_configure_doctype_submission_functions_add_function_form(doctype=doctype,
                                                                                         action=action,
                                                                                         addfunctionstep=addfunctionstep,
                                                                                         addfunctionscore=addfunctionscore,
                                                                                         user_msg=user_msg)
        return (title, body)
    except InvenioWebSubmitAdminWarningInsertFailed as e:
        ## insert failed - some functions within the step may have been corrupted!
        user_msg.append(str(e))
        ## TODO : LOG ERROR
        (title, body) = \
                _create_configure_doctype_submission_functions_form(doctype=doctype, action=action, user_msg=user_msg)
        return (title, body)
    except InvenioWebSubmitAdminWarningDeleteFailed as e:
        ## when regulating the scores of functions within the step, could not delete some or all of the functions
        ## within the step that the function was added to. Some functions may have been lost!
        user_msg.append(str(e))
        ## TODO : LOG ERROR
        (title, body) = \
                _create_configure_doctype_submission_functions_form(doctype=doctype, action=action, user_msg=user_msg)
        return (title, body)

    ## Successfully added
    user_msg.append("""The function [%s] has been added to submission [%s] at step [%s], score [%s]."""\
                    % (addfunctionname, "%s%s" % (action, doctype), addfunctionstep, addfunctionscore))
    (title, body) = \
            _create_configure_doctype_submission_functions_form(doctype=doctype, action=action, user_msg=user_msg)
    return (title, body)

def _delete_submission_function(doctype, action, deletefunctionname, deletefunctionstep, deletefunctionscore):
    """Delete a submission function from a given submission. Re-order all functions below it (within the same step)
       to fill the gap left by the deleted function.
       @param doctype: (string) the unique ID of a document type
       @param action: (string) the unique ID of an action
       @param deletefunctionname: (string) the name of the function to be deleted from the submission
       @param deletefunctionstep: (string) the step of the function to be deleted from the submission
       @param deletefunctionscore: (string) the score of the function to be deleted from the submission
       @return: tuple containing 2 strings: (page-title, page-body)
    """
    user_msg = []
    ## first, delete the function:
    try:
        delete_function_at_step_and_score_from_submission(doctype=doctype, action=action,
                                                          function=deletefunctionname, step=deletefunctionstep,
                                                          score=deletefunctionscore)
    except InvenioWebSubmitAdminWarningDeleteFailed as e:
        ## unable to delete function - error message and return
        user_msg.append("""Unable to delete function [%s] at step [%s], score [%s] from submission [%s]""" \
                        % (deletefunctionname, deletefunctionstep, deletefunctionscore, "%s%s" % (action, doctype)))
        ## TODO : LOG ERROR
        (title, body) = _create_configure_doctype_submission_functions_form(doctype=doctype, action=action, user_msg=user_msg)
        return (title, body)
    ## now, correct the scores of all functions in the step from which a function was just deleted:
    try:
        regulate_score_of_all_functions_in_step_to_ascending_multiples_of_10_for_submission(doctype=doctype,
                                                                                            action=action,
                                                                                            step=deletefunctionstep)
    except InvenioWebSubmitAdminWarningDeleteFailed as e:
        ## couldnt delete the functions before reordering them
        user_msg.append("""Deleted function [%s] at step [%s], score [%s] from submission [%s], but could not re-order""" \
                        """ scores of remaining functions within step [%s]""" \
                        % (deletefunctionname, deletefunctionstep, deletefunctionscore,
                           "%s%s" % (action, doctype), deletefunctionstep))
        ## TODO : LOG ERROR
        (title, body) = _create_configure_doctype_submission_functions_form(doctype=doctype, action=action, user_msg=user_msg)
        return (title, body)
    ## update submission "last-modification" date:
    update_modification_date_for_submission(doctype=doctype, action=action)
    ## success message:
    user_msg.append("""Successfully deleted function [%s] at step [%s], score [%s] from submission [%s]""" \
                    % (deletefunctionname, deletefunctionstep, deletefunctionscore, "%s%s" % (action, doctype)))
    ## TODO : LOG function Deletion
    (title, body) = _create_configure_doctype_submission_functions_form(doctype=doctype, action=action, user_msg=user_msg)
    return (title, body)

def perform_request_configure_doctype_submissionpage_preview(doctype, action, pagenum):
    """Display a preview of a Submission Page and its fields.
       @param doctype: (string) the unique ID of a document type
       @param action: (string) the unique ID of an action
       @param pagenum: (integer) the number of the submission page to be previewed
       @return: a tuple of four elements. (page-title, page-body)
    """
    body = ""
    user_msg = []

    try:
        pagenum = str(pagenum)
    except ValueError:
        pagenum = ""

    if pagenum != "":
        try:
            pagenum = str(wash_single_urlarg(urlarg=pagenum, argreqdtype=int, argdefault=""))
        except ValueError as e:
            pagenum = ""
    ## ensure that the page number for this submission is valid:
    num_pages_submission = get_numbersubmissionpages_doctype_action(doctype=doctype, action=action)
    try:
        if not (int(pagenum) > 0 and int(pagenum) <= num_pages_submission):
            user_msg.append("Invalid page number - out of range")
            (title, body) = _create_configure_doctype_submission_pages_form(doctype=doctype, action=action, user_msg=user_msg)
            return (title, body)
    except ValueError:
        ## invalid page number
        user_msg.append("Invalid page number - must be an integer value!")
        (title, body) = _create_configure_doctype_submission_pages_form(doctype=doctype, action=action, user_msg=user_msg)
        return (title, body)

    ## get details of all fields on submission page:
    fields = get_details_and_description_of_all_fields_on_submissionpage(doctype=doctype, action=action, pagenum=pagenum)
    ## ensure all values for each field are strings:
    string_fields = []
    for field in fields:
        string_fields.append(stringify_list_elements(field))
    title = """A preview of Page %s of the %s Submission""" % (pagenum, "%s%s" % (action, doctype))
    body = websubmitadmin_templates.tmpl_configuredoctype_display_submissionpage_preview(doctype=doctype,
                                                                                         action=action,
                                                                                         pagenum=pagenum,
                                                                                         fields=string_fields)
    return (title, body)

def perform_request_configure_doctype_submissionpage_elements(doctype, action, pagenum, movefieldfromposn="",
                                                              movefieldtoposn="", deletefieldposn="", editfieldposn="",
                                                              editfieldposncommit="", fieldname="", fieldtext="", fieldlevel="",
                                                              fieldshortdesc="", fieldcheck="", addfield="", addfieldcommit=""):
    """Process requests relating to the elements of a particular submission page"""

    body = ""
    user_msg = []
    try:
        pagenum = str(pagenum)
    except ValueError:
        pagenum = ""

    if pagenum != "":
        try:
            pagenum = str(wash_single_urlarg(urlarg=pagenum, argreqdtype=int, argdefault=""))
        except ValueError as e:
            pagenum = ""
    if fieldname != "":
        try:
            fieldname = wash_single_urlarg(urlarg=fieldname, argreqdtype=str, argdefault="", maxstrlen=15, minstrlen=1)
            if string_is_alphanumeric_including_underscore(txtstring=fieldname) == 0:
                fieldname = ""
        except ValueError as e:
            fieldname = ""
    if fieldtext != "":
        try:
            fieldtext = wash_single_urlarg(urlarg=fieldtext, argreqdtype=str, argdefault="")
        except ValueError as e:
            fieldtext = ""
    if fieldlevel != "":
        try:
            fieldlevel = wash_single_urlarg(urlarg=fieldlevel, argreqdtype=str, argdefault="O", maxstrlen=1, minstrlen=1)
            if string_is_alphanumeric_including_underscore(txtstring=fieldlevel) == 0:
                fieldlevel = "O"
            if fieldlevel not in ("m", "M", "o", "O"):
                fieldlevel = "O"
            fieldlevel = fieldlevel.upper()
        except ValueError as e:
            fieldlevel = "O"
    if fieldshortdesc != "":
        try:
            fieldshortdesc = wash_single_urlarg(urlarg=fieldshortdesc, argreqdtype=str, argdefault="")
        except ValueError as e:
            fieldshortdesc = ""
    if fieldcheck != "":
        try:
            fieldcheck = wash_single_urlarg(urlarg=fieldcheck, argreqdtype=str, argdefault="", maxstrlen=15, minstrlen=1)
            if string_is_alphanumeric_including_underscore(txtstring=fieldcheck) == 0:
                fieldcheck = ""
        except ValueError as e:
            fieldcheck = ""
    if editfieldposn != "":
        try:
            editfieldposn = str(wash_single_urlarg(urlarg=editfieldposn, argreqdtype=int, argdefault=""))
        except ValueError as e:
            editfieldposn = ""
    if deletefieldposn != "":
        try:
            deletefieldposn = str(wash_single_urlarg(urlarg=deletefieldposn, argreqdtype=int, argdefault=""))
        except ValueError as e:
            deletefieldposn = ""
    if movefieldfromposn != "":
        try:
            movefieldfromposn = str(wash_single_urlarg(urlarg=movefieldfromposn, argreqdtype=int, argdefault=""))
        except ValueError as e:
            movefieldfromposn = ""
    if movefieldtoposn != "":
        try:
            movefieldtoposn = str(wash_single_urlarg(urlarg=movefieldtoposn, argreqdtype=int, argdefault=""))
        except ValueError as e:
            movefieldtoposn = ""

    ## ensure that there is only one doctype for this doctype ID - simply display all doctypes with warning if not
    if doctype in ("", None):
        user_msg.append("""Unknown Document Type""")
        ## TODO : LOG ERROR
        all_doctypes = get_docid_docname_alldoctypes()
        body = websubmitadmin_templates.tmpl_display_alldoctypes(doctypes=all_doctypes, user_msg=user_msg)
        title = "Available WebSubmit Document Types"
        return (title, body)

    numrows_doctype = get_number_doctypes_docid(docid=doctype)
    if numrows_doctype > 1:
        ## there are multiple doctypes with this doctype ID:
        ## TODO : LOG ERROR
        user_msg.append("""Multiple document types identified by "%s" exist - cannot configure at this time.""" \
                   % (doctype,))
        all_doctypes = get_docid_docname_alldoctypes()
        body = websubmitadmin_templates.tmpl_display_alldoctypes(doctypes=all_doctypes, user_msg=user_msg)
        title = "Available WebSubmit Document Types"
        return (title, body)
    elif numrows_doctype == 0:
        ## this doctype does not seem to exist:
        user_msg.append("""The document type identified by "%s" doesn't exist - cannot configure at this time.""" \
                   % (doctype,))
        ## TODO : LOG ERROR
        all_doctypes = get_docid_docname_alldoctypes()
        body = websubmitadmin_templates.tmpl_display_alldoctypes(doctypes=all_doctypes, user_msg=user_msg)
        title = "Available WebSubmit Document Types"
        return (title, body)

    ## ensure that this submission exists for this doctype:
    numrows_submission = get_number_submissions_doctype_action(doctype=doctype, action=action)
    if numrows_submission > 1:
        ## there are multiple submissions for this doctype/action ID:
        ## TODO : LOG ERROR
        user_msg.append("""The Submission "%s" seems to exist multiple times for the Document Type "%s" - cannot configure at this time.""" \
                   % (action, doctype))
        (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
        return (title, body)
    elif numrows_submission == 0:
        ## this submission does not seem to exist for this doctype:
        user_msg.append("""The Submission "%s" doesn't exist for the "%s" Document Type - cannot configure at this time.""" \
                   % (action, doctype))
        ## TODO : LOG ERROR
        (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
        return (title, body)

    ## ensure that the page number for this submission is valid:
    num_pages_submission = get_numbersubmissionpages_doctype_action(doctype=doctype, action=action)
    try:
        if not (int(pagenum) > 0 and int(pagenum) <= num_pages_submission):
            user_msg.append("Invalid page number - out of range")
            (title, body) = _create_configure_doctype_submission_pages_form(doctype=doctype, action=action, user_msg=user_msg)
            return (title, body)
    except ValueError:
        ## invalid page number
        user_msg.append("Invalid page number - must be an integer value!")
        (title, body) = _create_configure_doctype_submission_pages_form(doctype=doctype, action=action, user_msg=user_msg)
        return (title, body)


    ## submission valid
    if editfieldposn != "" and editfieldposncommit == "":
        ## display form for editing field
        (title, body) = _configure_doctype_edit_field_on_submissionpage_display_field_details(doctype=doctype, action=action,
                                                                                              pagenum=pagenum, fieldposn=editfieldposn)
    elif editfieldposn != "" and editfieldposncommit != "":
        ## commit changes to element
        (title, body) = _configure_doctype_edit_field_on_submissionpage(doctype=doctype, action=action,
                                                                        pagenum=pagenum, fieldposn=editfieldposn, fieldtext=fieldtext,
                                                                        fieldlevel=fieldlevel, fieldshortdesc=fieldshortdesc, fieldcheck=fieldcheck)
    elif movefieldfromposn != "" and movefieldtoposn != "":
        ## move a field
        (title, body) = _configure_doctype_move_field_on_submissionpage(doctype=doctype,
                                                                        action=action, pagenum=pagenum, movefieldfromposn=movefieldfromposn,
                                                                        movefieldtoposn=movefieldtoposn)
    elif addfield != "":
        ## request to add a new field to a page - display form
        (title, body) = _configure_doctype_add_field_to_submissionpage_display_form(doctype=doctype, action=action, pagenum=pagenum)
    elif addfieldcommit != "":
        ## commit a new field to the page
        (title, body) = _configure_doctype_add_field_to_submissionpage(doctype=doctype, action=action,
                                                                       pagenum=pagenum, fieldname=fieldname, fieldtext=fieldtext,
                                                                       fieldlevel=fieldlevel, fieldshortdesc=fieldshortdesc, fieldcheck=fieldcheck)
    elif deletefieldposn != "":
        ## user wishes to delete a field from the page:
        (title, body) = _configure_doctype_delete_field_from_submissionpage(doctype=doctype,
                                                                            action=action, pagenum=pagenum, fieldnum=deletefieldposn)
    else:
        ## default visit to page - list its elements:
        (title, body) = _create_configure_doctype_submission_page_elements_form(doctype=doctype, action=action,
                                                                                pagenum=pagenum, movefieldfromposn=movefieldfromposn)
    return (title, body)

def stringify_list_elements(elementslist):
    o = []
    for el in elementslist:
        o.append(str(el))
    return o

def _configure_doctype_edit_field_on_submissionpage(doctype, action, pagenum, fieldposn,
                                                    fieldtext, fieldlevel, fieldshortdesc, fieldcheck):
    """Perform an update to the details of a field on a submission page.
       @param doctype: (string) the unique ID of a document type
       @param action: (string) the unique ID of an action
       @param pagenum: (integer) the number of the page on which the element to be updated is found
       @param fieldposn: (integer) the numeric position of the field to be editied
       @param fieldtext: (string) the text label displayed with a field
       @param fieldlevel: (char) M or O (whether the field is mandatory or optional)
       @param fieldshortdesc: (string) the short description of a field
       @param fieldcheck: (string) the name of a JavaScript check to be applied to a field
       @return: a tuple containing 2 strings - (page-title, page-body)
    """
    user_msg = []
    if fieldcheck not in ("", None):
        ## ensure check exists:
        checkres = get_number_jschecks_with_chname(chname=fieldcheck)
        if checkres < 1:
            user_msg.append("The Check '%s' does not exist in WebSubmit - changes to field not saved" % (fieldcheck,))
            (title, body) = _configure_doctype_edit_field_on_submissionpage_display_field_details(doctype=doctype, action=action,
                                                                                                  pagenum=pagenum, fieldposn=fieldposn,
                                                                                                  fieldtext=fieldtext, fieldlevel=fieldlevel,
                                                                                                  fieldshortdesc=fieldshortdesc, user_msg=user_msg)
            return (title, body)

    try:
        update_details_of_a_field_on_a_submissionpage(doctype=doctype, action=action, pagenum=pagenum, fieldposn=fieldposn,
                                                      fieldtext=fieldtext, fieldlevel=fieldlevel, fieldshortdesc=fieldshortdesc,
                                                      fieldcheck=fieldcheck)
        user_msg.append("The details of the field at position %s have been updated successfully" % (fieldposn,))
        update_modification_date_for_submission(doctype=doctype, action=action)
    except InvenioWebSubmitAdminWarningTooManyRows as e:
        ## multiple rows found at page position - not safe to edit:
        user_msg.append("Unable to update details of field at position %s on submission page %s - multiple fields found at this position" \
                        % (fieldposn, pagenum))
        ## TODO : LOG WARNING
    except InvenioWebSubmitAdminWarningNoRowsFound as e:
        ## field not found - cannot edit
        user_msg.append("Unable to update details of field at position %s on submission page %s - field doesn't seem to exist there!" \
                        % (fieldposn, pagenum))
        ## TODO : LOG WARNING

    (title, body) = _create_configure_doctype_submission_page_elements_form(doctype=doctype, action=action, pagenum=pagenum, user_msg=user_msg)
    return (title, body)

def _configure_doctype_edit_field_on_submissionpage_display_field_details(doctype, action, pagenum, fieldposn,
                                                                          fieldtext=None, fieldlevel=None, fieldshortdesc=None,
                                                                          fieldcheck=None, user_msg=""):
    """Display a form used to edit a field on a submission page.
       @param doctype: (string) the unique ID of a document type
       @param action: (string) the unique ID of an action
       @param pagenum: (integer) the number of the page on which the element to be updated is found
       @param fieldposn: (integer) the numeric position of the field to be editied
       @param fieldtext: (string) the text label displayed with a field
       @param fieldlevel: (char) M or O (whether the field is mandatory or optional)
       @param fieldshortdesc: (string) the short description of a field
       @param fieldcheck: (string) the name of a JavaScript check to be applied to a field
       @param user_msg: (list of strings, or string) any warning/error message to be displayed to the user
       @return: a tuple containing 2 strings (page-title, page-body)
    """
    if type(user_msg) not in (list, tuple) or user_msg == "":
        user_msg = []
    ## get a list of all check names:
    checks_res = get_all_jscheck_names()
    allchecks=[]
    for check in checks_res:
        allchecks.append((check,))
    ## get the details for the field to be edited:
    fielddets = get_details_of_field_at_positionx_on_submissionpage(doctype=doctype, action=action, pagenum=pagenum, fieldposition=fieldposn)

    if len(fielddets) < 1:
        (title, body) = _create_configure_doctype_submission_page_elements_form(doctype=doctype, action=action, pagenum=pagenum)
        return (title, body)

    fieldname = str(fielddets[2])
    if fieldtext is not None:
        fieldtext = str(fieldtext)
    else:
        fieldtext = str(fielddets[3])
    if fieldlevel is not None:
        fieldlevel = str(fieldlevel)
    else:
        fieldlevel = str(fielddets[4])
    if fieldshortdesc is not None:
        fieldshortdesc = str(fieldshortdesc)
    else:
        fieldshortdesc = str(fielddets[5])
    if fieldcheck is not None:
        fieldcheck = str(fieldcheck)
    else:
        fieldcheck = str(fielddets[6])
    cd = str(fielddets[7])
    md = str(fielddets[8])
    title = """Edit the %(fieldname)s field as it appears at position %(fieldnum)s on Page %(pagenum)s of the %(submission)s Submission""" \
            % { 'fieldname' : fieldname, 'fieldnum' : fieldposn, 'pagenum' : pagenum, 'submission' : "%s%s" % (action, doctype) }

    body = websubmitadmin_templates.tmpl_configuredoctype_edit_submissionfield(doctype=doctype,
                                                                               action=action,
                                                                               pagenum=pagenum,
                                                                               fieldnum=fieldposn,
                                                                               fieldname=fieldname,
                                                                               fieldtext=fieldtext,
                                                                               fieldlevel=fieldlevel,
                                                                               fieldshortdesc=fieldshortdesc,
                                                                               fieldcheck=fieldcheck,
                                                                               cd=cd,
                                                                               md=md,
                                                                               allchecks=allchecks,
                                                                               user_msg=user_msg)
    return (title, body)

def _configure_doctype_add_field_to_submissionpage(doctype, action, pagenum, fieldname="",
                                                   fieldtext="", fieldlevel="", fieldshortdesc="", fieldcheck=""):
    """Add a field to a submission page.
       @param doctype: (string) the unique ID of a document type
       @param action: (string) the unique ID of an action
       @param pagenum: (integer) the number of the page on which the element to be updated is found
       @param fieldname: (string) the name of the field to be added to the page
       @param fieldtext: (string) the text label displayed with a field
       @param fieldlevel: (char) M or O (whether the field is mandatory or optional)
       @param fieldshortdesc: (string) the short description of a field
       @param fieldcheck: (string) the name of a JavaScript check to be applied to a field
       @return: a tuple containing 2 strings - (page-title, page-body)
    """
    user_msg = []
    ## ensure that a field "fieldname" actually exists:
    if fieldname == "":
        ## the field to be added has no element description in the WebSubmit DB - cannot add
        user_msg.append("""The field that you have chosen to add does not seem to exist in WebSubmit - cannot add""")
        (title, body) = _configure_doctype_add_field_to_submissionpage_display_form(doctype, action, pagenum,
                                                                                    fieldtext=fieldtext,
                                                                                    fieldlevel=fieldlevel, fieldshortdesc=fieldshortdesc,
                                                                                    fieldcheck=fieldcheck, user_msg=user_msg)
        return (title, body)

    numelements_elname = get_number_elements_with_elname(elname=fieldname)
    if numelements_elname < 1:
        ## the field to be added has no element description in the WebSubmit DB - cannot add
        user_msg.append("""The field that you have chosen to add (%s) does not seem to exist in WebSubmit - cannot add""" % (fieldname,))
        (title, body) = _configure_doctype_add_field_to_submissionpage_display_form(doctype, action, pagenum,
                                                                                    fieldtext=fieldtext,
                                                                                    fieldlevel=fieldlevel, fieldshortdesc=fieldshortdesc,
                                                                                    fieldcheck=fieldcheck, user_msg=user_msg)
        return (title, body)
    ## if fieldcheck has been provided, ensure that it is a valid check name:
    if fieldcheck not in ("", None):
        ## ensure check exists:
        checkres = get_number_jschecks_with_chname(chname=fieldcheck)
        if checkres < 1:
            user_msg.append("The Check '%s' does not exist in WebSubmit - new field not saved to page" % (fieldcheck,))
            (title, body) = _configure_doctype_add_field_to_submissionpage_display_form(doctype, action, pagenum,
                                                                                        fieldname=fieldname, fieldtext=fieldtext,
                                                                                        fieldlevel=fieldlevel, fieldshortdesc=fieldshortdesc,
                                                                                        user_msg=user_msg)
            return (title, body)
    ## now add the new field to the page:
    try:
        insert_field_onto_submissionpage(doctype=doctype, action=action, pagenum=pagenum, fieldname=fieldname, fieldtext=fieldtext,
                                         fieldlevel=fieldlevel, fieldshortdesc=fieldshortdesc, fieldcheck=fieldcheck)
        user_msg.append("""Successfully added the field "%s" to the last position on page %s of submission %s""" \
                        % (fieldname, pagenum, "%s%s" % (action, doctype)))
        update_modification_date_for_submission(doctype=doctype, action=action)
        (title, body) = _create_configure_doctype_submission_page_elements_form(doctype=doctype, action=action, pagenum=pagenum, user_msg=user_msg)
    except InvenioWebSubmitAdminWarningInsertFailed as e:
        ## the insert of the new field failed for some reason
        ## TODO : LOG ERROR
        user_msg.append("""Couldn't add the field "%s" to page %s of submission %s - please try again""" \
                        % (fieldname, pagenum, "%s%s" % (action, doctype)))
        (title, body) = _configure_doctype_add_field_to_submissionpage_display_form(doctype, action, pagenum,
                                                                                    fieldname=fieldname, fieldtext=fieldtext,
                                                                                    fieldlevel=fieldlevel, fieldshortdesc=fieldshortdesc,
                                                                                    fieldcheck=fieldcheck, user_msg=user_msg)
    return (title, body)

def _configure_doctype_add_field_to_submissionpage_display_form(doctype, action, pagenum, fieldname="", fieldtext="",
                                                                fieldlevel="", fieldshortdesc="", fieldcheck="", user_msg=""):
    title = """Add a Field to Page %(pagenum)s of the %(submission)s Submission""" \
            % { 'pagenum' : pagenum, 'submission' : "%s%s" % (action, doctype) }

    ## sanity checking:
    if type(user_msg) not in (list, tuple) or user_msg == "":
        user_msg = []
    ## get a list of all check names:
    checks_res = get_all_jscheck_names()
    allchecks=[]
    for check in checks_res:
        allchecks.append((check,))
    ## get a list of all WebSubmit element names:
    elements_res = get_all_element_names()
    allelements = []
    for el in elements_res:
        allelements.append((el,))

    ## get form:
    body = websubmitadmin_templates.tmpl_configuredoctype_add_submissionfield(doctype=doctype,
                                                                              action=action,
                                                                              pagenum=pagenum,
                                                                              fieldname=fieldname,
                                                                              fieldtext=fieldtext,
                                                                              fieldlevel=fieldlevel,
                                                                              fieldshortdesc=fieldshortdesc,
                                                                              fieldcheck=fieldcheck,
                                                                              allchecks=allchecks,
                                                                              allelements=allelements,
                                                                              user_msg=user_msg)
    return (title, body)

def _configure_doctype_move_field_on_submissionpage(doctype, action, pagenum, movefieldfromposn, movefieldtoposn):
    user_msg = []
    _ = gettext_set_language(CFG_SITE_LANG)
    movefield_res = move_field_on_submissionpage_from_positionx_to_positiony(doctype=doctype, action=action, pagenum=pagenum,
                                                                             movefieldfrom=movefieldfromposn, movefieldto=movefieldtoposn)

    if movefield_res == 1:
        ## invalid field numbers
        try:
            raise InvenioWebSubmitWarning(_('Unable to move field at position %(x_from)s to position %(x_to)s on page %(x_page)s of submission \'%(x_sub)s%(x_subm)s\' - Invalid Field Position Numbers',
                                            x_from=movefieldfromposn, x_to=movefieldtoposn, x_page=pagenum, x_sub=action, x_subm=doctype))
        except InvenioWebSubmitWarning as exc:
            register_exception(stream='warning')
            #warnings.append(exc.message)
        #warnings.append(('WRN_WEBSUBMITADMIN_INVALID_FIELD_NUMBERS_SUPPLIED_WHEN_TRYING_TO_MOVE_FIELD_ON_SUBMISSION_PAGE', \
                         #movefieldfromposn, movefieldtoposn, pagenum, "%s%s" % (action, doctype)))
            user_msg.append("""Unable to move field from position %s to position %s on page %s of submission %s%s - field position numbers invalid""" \
                        % (movefieldfromposn, movefieldtoposn, pagenum, action, doctype))
    elif movefield_res == 2:
        ## failed to swap 2 fields - couldn't move field1 to temp position
        try:
            raise InvenioWebSubmitWarning(_('Unable to swap field at position %(x_from)s with field at position %(x_to)s on page %(x_page)s of submission %(x_sub)s - could not move field at position %(x_subm)s to temporary field location',
                                            x_from=movefieldfromposn, x_to=movefieldtoposn, x_page=pagenum, x_sub=action, x_subm=doctype))
        except InvenioWebSubmitWarning as exc:
            register_exception(stream='warning')
            #warnings.append(exc.message)
        #warnings.append(('WRN_WEBSUBMITADMIN_UNABLE_TO_SWAP_TWO_FIELDS_ON_SUBMISSION_PAGE_COULDNT_MOVE_FIELD1_TO_TEMP_POSITION', \
                         #movefieldfromposn, movefieldtoposn, pagenum, "%s%s" % (action, doctype)))
            user_msg.append("""Unable to move field from position %s to position %s on page %s of submission %s%s""" \
                        % (movefieldfromposn, movefieldtoposn, pagenum, action, doctype))
    elif movefield_res == 3:
        ## failed to swap 2 fields on submission page - couldn't move field2 to field1 position
        try:
            raise InvenioWebSubmitWarning(_('Unable to swap field at position %(x_from)s with field at position %(x_to)s on page %(x_page)s of submission %(x_sub)s - could not move field at position %(x_posfrom)s to position %(x_posto)s. Please ask Admin to check that a field was not stranded in a temporary position',
                                            x_from=movefieldfromposn, x_to=movefieldtoposn, x_page=pagenum, x_sub=action, x_posfrom=doctype, x_posto=movefieldtoposn))
        except InvenioWebSubmitWarning as exc:
            register_exception(stream='warning')
            #warnings.append(exc.message)
        #warnings.append(('WRN_WEBSUBMITADMIN_UNABLE_TO_SWAP_TWO_FIELDS_ON_SUBMISSION_PAGE_COULDNT_MOVE_FIELD2_TO_FIELD1_POSITION', \
                          #movefieldfromposn, movefieldtoposn, pagenum, "%s%s" % (action, doctype), movefieldtoposn, movefieldfromposn))
            user_msg.append("""Unable to move field from position %s to position %s on page %s of submission %s%s - See Admin if field order is broken""" \
                        % (movefieldfromposn, movefieldtoposn, pagenum, action, doctype))
    elif movefield_res == 4:
        ## failed to swap 2 fields in submission page - couldnt swap field at temp position to field2 position
        try:
            raise InvenioWebSubmitWarning(_('Unable to swap field at position %(x_from)s with field at position %(x_to)s on page %(x_page)s of submission %(x_sub)s - could not move field that was located at position %(x_posfrom)s to position %(x_posto)s from temporary position. Field is now stranded in temporary position and must be corrected manually by an Admin',
                                            x_from=movefieldfromposn, x_to=movefieldtoposn, x_page=pagenum, x_sub=action, x_posfrom=movefieldfromposn, x_posto=movefieldtoposn))
        except InvenioWebSubmitWarning as exc:
            register_exception(stream='warning')
            #warnings.append(exc.message)
        #warnings.append(('WRN_WEBSUBMITADMIN_UNABLE_TO_SWAP_TWO_FIELDS_ON_SUBMISSION_PAGE_COULDNT_MOVE_FIELD1_TO_POSITION_FIELD2_FROM_TEMPORARY_POSITION', \
                         #movefieldfromposn, movefieldtoposn, pagenum, "%s%s" % (action, doctype), movefieldfromposn, movefieldtoposn))
            user_msg.append("""Unable to move field from position %s to position %s on page %s of submission %s%s - Field-order is now broken and must be corrected by Admin""" \
                        % (movefieldfromposn, movefieldtoposn, pagenum, action, doctype))
    elif movefield_res == 5:
        ## failed to decrement the position of all fields below the field that was moved to a temp position
        try:
            raise InvenioWebSubmitWarning(_('Unable to move field at position %(x_from)s to position %(x_to)s on page %(x_page)s of submission %(x_sub)s - could not decrement the position of the fields below position %(x_pos)s. Tried to recover - please check that field ordering is not broken',
                                            x_from=movefieldfromposn, x_to=movefieldtoposn, x_page=pagenum, x_sub=action, x_posfrom=movefieldfromposn))
        except InvenioWebSubmitWarning as exc:
            register_exception(stream='warning')
            #warnings.append(exc.message)
        #warnings.append(('WRN_WEBSUBMITADMIN_UNABLE_TO_MOVE_FIELD_TO_NEW_POSITION_ON_SUBMISSION_PAGE_COULDNT_DECREMENT_POSITION_OF_FIELDS_BELOW_FIELD1', \
                         #movefieldfromposn, movefieldtoposn, pagenum, "%s%s" % (action, doctype), movefieldfromposn))
            user_msg.append("""Unable to move field from position %s to position %s on page %s of submission %s%s - See Admin if field-order is broken""" \
                        % (movefieldfromposn, movefieldtoposn, pagenum, action, doctype))
    elif movefield_res == 6:
        ## failed to increment position of fields in and below position into which 'movefromfieldposn' is to be inserted
        try:
            raise InvenioWebSubmitWarning(_('Unable to move field at position %(x_from)s to position %(x_to)s on page %(x_page)s of submission %(x_sub)s%(x_subm)s - could not increment the position of the fields at and below position %(x_frompos)s. The field that was at position %(x_topos)s is now stranded in a temporary position.',
                                            x_from=movefieldfromposn, x_to=movefieldtoposn, x_page=pagenum, x_sub=action, x_subm=doctype, x_frompos=movefieldtoposn, x_topos=movefieldfromposn))
        except InvenioWebSubmitWarning as exc:
            register_exception(stream='warning')
            #warnings.append(exc.message)
        #warnings.append(('WRN_WEBSUBMITADMIN_UNABLE_TO_MOVE_FIELD_TO_NEW_POSITION_ON_SUBMISSION_PAGE_COULDNT_INCREMENT_POSITION_OF_FIELDS_AT_AND_BELOW_FIELD2', \
                         #movefieldfromposn, movefieldtoposn, pagenum, "%s%s" % (action, doctype), movefieldtoposn, movefieldfromposn))
            user_msg.append("""Unable to move field from position %s to position %s on page %s of submission %s%s - Field-order is now broken and must be corrected by Admin""" \
                        % (movefieldfromposn, movefieldtoposn, pagenum, action, doctype))
    else:
        ## successful update:
        try:
            raise InvenioWebSubmitWarning(_('Moved field from position %(x_from)s to position %(x_to)s on page %(x_page)s of submission \'%(x_sub)s%(x_subm)s\'.',
                                            x_from=movefieldfromposn, x_to=movefieldtoposn, x_page=pagenum, x_sub=action, x_subm=doctype))
        except InvenioWebSubmitWarning as exc:
            register_exception(stream='warning')
            #warnings.append(exc.message)
        #warnings.append(('WRN_WEBSUBMITADMIN_MOVED_FIELD_ON_SUBMISSION_PAGE', movefieldfromposn, movefieldtoposn, pagenum, "%s%s" % (action, doctype)))
            user_msg.append("""Successfully moved field from position %s to position %s on page %s of submission %s%s""" \
                        % (movefieldfromposn, movefieldtoposn, pagenum, action, doctype))

    (title, body) = _create_configure_doctype_submission_page_elements_form(doctype=doctype, action=action, pagenum=pagenum, user_msg=user_msg)
    return (title, body)

def _configure_doctype_delete_field_from_submissionpage(doctype, action, pagenum, fieldnum):
    """Delete a field from a submission page"""
    _ = gettext_set_language(CFG_SITE_LANG)
    user_msg = []
    del_res = delete_a_field_from_submissionpage_then_reorder_fields_below_to_fill_vacant_position(doctype=doctype,
                                                                                                   action=action,
                                                                                                   pagenum=pagenum,
                                                                                                   fieldposn=fieldnum)
    if del_res == 1:
        try:
            raise InvenioWebSubmitWarning(_('Unable to delete field at position %(x_from)s from page %(x_to)s of submission \'%(x_sub)s\'',
                                            x_from=fieldnum, x_page=pagenum, x_sub=action))
        except InvenioWebSubmitWarning as exc:
            register_exception(stream='warning')
            #warnings.append(exc.message)
        #warnings.append(('WRN_WEBSUBMITADMIN_UNABLE_TO_DELETE_FIELD_FROM_SUBMISSION_PAGE', fieldnum, pagenum, "%s%s" % (action, doctype)))
            user_msg.append("Unable to delete field at position %s from page number %s of submission %s%s" % (fieldnum, pagenum, action, doctype))
    else:
        ## deletion was OK
        user_msg.append("Field deleted")
        try:
            raise InvenioWebSubmitWarning(_('Unable to delete field at position %(x_from)s from page %(x_to)s of submission \'%(x_sub)s%(x_subm)s\'',
                                            x_from=fieldnum, x_to=pagenum, x_sub=action, x_subm=doctype))
        except InvenioWebSubmitWarning as exc:
            register_exception(stream='warning')
            #warnings.append(exc.message)
        #warnings.append(('WRN_WEBSUBMITADMIN_DELETED_FIELD_FROM_SUBMISSION_PAGE', fieldnum, pagenum, "%s%s" % (action, doctype)))
    (title, body) = _create_configure_doctype_submission_page_elements_form(doctype=doctype, action=action, pagenum=pagenum, user_msg=user_msg)
    return (title, body)

def _create_configure_doctype_submission_page_elements_form(doctype, action, pagenum, movefieldfromposn="", user_msg=""):
    ## get list of elements for page:
    title = """Submission Elements found on Page %s of the "%s" Submission of the "%s" Document Type:"""\
            % (pagenum, action, doctype)
    body = ""
    raw_page_elements = get_details_allsubmissionfields_on_submission_page(doctype=doctype, action=action, pagenum=pagenum)
    ## correctly stringify page elements for the template:
    page_elements = []
    for element in raw_page_elements:
        page_elements.append(stringify_list_elements(element))
    body = websubmitadmin_templates.tmpl_configuredoctype_list_submissionelements(doctype=doctype,
                                                                                  action=action,
                                                                                  pagenum=pagenum,
                                                                                  page_elements=page_elements,
                                                                                  movefieldfromposn=movefieldfromposn,
                                                                                  user_msg=user_msg)
    return (title, body)

def perform_request_configure_doctype_submissionpages(doctype,
                                                      action,
                                                      pagenum="",
                                                      movepage="",
                                                      movepagedirection="",
                                                      deletepage="",
                                                      deletepageconfirm="",
                                                      addpage=""):
    """Process requests relating to the submission pages of a doctype/submission"""
    body = ""
    user_msg = []
    try:
        pagenum = int(pagenum)
    except ValueError:
        pagenum = ""

    ## ensure that there is only one doctype for this doctype ID - simply display all doctypes with warning if not
    if doctype in ("", None):
        user_msg.append("""Unknown Document Type""")
        ## TODO : LOG ERROR
        all_doctypes = get_docid_docname_alldoctypes()
        body = websubmitadmin_templates.tmpl_display_alldoctypes(doctypes=all_doctypes, user_msg=user_msg)
        title = "Available WebSubmit Document Types"
        return (title, body)

    numrows_doctype = get_number_doctypes_docid(docid=doctype)
    if numrows_doctype > 1:
        ## there are multiple doctypes with this doctype ID:
        ## TODO : LOG ERROR
        user_msg.append("""Multiple document types identified by "%s" exist - cannot configure at this time.""" \
                   % (doctype,))
        all_doctypes = get_docid_docname_alldoctypes()
        body = websubmitadmin_templates.tmpl_display_alldoctypes(doctypes=all_doctypes, user_msg=user_msg)
        title = "Available WebSubmit Document Types"
        return (title, body)
    elif numrows_doctype == 0:
        ## this doctype does not seem to exist:
        user_msg.append("""The document type identified by "%s" doesn't exist - cannot configure at this time.""" \
                   % (doctype,))
        ## TODO : LOG ERROR
        all_doctypes = get_docid_docname_alldoctypes()
        body = websubmitadmin_templates.tmpl_display_alldoctypes(doctypes=all_doctypes, user_msg=user_msg)
        title = "Available WebSubmit Document Types"
        return (title, body)

    ## ensure that this submission exists for this doctype:
    numrows_submission = get_number_submissions_doctype_action(doctype=doctype, action=action)
    if numrows_submission > 1:
        ## there are multiple submissions for this doctype/action ID:
        ## TODO : LOG ERROR
        user_msg.append("""The Submission "%s" seems to exist multiple times for the Document Type "%s" - cannot configure at this time.""" \
                   % (action, doctype))
        (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
        return (title, body)
    elif numrows_submission == 0:
        ## this submission does not seem to exist for this doctype:
        user_msg.append("""The Submission "%s" doesn't exist for the "%s" Document Type - cannot configure at this time.""" \
                   % (action, doctype))
        ## TODO : LOG ERROR
        (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
        return (title, body)

    ## submission valid
    if addpage != "":
        ## add a new page to a submission:
        error_code = add_submission_page_doctype_action(doctype=doctype, action=action)
        if error_code == 0:
            ## success
            user_msg.append("""A new Submission Page has been added into the last position""")
        else:
            ## could not move it
            user_msg.append("""Unable to add a new Submission Page""")
        (title, body) = _create_configure_doctype_submission_pages_form(doctype=doctype,
                                                                        action=action,
                                                                        user_msg=user_msg)
    elif movepage != "":
        ## user wants to move a page upwards in the order
        (title, body) = _configure_doctype_move_submission_page(doctype=doctype,
                                                                action=action, pagenum=pagenum, direction=movepagedirection)
    elif deletepage != "":
        ## user wants to delete a page:
        if deletepageconfirm != "":
            ## confirmation of deletion has been provided - proceed
            (title, body) = _configure_doctype_delete_submission_page(doctype=doctype,
                                                                      action=action, pagenum=pagenum)
        else:
            ## user has not yet confirmed the deletion of a page - prompt for confirmation
            (title, body) = _create_configure_doctype_submission_pages_form(doctype=doctype,
                                                                            action=action,
                                                                            deletepagenum=pagenum)
    else:
        ## default - display details of submission pages for this submission:
        (title, body) = _create_configure_doctype_submission_pages_form(doctype=doctype, action=action)
    return (title, body)

def _configure_doctype_move_submission_page(doctype, action, pagenum, direction):
    user_msg = []
    ## Sanity checking:
    if direction.lower() not in ("up", "down"):
        ## invalid direction:
        user_msg.append("""Invalid Page destination - no action was taken""")
        (title, body) = _create_configure_doctype_submission_pages_form(doctype=doctype,
                                                                        action=action,
                                                                        user_msg=user_msg)
        return (title, body)

    ## swap the pages:
    if direction.lower() == "up":
        error_code = swap_elements_adjacent_pages_doctype_action(doctype=doctype, action=action,
                                                                 page1=pagenum, page2=pagenum-1)
    else:
        error_code = swap_elements_adjacent_pages_doctype_action(doctype=doctype, action=action,
                                                                 page1=pagenum, page2=pagenum+1)
    if error_code == 0:
        ## pages swapped successfully:
        ## TODO : LOG PAGE SWAP
        user_msg.append("""Page %s was successfully moved %swards""" % (pagenum, direction.capitalize()))
    elif error_code == 1:
        ## pages are not adjacent:
        user_msg.append("""Unable to move page - only adjacent pages can be swapped around""")
    elif error_code == 2:
        ## at least one page out of legal range (e.g. trying to move a page to a position higher or lower
        ## than the number of pages:
        user_msg.append("""Unable to move page to illegal position""")
    elif error_code in (3, 4):
        ## Some sort of problem moving fields around!
        ## TODO : LOG ERROR
        user_msg.append("""Error: there was a problem swapping the submission elements to their new pages.""")
        user_msg.append("""An attempt was made to return the elements to their original pages - you """\
                        """should verify that this was successful, or ask your administrator"""\
                        """ to fix the problem manually""")
    elif error_code == 5:
        ## the elements from the first page were left stranded in the temporary page!
        ## TODO : LOG ERROR
        user_msg.append("""Error: there was a problem swapping the submission elements to their new pages.""")
        user_msg.append("""Some elements were left stranded on a temporary page. Please ask your administrator to"""\
                        """ fix this problem manually""")
    (title, body) = _create_configure_doctype_submission_pages_form(doctype=doctype, action=action, user_msg=user_msg)
    return (title, body)

def _configure_doctype_delete_submission_page(doctype, action, pagenum):
    user_msg = []
    num_pages = get_numbersubmissionpages_doctype_action(doctype=doctype, action=action)
    if num_pages > 0:
        ## proceed with deletion
        error_code = delete_allfields_submissionpage_doctype_action(doctype=doctype, action=action, pagenum=pagenum)
        if error_code == 0:
            ## everything OK
            ## move elements from pages above the deleted page down by one page:
            decrement_by_one_pagenumber_submissionelements_abovepage(doctype=doctype, action=action, frompage=pagenum)
            ## now decrement the number of pages associated with the submission:
            error_code = decrement_by_one_number_submissionpages_doctype_action(doctype=doctype, action=action)
            if error_code == 0:
                ## successfully deleted submission page
                ## TODO : LOG DELETION
                user_msg.append("""Page number %s of Submission %s was successfully deleted."""\
                                % (pagenum, action))
                (title, body) = _create_configure_doctype_submission_pages_form(doctype=doctype,
                                                                                action=action,
                                                                                user_msg=user_msg)
            else:
                ## error - either submission didn't exist, or multiple instances found
                ## TODO : LOG ERROR
                user_msg.append("""The Submission elements were deleted from Page %s of the Submission "%s"."""\
                                """ However, it was not possible to delete the page itself."""\
                                % (pagenum, action))
                (title, body) = _create_configure_doctype_submission_pages_form(doctype=doctype,
                                                                                action=action,
                                                                                user_msg=user_msg)
        else:
            ## unable to delete some or all fields from the page
            ## TODO : LOG ERROR
            user_msg.append("""Error: Unable to delete some field elements from Page %s of Submission %s%s - """\
                            """Page not deleted!""" % (pagenum, action, doctype))
            (title, body) = _create_configure_doctype_submission_pages_form(doctype=doctype,
                                                                            action=action,
                                                                            user_msg=user_msg)
    elif num_pages == 0:
        ## no pages to delete for this submission
        user_msg.append("""This Submission has no Pages - Cannot delete a Page!""")
        (title, body) = _create_configure_doctype_submission_pages_form(doctype=doctype,
                                                                        action=action,
                                                                        user_msg=user_msg)
    else:
        ## error - couldn't determine the number of pages for submission
        ## TODO : LOG ERROR
        user_msg.append("""Unable to determine number of Submission Pages for Submission "%s" - """\
                        """Cannot delete page %s"""\
                        % (action, pagenum))
        (title, body) = _create_configure_doctype_form(doctype=doctype, user_msg=user_msg)
    return (title, body)

def _create_configure_doctype_submission_pages_form(doctype,
                                                    action,
                                                    deletepagenum="",
                                                    user_msg=""):
    """Perform the necessary steps in order to display a list of the pages belonging to a given
       submission of a given document type.
       @param doctype: (string) the unique ID of the document type.
       @param action: (string) the unique name/ID of the action.
       @param user_msg: (string, or list) any message(s) to be displayed to the user.
       @return: a tuple containing 2 strings - the page title and the page body.
    """
    title = """Details of the Pages of the "%s" Submission of the "%s" Document Type:""" % (action, doctype)
    submission_dets = get_cd_md_numbersubmissionpages_doctype_action(doctype=doctype, action=action)
    if len(submission_dets) > 0:
        cd = str(submission_dets[0][0])
        md = str(submission_dets[0][1])
        num_pages = submission_dets[0][2]
    else:
        (cd, md, num_pages) = ("", "", "0")
    body = websubmitadmin_templates.tmpl_configuredoctype_list_submissionpages(doctype=doctype,
                                                                               action=action,
                                                                               number_pages=num_pages,
                                                                               cd=cd,
                                                                               md=md,
                                                                               deletepagenum=deletepagenum,
                                                                               user_msg=user_msg)
    return (title, body)
