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

from invenio.legacy.dbquery import run_sql
from invenio.legacy.websubmit.admin_config import *
from random import randint

# Functions related to the organisation of catalogues:

def insert_submission_collection(collection_name):
    qstr = """INSERT INTO sbmCOLLECTION (name) VALUES (%s)"""
    qres = run_sql(qstr, (collection_name,))
    return int(qres)

def update_score_of_collection_child_of_submission_collection_at_scorex(id_father, old_score, new_score):
    qstr = """UPDATE sbmCOLLECTION_sbmCOLLECTION """ \
           """SET catalogue_order=%s WHERE id_father=%s AND catalogue_order=%s"""
    qres = run_sql(qstr, (new_score, id_father, old_score))
    return 0

def update_score_of_collection_child_of_submission_collection_with_colid_and_scorex(id_father,
                                                                                    id_son,
                                                                                    old_score,
                                                                                    new_score):
    qstr = """UPDATE sbmCOLLECTION_sbmCOLLECTION """ \
           """SET catalogue_order=%s """ \
           """WHERE id_father=%s AND id_son=%s AND catalogue_order=%s"""
    qres = run_sql(qstr, (new_score, id_father, id_son, old_score))
    return 0

def update_score_of_doctype_child_of_submission_collection_at_scorex(id_father, old_score, new_score):
    qstr = """UPDATE sbmCOLLECTION_sbmDOCTYPE """ \
           """SET catalogue_order=%s WHERE id_father=%s AND catalogue_order=%s"""
    qres = run_sql(qstr, (new_score, id_father, old_score))
    return 0

def update_score_of_doctype_child_of_submission_collection_with_doctypeid_and_scorex(id_father,
                                                                                     id_son,
                                                                                     old_score,
                                                                                     new_score):
    qstr = """UPDATE sbmCOLLECTION_sbmDOCTYPE """ \
           """SET catalogue_order=%s """ \
           """WHERE id_father=%s AND id_son=%s AND catalogue_order=%s"""
    qres = run_sql(qstr, (new_score, id_father, id_son, old_score))
    return 0

def get_id_father_of_collection(collection_id):
    qstr = """SELECT id_father FROM sbmCOLLECTION_sbmCOLLECTION """ \
           """WHERE id_son=%s """ \
           """LIMIT 1"""
    qres = run_sql(qstr, (collection_id,))
    try:
        return int(qres[0][0])
    except (TypeError, IndexError):
        return None

def get_maximum_catalogue_score_of_collection_children_of_submission_collection(collection_id):
    qstr = """SELECT IFNULL(MAX(catalogue_order), 0) """ \
           """FROM sbmCOLLECTION_sbmCOLLECTION """ \
           """WHERE id_father=%s"""
    qres = int(run_sql(qstr, (collection_id,))[0][0])
    return qres

def get_score_of_collection_child_of_submission_collection(id_father, id_son):
    qstr = """SELECT catalogue_order FROM sbmCOLLECTION_sbmCOLLECTION """ \
           """WHERE id_son=%s and id_father=%s """ \
           """LIMIT 1"""
    qres = run_sql(qstr, (id_son, id_father))
    try:
        return int(qres[0][0])
    except (TypeError, IndexError):
        return None

def get_score_of_previous_collection_child_above(id_father, score):
    qstr = """SELECT MAX(catalogue_order) """ \
           """FROM sbmCOLLECTION_sbmCOLLECTION """ \
           """WHERE id_father=%s and catalogue_order < %s"""
    qres = run_sql(qstr, (id_father, score))
    try:
        return int(qres[0][0])
    except (TypeError, IndexError):
        return None

def get_score_of_next_collection_child_below(id_father, score):
    qstr = """SELECT MIN(catalogue_order) """ \
           """FROM sbmCOLLECTION_sbmCOLLECTION """ \
           """WHERE id_father=%s and catalogue_order > %s"""
    qres = run_sql(qstr, (id_father, score))
    try:
        return int(qres[0][0])
    except (TypeError, IndexError):
        return None

def get_catalogue_score_of_doctype_child_of_submission_collection(id_father, id_son):
    qstr = """SELECT catalogue_order FROM sbmCOLLECTION_sbmDOCTYPE """ \
           """WHERE id_son=%s and id_father=%s """ \
           """LIMIT 1"""
    qres = run_sql(qstr, (id_son, id_father))
    try:
        return int(qres[0][0])
    except (TypeError, IndexError):
        return None

def get_score_of_previous_doctype_child_above(id_father, score):
    qstr = """SELECT MAX(catalogue_order) """ \
           """FROM sbmCOLLECTION_sbmDOCTYPE """ \
           """WHERE id_father=%s and catalogue_order < %s"""
    qres = run_sql(qstr, (id_father, score))
    try:
        return int(qres[0][0])
    except (TypeError, IndexError):
        return None

def get_score_of_next_doctype_child_below(id_father, score):
    qstr = """SELECT MIN(catalogue_order) """ \
           """FROM sbmCOLLECTION_sbmDOCTYPE """ \
           """WHERE id_father=%s and catalogue_order > %s"""
    qres = run_sql(qstr, (id_father, score))
    try:
        return int(qres[0][0])
    except (TypeError, IndexError):
        return None

def get_maximum_catalogue_score_of_doctype_children_of_submission_collection(collection_id):
    qstr = """SELECT IFNULL(MAX(catalogue_order), 0) """ \
           """FROM sbmCOLLECTION_sbmDOCTYPE """ \
           """WHERE id_father=%s"""
    qres = int(run_sql(qstr, (collection_id,))[0][0])
    return qres


def insert_collection_child_for_submission_collection(id_father, id_son, score):
    qstr = """INSERT INTO sbmCOLLECTION_sbmCOLLECTION (id_father, id_son, catalogue_order) """ \
           """VALUES (%s, %s, %s)"""
    qres = run_sql(qstr, (id_father, id_son, score))

def insert_doctype_child_for_submission_collection(id_father, id_son, score):
    qstr = """INSERT INTO sbmCOLLECTION_sbmDOCTYPE (id_father, id_son, catalogue_order) """ \
           """VALUES (%s, %s, %s)"""
    qres = run_sql(qstr, (id_father, id_son, score))

def get_doctype_children_of_collection(id_father):
    """Get details of all 'doctype' children of a given collection. For each doctype, get:
         * doctype ID
         * doctype long-name
         * doctype catalogue-order
       The document type children retrieved are ordered in ascending order of 'catalogue order'.
       @param id_father: (integer) - the ID of the parent collection for which doctype children are
        to be retrieved.
       @return: (tuple) of tuples. Each tuple is a row giving the following details of a doctype:
        (doctype_id, doctype_longname, doctype_catalogue_order)
    """
    ## query to retrieve details of doctypes attached to a given collection:
    qstr_doctype_children = """SELECT col_doctype.id_son, doctype.ldocname, col_doctype.catalogue_order """ \
                            """FROM sbmCOLLECTION_sbmDOCTYPE AS col_doctype """ \
                            """INNER JOIN sbmDOCTYPE AS doctype """ \
                            """ON col_doctype.id_son = doctype.sdocname """ \
                            """WHERE id_father=%s ORDER BY catalogue_order ASC"""
    res_doctype_children  = run_sql(qstr_doctype_children, (id_father,))
    ## return the result of this query:
    return res_doctype_children

def get_collection_children_of_collection(id_father):
    """Get the collection ids of all 'collection' children of a given collection.
       @param id_father: (integer) the ID of the parent collection for which collection are to
        be retrieved.
       @return: (tuple) of tuples. Each tuple is a row containing the collection ID of a 'collection' child
        of the given parent collection.
    """
    ## query to retrieve IDs of collections attached to a given collection:
    qstr_collection_children = """SELECT id_son FROM sbmCOLLECTION_sbmCOLLECTION WHERE id_father=%s ORDER BY catalogue_order ASC"""
    res_collection_children  = run_sql(qstr_collection_children, (id_father,))
    ## return the result of this query:
    return res_collection_children

def get_id_and_score_of_collection_children_of_collection(id_father):
    """Get the collection ids and catalogue score positions of all 'collection' children of
       a given collection.
       @param id_father: (integer) the ID of the parent collection for which collection are to
        be retrieved.
       @return: (tuple) of tuples. Each tuple is a row containing the collection ID and the catalogue-score
        position of a 'collection' child of the given parent collection: (id, catalogue-score)
    """
    ## query to retrieve IDs of collections attached to a given collection:
    qstr_collection_children = """SELECT id_son, catalogue_order """ \
                               """FROM sbmCOLLECTION_sbmCOLLECTION """ \
                               """WHERE id_father=%s ORDER BY catalogue_order ASC"""
    res_collection_children  = run_sql(qstr_collection_children, (id_father,))
    ## return the result of this query:
    return res_collection_children

def get_number_of_rows_for_submission_collection_as_submission_tree_branch(collection_id):
    """Get the number of rows found for a submission-collection as a branch of the
       submission tree.
       @param collection_id: (integer) - the id of the submission-collection.
       @return: (integer) - number of rows found by the query.
    """
    qstr = """SELECT COUNT(*) FROM sbmCOLLECTION_sbmCOLLECTION WHERE id_son=%s"""
    return int(run_sql(qstr, (collection_id,))[0][0])

def get_number_of_rows_for_submission_collection(collection_id):
    """Get the number of rows found for a submission-collection.
       @param collection_id: (integer) - the id of the submission-collection.
       @return: (integer) - number of rows found by the query.
    """
    qstr = """SELECT COUNT(*) FROM sbmCOLLECTION WHERE id=%s"""
    return int(run_sql(qstr, (collection_id,))[0][0])

def delete_submission_collection_details(collection_id):
    """Delete the details of a submission-collection from the database.
       @param collection_id: (integer) - the ID of the submission-collection whose details
        are to be deleted from the WebSubmit database.
       @return: (integer) - error code: 0 on successful delete; 1 on failure to delete.
    """
    qstr = """DELETE FROM sbmCOLLECTION WHERE id=%s"""
    run_sql(qstr, (collection_id,))
    ## check to see if submission-collection details deleted:
    numrows_submission_collection = get_number_of_rows_for_submission_collection(collection_id)
    if numrows_submission_collection == 0:
        ## everything OK - no doctype-children remain for this submission-collection
        return 0
    else:
        ## everything NOT OK - still rows remaining for this submission-collection
        ## make a last attempt to delete them:
        run_sql(qstr, (collection_id,))
        ## once more, check the number of rows remaining for this submission-collection:
        numrows_submission_collection = get_number_of_rows_for_submission_collection(collection_id)
        if numrows_submission_collection == 0:
            ## Everything OK - submission-collection deleted
            return 0
        else:
            ## still could not delete the submission-collection
            return 1

def delete_submission_collection_from_submission_tree(collection_id):
    """Delete a submission-collection from the submission tree.
       @param collection_id: (integer) - the ID of the submission-collection whose details
        are to be deleted from the WebSubmit database.
       @return: (integer) - error code: 0 on successful delete; 1 on failure to delete.
    """
    qstr = """DELETE FROM sbmCOLLECTION_sbmCOLLECTION WHERE id_son=%s"""
    run_sql(qstr, (collection_id,))
    ## check to ensure that the submission-collection was deleted from the tree:
    numrows_collection = \
       get_number_of_rows_for_submission_collection_as_submission_tree_branch(collection_id)
    if numrows_collection == 0:
        ## everything OK - this submission-collection does not exist as a branch on the submission tree
        return 0
    else:
        ## submission-collection still exists as a branch of the submission tree
        ## try once more to delete it:
        run_sql(qstr, (collection_id,))
        numrows_collection = \
                  get_number_of_rows_for_submission_collection_as_submission_tree_branch(collection_id)
        if numrows_collection == 0:
            ## deleted successfully this time:
            return 0
        else:
            ## Still unable to delete
            return 1

def get_collection_name(collection_id):
    """Get the name of a given collection.
       @param collection_id: (integer) - the ID of the collection for which whose name is to be retrieved
       @return: (string or None) the name of the collection if it exists, None if no rows were returned
    """
    collection_name = None
    ## query to retrieve the name of a given collection:
    qstr_collection_name = """SELECT name FROM sbmCOLLECTION WHERE id=%s"""
    ## get the name of this collection:
    res_collection_name  = run_sql(qstr_collection_name, (collection_id,))
    try:
        collection_name = res_collection_name[0][0]
    except IndexError:
        pass
    ## return the collection name:
    return collection_name

def delete_doctype_children_from_submission_collection(collection_id):
    """Delete all doctype-children of a submission-collection.
       @param collection_id: (integer) - the ID of the submission-collection from which
        the doctype-children are to be deleted.
       @return: (integer) - error code: 0 on successful delete; 1 on failure to delete.
    """
    qstr = """DELETE FROM sbmCOLLECTION_sbmDOCTYPE WHERE id_father=%s"""
    run_sql(qstr, (collection_id,))
    ## check to see if doctype-children still remain attached to submission-collection:
    num_doctype_children = get_number_of_doctype_children_of_submission_collection(collection_id)
    if num_doctype_children == 0:
        ## everything OK - no doctype-children remain for this submission-collection
        return 0
    else:
        ## everything NOT OK - still doctype-children remaining for this submission-collection
        ## make a last attempt to delete them:
        run_sql(qstr, (collection_id,))
        ## once more, check the number of doctype-children remaining
        num_doctype_children = get_number_of_doctype_children_of_submission_collection(collection_id)
        if num_doctype_children == 0:
            ## Everything OK - all doctype-children deleted this time
            return 0
        else:
            ## still could not delete the doctype-children from this submission
            return 1

def get_details_of_all_submission_collections():
    """Get the id and name of all submission-collections.
       @return: (tuple) of tuples - (collection-id, collection-name)
    """
    qstr_collections = """SELECT id, name from sbmCOLLECTION order by id ASC"""
    res_collections  = run_sql(qstr_collections)
    return res_collections

def get_count_of_doctype_instances_at_score_for_collection(doctypeid, id_father, catalogue_score):
    """Get the number of rows found for a given doctype as attached to a given position on a query tree.
       @param doctypeid: (string) - the identifier for the given document type.
       @param id_father: (integer) - the id of the submission-collection to which the doctype is attached.
       @param catalogue_posn: (integer) - the score of the document type for that catalogue connection.
       @return: (integer) - number of rows found by the query.
    """
    qstr = """SELECT COUNT(*) FROM sbmCOLLECTION_sbmDOCTYPE WHERE id_father=%s AND id_son=%s AND catalogue_order=%s"""
    return int(run_sql(qstr, (id_father, doctypeid, catalogue_score))[0][0])

def get_number_of_doctype_children_of_submission_collection(collection_id):
    """Get the number of rows found for doctype-children as attached to a given submission-collection.
       @param collection_id: (integer) - the id of the submission-collection to which the doctype-children are attached.
       @return: (integer) - number of rows found by the query.
    """
    qstr = """SELECT COUNT(*) FROM sbmCOLLECTION_sbmDOCTYPE WHERE id_father=%s"""
    return int(run_sql(qstr, (collection_id,))[0][0])


def delete_doctype_from_position_on_submission_page(doctypeid, id_father, catalogue_score):
    """Delete a document type from a given score position of a given submission-collection.
       @param doctypeid: (string) - the ID of the document type that is to be deleted from the submission-collection.
       @param id_father: (integer) - the ID of the submission-collection from which the document type
        is to be deleted.
       @param catalogue_score: (integer) - the score of the submission-collection at which the
        document type to be deleted is connected.
       @return: (integer) - error code: 0 if delete was successful; 1 if delete failed;
    """
    qstr = """DELETE FROM sbmCOLLECTION_sbmDOCTYPE WHERE id_father=%s AND id_son=%s AND catalogue_order=%s"""
    run_sql(qstr, (id_father, doctypeid, catalogue_score))
    ## check to see whether this doctype was deleted:
    numrows_doctype = get_count_of_doctype_instances_at_score_for_collection(doctypeid, id_father, catalogue_score)
    if numrows_doctype == 0:
        ## delete successful
        return 0
    else:
        ## unsuccessful delete - try again
        run_sql(qstr, (id_father, doctypeid, catalogue_score))
        numrows_doctype = get_count_of_doctype_instances_at_score_for_collection(doctypeid, id_father, catalogue_score)
        if numrows_doctype == 0:
            ## delete successful
            return 0
        else:
            ## unable to delete
            return 1

def update_score_of_doctype_child_of_collection(id_father, id_son, old_catalogue_score, new_catalogue_score):
    """Update the score of a given doctype child of a submission-collection.
       @param id_father: (integer) - the ID of the submission-collection whose child's score is to be updated
       @param id_son: (string) - the ID of the document type to be updated
       @param old_catalogue_score: (integer) - the score of the submission-collection that the doctype is found
        at before update
       @param new_catalogue_score: (integer) - the new value of the doctype's score for the submission-collection
       @return: (integer) - 0
    """
    qstr = """UPDATE sbmCOLLECTION_sbmDOCTYPE SET catalogue_order=%s """ \
           """WHERE id_father=%s AND id_son=%s AND catalogue_order=%s"""
    run_sql(qstr, (new_catalogue_score, id_father, id_son, old_catalogue_score))
    return 0

def update_score_of_collection_child_of_collection(id_father, id_son, old_catalogue_score, new_catalogue_score):
    """Update the score of a given collection child ofa submission-collection.
       @param id_father: (integer) - the ID of the submission-collection whose child's score is to be updated
       @param id_son: (integer) - the ID of the collection type to be updated
       @param old_catalogue_score: (integer) - the score of the submission-collection that the collection is found
        at before update
       @param new_catalogue_score: (integer) - the new value of the collection's score for the submission-collection
       @return: (integer) - 0
    """
    qstr = """UPDATE sbmCOLLECTION_sbmCOLLECTION SET catalogue_order=%s """ \
           """WHERE id_father=%s AND id_son=%s AND catalogue_order=%s"""
    run_sql(qstr, (new_catalogue_score, id_father, id_son, old_catalogue_score))
    return 0


def normalize_scores_of_doctype_children_for_submission_collection(collection_id):
    """Normalize the scores of the doctype-children of a given submission-collection.
       I.e. set them into the format (1, 2, 3, 4, 5, [...]).
       @param collection_id: (integer) - the ID of the submission-collection whose
        doctype-children's scores are to be normalized.
       @return: None
    """
    ## Get all document types attached to the collection, ordered by score:
    doctypes = get_doctype_children_of_collection(collection_id)

    num_doctypes = len(doctypes)
    normal_score = 1
    ## for each document type, if score does not fit with counter, update it:
    for idx in xrange(0, num_doctypes):
        this_doctype_id    = doctypes[idx][0]
        this_doctype_score = int(doctypes[idx][2])
        if this_doctype_score != normal_score:
            ## Score of doctype is not good - correct it:
            update_score_of_doctype_child_of_collection(collection_id, this_doctype_id, \
                                                        this_doctype_score, normal_score)
        normal_score += 1
    return

def normalize_scores_of_collection_children_of_collection(collection_id):
    """Normalize the scores of the collection-children of a given submission-collection.
       I.e. set them into the format (1, 2, 3, 4, 5, [...]).
       @param collection_id: (integer) - the ID of the submission-collection whose
        collection-children's scores are to be normalized.
       @return: None
    """
    ## Get all document types attached to the collection, ordered by score:
    collections = get_id_and_score_of_collection_children_of_collection(collection_id)

    num_collections = len(collections)
    normal_score = 1
    ## for each collection, if score does not fit with counter, update it:
    for idx in xrange(0, num_collections):
        this_collection_id    = collections[idx][0]
        this_collection_score = int(collections[idx][1])
        if this_collection_score != normal_score:
            ## Score of collection is not good - correct it:
            update_score_of_collection_child_of_collection(collection_id, this_collection_id, \
                                                        this_collection_score, normal_score)
        normal_score += 1
    return


# Functions relating to WebSubmit ACTIONS, their addition, and their modification:

def update_action_details(actid, actname, working_dir, status_text):
    """Update the details of an action in the websubmit database IF there was only one action
       with that actid (sactname).
       @param actid: unique action id (sactname)
       @param actname: action name (lactname)
       @param working_dir: directory action works from (dir)
       @param status_text: text string indicating action status (statustext)
       @return: 0 (ZERO) if update is performed; 1 (ONE) if insert not performed due to rows existing for
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
       @return: an integer count of the number of actions in the websubmit database for this actid.
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
       @return: 0 (ZERO) if insert is performed; 1 (ONE) if insert not performed due to rows existing for
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


# Functions relating to WebSubmit Form Element JavaScript CHECKING FUNCTIONS, their addition, and their
# modification:

def get_number_jschecks_with_chname(chname):
    """Return the number of Checks found for a given check name/id.
       @param chname: Check name/id (chname) to query for
       @return: an integer count of the number of Checks in the WebSubmit database for this chname.
    """
    q = """SELECT COUNT(chname) FROM sbmCHECKS where chname=%s"""
    return int(run_sql(q, (chname,))[0][0])

def get_all_jscheck_names():
    """Return a list of the names of all WebSubmit JSChecks"""
    q = """SELECT DISTINCT(chname) FROM sbmCHECKS ORDER BY chname ASC"""
    res = run_sql(q)
    return map(lambda x: str(x[0]), res)

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
       @return: 0 (ZERO) if insert is performed; 1 (ONE) if insert not performed due to rows existing for
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
       @return: 0 (ZERO) if update is performed; 1 (ONE) if insert not performed due to rows existing for
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


# Functions relating to WebSubmit FUNCTIONS, their addition, and their modification:

def get_function_description(function):
    """Get and return a tuple containing the function description (description) for
       the function with the name held in the "function" parameter.
       @return: tuple of tuple (for one function): ((description,))
    """
    q = """SELECT description FROM sbmALLFUNCDESCR where function=%s"""
    return run_sql(q, (function,))

def get_function_parameter_vals_doctype(doctype, paramlist):
    res = []
    q = """SELECT name, value FROM sbmPARAMETERS WHERE doctype=%s AND name=%s"""
    for par in paramlist:
        r = run_sql(q, (doctype, par))
        if len(r) > 0:
            res.append(r[0])
        else:
            res.append((par, ""))
    return res

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
       @return: an integer count of the number of parameters matching the criteria.
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

def regulate_score_of_all_functions_in_step_to_ascending_multiples_of_10_for_submission(doctype, action, step):
    """Within a step of a submission, regulate the scores of all functions to multiples of 10.  For example, for
       the following:
          Submission   Func           Step     Score
           SBITEST      Print           2        10
           SBITEST      Run             2        11
           SBITEST      Alert           2        20
           SBITEST      End             2        50
       ...regulate the scores like this:
          Submission   Func           Step     Score
           SBITEST      Print           2        10
           SBITEST      Run             2        20
           SBITEST      Alert           2        30
           SBITEST      End             2        40
       @param doctype: (string) the unique ID of a document type
       @param action: (string) the unique ID of an action
       @param step: (integer) the number of the step in which functions scores are to be regulated
       @return: None
       @Exceptions raised:
          InvenioWebSubmitAdminWarningDeleteFailed - in the case that it wasn't possible to delete functions
    """
    functnres = get_name_step_score_of_all_functions_in_step_of_submission(doctype=doctype, action=action, step=step)
    i = 1
    score_order_broken = 0

    for functn in functnres:
        cur_functn_score = int(functn[2])
        if cur_functn_score != i * 10:
            ## this score is not a correct multiple of 10 for its place in the order
            score_order_broken = 1
        i += 1

    if score_order_broken == 1:
        ## the function scores were not good.
        ## delete the functions within this step
        try:
            delete_all_functions_in_step_of_submission(doctype=doctype, action=action, step=step)
        except InvenioWebSubmitAdminWarningDeleteFailed as e:
            ## unable to delete some or all functions
            ## pass the exception back up to the caller
            raise

        ## re-insert them with the correct scores
        i = 10
        for functn in functnres:
            insert_functn_name = functn[0]
            try:
                insert_function_into_submission_at_step_and_score(doctype=doctype, action=action,
                                                                  function=insert_functn_name,
                                                                  step=step, score=i)
            except InvenioWebSubmitAdminWarningReferentialIntegrityViolation as e:
                ## tried to insert a function that doesn't exist in WebSubmit DB
                ## TODO : LOG ERROR
                ## continue onto next loop iteration - don't increment value of I
                continue
            i += 10
    return

def get_number_of_functions_with_functionname_in_submission_at_step_and_score(doctype, action, function, step, score):
    """Get the number or rows for a particular function at a given step and score of a doctype submission"""
    q = """SELECT COUNT(doctype) FROM sbmFUNCTIONS where doctype=%s AND action=%s AND function=%s AND step=%s AND score=%s"""
    return int(run_sql(q, (doctype, action, function, step, score))[0][0])

def get_number_functions_doctypesubmission_step_score(doctype, action, step, score):
    """Get the number or rows for a particular function at a given step and score of a doctype submission"""
    q = """SELECT COUNT(doctype) FROM sbmFUNCTIONS where doctype=%s AND action=%s AND step=%s AND score=%s"""
    return int(run_sql(q, (doctype, action, step, score))[0][0])

def update_step_score_doctypesubmission_function(doctype, action, function, oldstep, oldscore, newstep, newscore):
    numrows_function = get_number_of_functions_with_functionname_in_submission_at_step_and_score(doctype=doctype, action=action,
                                                                                      function=function, step=oldstep, score=oldscore)
    if numrows_function == 1:
        q = """UPDATE sbmFUNCTIONS SET step=%s, score=%s WHERE doctype=%s AND action=%s AND function=%s AND step=%s AND score=%s"""
        run_sql(q, (newstep, newscore, doctype, action, function, oldstep, oldscore))
        return 0  ## Everything OK
    else:
        ## Everything NOT OK - perhaps this function doesn't exist at this posn - cannot update
        return 1

def move_position_submissionfunction_up(doctype, action, function, funccurstep, funccurscore):
    functions_above = get_functionname_step_score_allfunctions_beforereference_doctypesubmission(doctype=doctype,
                                                                                                 action=action,
                                                                                                 step=funccurstep,
                                                                                                 score=funccurscore)
    numrows_functions_above = len(functions_above)
    if numrows_functions_above < 1:
        ## there are no functions above this - nothing to do
        return 0 ## Everything OK
    ## get the details of the function above this one:
    name_function_above = functions_above[numrows_functions_above-1][0]
    step_function_above = int(functions_above[numrows_functions_above-1][1])
    score_function_above = int(functions_above[numrows_functions_above-1][2])
    if step_function_above < int(funccurstep):
        ## the function above the function to be moved is in a lower step. Put the function to be moved in the same step
        ## as the one above, but set its score to be greater by 10 than the one above
        error_code = update_step_score_doctypesubmission_function(doctype=doctype,
                                                                  action=action,
                                                                  function=function,
                                                                  oldstep=funccurstep,
                                                                  oldscore=funccurscore,
                                                                  newstep=step_function_above,
                                                                  newscore=int(score_function_above)+10)
        return error_code
    else:
        ## the function above is in the same step as the function to be moved. just switch them around (scores)
        ## first, delete the function above:
        error_code = delete_function_doctypesubmission_step_score(doctype=doctype,
                                                                  action=action,
                                                                  function=name_function_above,
                                                                  step=step_function_above,
                                                                  score=score_function_above)
        if error_code == 0:
            ## now update the function to be moved with the step and score of the function that was above it
            error_code = update_step_score_doctypesubmission_function(doctype=doctype,
                                                                      action=action,
                                                                      function=function,
                                                                      oldstep=funccurstep,
                                                                      oldscore=funccurscore,
                                                                      newstep=step_function_above,
                                                                      newscore=score_function_above)
            if error_code == 0:
                ## now insert the function that *was* above, into the position of the function that we have just moved
                try:
                    insert_function_into_submission_at_step_and_score(doctype=doctype, action=action,
                                                                      function=name_function_above,
                                                                      step=funccurstep,
                                                                      score=funccurscore)
                    return 0
                except InvenioWebSubmitAdminWarningReferentialIntegrityViolation as e:
                    return 1
            else:
                ## could not update the function that was to be moved! Try to re-insert that which was deleted
                try:
                    insert_function_into_submission_at_step_and_score(doctype=doctype, action=action,
                                                                      function=name_function_above,
                                                                      step=step_function_above,
                                                                      score=score_function_above)
                except InvenioWebSubmitAdminWarningReferentialIntegrityViolation as e:
                    pass
                return 1 ## Returning an ERROR code to signal that the move did not work
        else:
            ## Unable to delete the function above that which we want to move. Cannot move the function then.
            ## Return an error code to signal that things went wrong
            return 1

def add_10_to_score_of_all_functions_in_step_of_submission(doctype, action, step):
    """Add 10 to the score of all functions within a particular step of a submission.
       @param doctype: (string) the unique ID of a document type
       @param action: (string) the unique ID of an action
       @param step: (integer) the step in which all function scores are to be incremented by 10
       @return: None
    """
    q = """UPDATE sbmFUNCTIONS SET score=score+10 WHERE doctype=%s AND action=%s AND step=%s"""
    run_sql(q, (doctype, action, step))
    return

def update_score_of_allfunctions_from_score_within_step_in_submission_reduce_by_val(doctype, action, step, fromscore, val):
    q = """UPDATE sbmFUNCTIONS SET score=score-%s WHERE doctype=%s AND action=%s AND step=%s AND score >= %s"""
    run_sql(q, (val, doctype, action, step, fromscore))
    return

def add_10_to_score_of_all_functions_in_step_of_submission_and_with_score_equalto_or_above_val(doctype, action, step, fromscore):
    """Add 10 to the score of all functions within a particular step of a submission, but with a score equal-to,
       or higher than a given value (fromscore).
       @param doctype: (string) the unique ID of a document type
       @param action: (string) the unique ID of an action
       @param step: (integer) the step in which all function scores are to be incremented by 10
       @param fromscore: (integer) the score from which all scores are incremented by 10
       @return: None
    """
    q = """UPDATE sbmFUNCTIONS SET score=score+10 WHERE doctype=%s AND action=%s AND step=%s AND score >= %s"""
    run_sql(q, (doctype, action, step, fromscore))
    return

def get_number_of_submission_functions_in_step_between_two_scores(doctype, action, step, score1, score2):
    """Return the number of submission functions found within a particular step of a submission, and between
       two scores.
       @param doctype: (string) the unique ID of a document type
       @param action: (string) the unique ID of an action
       @param step: (integer) the number of the step
       @param score1: (integer) the first score boundary
       @param score2: (integer) the second score boundary
       @return: (integer) the number of functions found
    """
    q = """SELECT COUNT(doctype) FROM sbmFUNCTIONS WHERE doctype=%s AND action=%s AND step=%s AND (score BETWEEN %s AND %s)"""
    return int(run_sql(q, (doctype, action, step,
                           ((score1 <= score2 and score1) or (score2)),
                           ((score1 <= score2 and score2) or (score1))))[0][0])

def move_submission_function_from_one_position_to_another_position(doctype, action, movefuncname, movefuncfromstep,
                                                                   movefuncfromscore, movefunctostep, movefunctoscore):
    """Move a submission function from one score/step to another position.
       @param doctype: (string) the unique ID of a document type
       @param action: (string) the unique ID of an action
       @param movefuncname: (string) the name of the function to be moved
       @param movefuncfromstep: (integer) the step in which the function to be moved is located
       @param movefuncfromscore: (integer) the score at which the function to be moved is located
       @parm movefunctostep: (integer) the step to which the function is to be moved
       @param movefunctoscore: (integer) the to which the function is to be moved
       @return: None
       @exceptions raised:
          InvenioWebSubmitAdminWarningDeleteFailed - when unable to delete functions when regulating their scores
          InvenioWebSubmitAdminWarningNoRowsFound - when the function to be moved is not found
          InvenioWebSubmitAdminWarningInsertFailed - when regulating the scores of functions, and unable to insert
            a function
          InvenioWebSubmitAdminWarningReferentialIntegrityViolation - when the function to be inserted does not
            exist in WebSubmit
          InvenioWebSubmitAdminWarningNoUpdate - when the function was not moved because there would have been no
            change in its position, or because the function could not be moved for some reason

    """
    ## first check that there is a function "movefuncname"->"movefuncfromstep";"movefuncfromscore"
    numrows_movefunc = \
      get_number_of_functions_with_functionname_in_submission_at_step_and_score(doctype=doctype,
                                                                                action=action,
                                                                                function=movefuncname,
                                                                                step=movefuncfromstep,
                                                                                score=movefuncfromscore)
    if numrows_movefunc < 1:
        ## the function to move doesn't exist
        msg = """Could not move function [%s] at step [%s], score [%s] in submission [%s] to another position. """\
              """This function does not exist at this position."""\
              % (movefuncname, movefuncfromstep, movefuncfromscore, "%s%s" % (action, doctype))
        raise InvenioWebSubmitAdminWarningNoRowsFound(msg)

    ## check that the function is not being moved to the same position:
    if movefuncfromstep == movefunctostep:
        num_functs_between_old_and_new_posn =\
         get_number_of_submission_functions_in_step_between_two_scores(doctype=doctype,
                                                                       action=action,
                                                                       step=movefuncfromstep,
                                                                       score1=movefuncfromscore,
                                                                       score2=movefunctoscore)
        if num_functs_between_old_and_new_posn < 3 and (movefuncfromscore <= movefunctoscore):
            ## moving the function to the same position - no point
            msg = """The function [%s] of the submission [%s] was not moved from step [%s], score [%s] to """\
                  """step [%s], score [%s] as there would have been no change in position."""\
                  % (movefuncname, "%s%s" % (action, doctype), movefuncfromstep,
                     movefuncfromscore, movefunctostep, movefunctoscore)
            raise InvenioWebSubmitAdminWarningNoUpdate(msg)

    ## delete the function that is being moved:
    try:
        delete_the_function_at_step_and_score_from_a_submission(doctype=doctype, action=action,
                                                                function=movefuncname, step=movefuncfromstep,
                                                                score=movefuncfromscore)
    except InvenioWebSubmitAdminWarningDeleteFailed as e:
        ## unable to delete the function - cannot perform the move.
        msg = """Unable to move function [%s] at step [%s], score [%s] of submission [%s] - couldn't """\
              """delete the function from its current position."""\
              % (movefuncname, movefuncfromstep, movefuncfromscore, "%s%s" % (action, doctype))
        raise InvenioWebSubmitAdminWarningNoUpdate(msg)
    ## now insert the function into its new position and correct the order of all functions within that step:
    insert_function_into_submission_at_step_and_score_then_regulate_scores_of_functions_in_step(doctype=doctype,
                                                                                                action=action,
                                                                                                function=movefuncname,
                                                                                                step=movefunctostep,
                                                                                                score=movefunctoscore)
    ## regulate the scores of the functions in the step from which the function was moved
    try:
        regulate_score_of_all_functions_in_step_to_ascending_multiples_of_10_for_submission(doctype=doctype,
                                                                                            action=action,
                                                                                            step=movefuncfromstep)
    except InvenioWebSubmitAdminWarningDeleteFailed as e:
        ## couldn't delete some or all functions
        msg = """Moved function [%s] to step [%s], score [%s] of submission [%s]. However, when trying to regulate"""\
              """ scores of functions in step [%s], failed to delete some functions. Check that they have not been lost."""\
              % (movefuncname, movefuncfromstep, movefuncfromscore, "%s%s" % (action, doctype), movefuncfromstep)
        raise InvenioWebSubmitAdminWarningDeleteFailed(msg)
    ## finished
    return

def move_position_submissionfunction_fromposn_toposn(doctype, action, movefuncname, movefuncfromstep,
                                                    movefuncfromscore, movefunctoname, movefunctostep,
                                                    movefunctoscore):
    ## first check that there is a function "movefuncname"->"movefuncfromstep";"movefuncfromscore"
    numrows_movefunc = get_number_of_functions_with_functionname_in_submission_at_step_and_score(doctype=doctype,
                                                                                                 action=action,
                                                                                                 function=movefuncname,
                                                                                                 step=movefuncfromstep,
                                                                                                 score=movefuncfromscore)
    if numrows_movefunc < 1:
        ## the function to move does not exist!
        return 1
    ## now check that there is a function "movefunctoname"->"movefunctostep";"movefunctoscore"
    numrows_movefunctoposn = get_number_of_functions_with_functionname_in_submission_at_step_and_score(doctype=doctype,
                                                                                                       action=action,
                                                                                                       function=movefunctoname,
                                                                                                       step=movefunctostep,
                                                                                                       score=movefunctoscore)
    if numrows_movefunctoposn < 1:
        ## the function in the position to move to does not exist!
        return 1
    ##
    functions_above = get_functionname_step_score_allfunctions_beforereference_doctypesubmission(doctype=doctype,
                                                                                                 action=action,
                                                                                                 step=movefunctostep,
                                                                                                 score=movefunctoscore)
    numrows_functions_above = len(functions_above)
    if numrows_functions_above >= 1:
        function_above_name = functions_above[numrows_functions_above-1][0]
        function_above_step = int(functions_above[numrows_functions_above-1][1])
        function_above_score = int(functions_above[numrows_functions_above-1][2])
        ## Check that the place to which we are moving our function is NOT the same place that it is currently
        ## situated!

    if (numrows_functions_above < 1) or (int(functions_above[numrows_functions_above-1][1]) < int(movefunctostep)):  ### NICK SEPARATE THESE 2 OUT
        ## EITHER: there are no functions above the destination position; -OR- the function immediately above the
        ## destination position function is in a lower step.
        ## So, it is not important to care about any functions above for the move
        if ((numrows_functions_above < 1) and (int(movefunctoscore) > 10)):
            ## There is a space of 10 or more between the score of the function into whose place we are moving
            ## a function, and the one above it. Set the new function score for the moved function as the
            ## score of the function whose place it is taking in the order - 10
            error_code = update_step_score_doctypesubmission_function(doctype=doctype,
                                                                      action=action,
                                                                      function=movefuncname,
                                                                      oldstep=movefuncfromstep,
                                                                      oldscore=movefuncfromscore,
                                                                      newstep=movefunctostep,
                                                                      newscore=int(movefunctoscore)-10)
            return error_code
        elif (int(movefunctoscore) - 10 > function_above_score):
            ## There is a space of 10 or more between the score of the function into whose place we are moving
            ## a function, and the one above it. Set the new function score for the moved function as the
            ## score of the function whose place it is taking in the order - 10
            error_code = update_step_score_doctypesubmission_function(doctype=doctype,
                                                                      action=action,
                                                                      function=movefuncname,
                                                                      oldstep=movefuncfromstep,
                                                                      oldscore=movefuncfromscore,
                                                                      newstep=movefunctostep,
                                                                      newscore=int(movefunctoscore)-10)
            return error_code
        else:
            ## There is not a space of 10 or more in the scores of the function into whose position we are moving
            ## a function and the function above it. It is necessary to augment the score of all functions
            ## within the step of the one into whose position our function will be moved, from that position onwards,
            ## by 10; then the function to be moved can be inserted into the newly created space
            ## First, delete the function to be moved so that it is not changed during any augmentation:
            error_code = delete_function_doctypesubmission_step_score(doctype=doctype,
                                                                      action=action,
                                                                      function=movefuncname,
                                                                      step=movefuncfromstep,
                                                                      score=movefuncfromscore)
            if error_code == 0:
                ## deletion successful
                ## now augment the relevant scores:
                add_10_to_score_of_all_functions_in_step_of_submission_and_with_score_equalto_or_above_val(doctype=doctype,
                                                                                                           action=action,
                                                                                                           step=movefunctostep,
                                                                                                           fromscore=movefunctoscore)
                try:
                    insert_function_into_submission_at_step_and_score(doctype=doctype, action=action,
                                                                      function=movefuncname,
                                                                      step=movefunctostep,
                                                                      score=movefunctoscore)
                except InvenioWebSubmitAdminWarningReferentialIntegrityViolation as e:
                    return 1
                return 0
            else:
                ## could not delete it - cannot continue:
                return 1
    else:
        ## there are functions above the destination position function and they are in the same step as it.
        if int(movefunctoscore) - 10 > function_above_score:
            ## the function above has a score that is more than 10 below that into whose position we are moving
            ## a function. It is therefore possible to set the new score as movefunctoscore - 10:
            error_code = update_step_score_doctypesubmission_function(doctype=doctype,
                                                                      action=action,
                                                                      function=movefuncname,
                                                                      oldstep=movefuncfromstep,
                                                                      oldscore=movefuncfromscore,
                                                                      newstep=movefunctostep,
                                                                      newscore=int(movefunctoscore)-10)
            return error_code
        else:
            ## there is not a space of 10 or more in the scores of the function into whose position our function
            ## is to be moved and the function above it. It is necessary to augment the score of all functions
            ## within the step of the one into whose position our function will be moved, from that position onwards,
            ## by 10; then the function to be moved can be inserted into the newly created space

            ## First, delete the function to be moved so that it is not changed during any augmentation:
            error_code = delete_function_doctypesubmission_step_score(doctype=doctype,
                                                                      action=action,
                                                                      function=movefuncname,
                                                                      step=movefuncfromstep,
                                                                      score=movefuncfromscore)
            if error_code == 0:
                ## deletion successful
                ## now augment the relevant scores:
                add_10_to_score_of_all_functions_in_step_of_submission_and_with_score_equalto_or_above_val(doctype=doctype,
                                                                                                           action=action,
                                                                                                           step=movefunctostep,
                                                                                                           fromscore=movefunctoscore)
                try:
                    insert_function_into_submission_at_step_and_score(doctype=doctype, action=action,
                                                                      function=movefuncname,
                                                                      step=movefunctostep,
                                                                      score=movefunctoscore)
                except InvenioWebSubmitAdminWarningReferentialIntegrityViolation as e:
                    return 1
                return 0
            else:
                ## could not delete it - cannot continue:
                return 1

def move_position_submissionfunction_down(doctype, action, function, funccurstep, funccurscore):
    functions_below = get_functionname_step_score_allfunctions_afterreference_doctypesubmission(doctype=doctype,
                                                                                                action=action,
                                                                                                step=funccurstep,
                                                                                                score=funccurscore)
    numrows_functions_below = len(functions_below)
    if numrows_functions_below < 1:
        ## there are no functions below this - nothing to do
        return 0 ## Everything OK
    ## get the details of the function below this one:
    name_function_below = functions_below[0][0]
    step_function_below = int(functions_below[0][1])
    score_function_below = int(functions_below[0][2])
    if step_function_below > int(funccurstep):
        ## the function below is in a higher step: update all functions in that step with their score += 10,
        ## then place the function to be moved into that step with a score of that which the function below had
        if score_function_below <= 10:
            ## the score of the function below is 10 or less: add 10 to the score of all functions in that step
            add_10_to_score_of_all_functions_in_step_of_submission(doctype=doctype, action=action, step=step_function_below)
            numrows_function_stepscore_moveto = get_number_functions_doctypesubmission_step_score(doctype=doctype,
                                                                                                    action=action,
                                                                                                    step=step_function_below,
                                                                                                    score=score_function_below)
            if numrows_function_stepscore_moveto == 0:
                ## the score of the step that the function will be moved to is empty - it's safe to move the function there:
                error_code = update_step_score_doctypesubmission_function(doctype=doctype,
                                                                          action=action,
                                                                          function=function,
                                                                          oldstep=funccurstep,
                                                                          oldscore=funccurscore,
                                                                          newstep=step_function_below,
                                                                          newscore=score_function_below)
                return error_code
            else:
                ## could not move the functions below? Cannot move this function then
                return 1
        else:
            ## the function below is already on a score higher than 10 - just move the function into score 10 in that step
            error_code = update_step_score_doctypesubmission_function(doctype=doctype,
                                                                      action=action,
                                                                      function=function,
                                                                      oldstep=funccurstep,
                                                                      oldscore=funccurscore,
                                                                      newstep=step_function_below,
                                                                      newscore=10)
            return error_code
    else:
        ## the function below is in the same step. Switch it with this function
        ## first, delete the function below:
        error_code = delete_function_doctypesubmission_step_score(doctype=doctype,
                                                                  action=action,
                                                                  function=name_function_below,
                                                                  step=step_function_below,
                                                                  score=score_function_below)
        if error_code == 0:
            ## now update the function to be moved with the step and score of the function that was below it
            error_code = update_step_score_doctypesubmission_function(doctype=doctype,
                                                                      action=action,
                                                                      function=function,
                                                                      oldstep=funccurstep,
                                                                      oldscore=funccurscore,
                                                                      newstep=step_function_below,
                                                                      newscore=score_function_below)
            if error_code == 0:
                ## now insert the function that *was* below, into the position of the function that has just been moved
                try:
                    insert_function_into_submission_at_step_and_score(doctype=doctype, action=action,
                                                                      function=name_function_below,
                                                                      step=funccurstep, score=funccurscore)
                except InvenioWebSubmitAdminWarningReferentialIntegrityViolation as e:
                    return 1
                return 0
            else:
                ## could not update the function that was to be moved! Try to re-insert that which was deleted
                try:
                    insert_function_into_submission_at_step_and_score(doctype=doctype, action=action,
                                                                      function=name_function_below,
                                                                      step=step_function_below,
                                                                      score=score_function_below)
                except InvenioWebSubmitAdminWarningReferentialIntegrityViolation as e:
                    pass
                return 1 ## Returning an ERROR code to signal that the move did not work
        else:
            ## Unable to delete the function below that which we want to move. Cannot move the function then.
            ## Return an error code to signal that things went wrong
            return 1

def get_names_of_all_functions():
    """Return a list of the names of all WebSubmit functions (as strings).
       The function names will be sorted in ascending alphabetical order.
       @return: a list of strings
    """
    q = """SELECT function FROM sbmALLFUNCDESCR ORDER BY function ASC"""
    res = run_sql(q)
    return map(lambda x: str(x[0]), res)

def get_funcname_funcdesc_allfunctions():
    """Get and return a tuple of tuples containing the "function name" (function) and function textual
       description (description) for each WebSubmit function in the WebSubmit database.
       @return: tuple of tuples: ((function,description),(function,description)[,...])
    """
    q = """SELECT function, description FROM sbmALLFUNCDESCR ORDER BY function ASC"""
    return run_sql(q)

def get_function_usage_details(function):
    """Get the details of a function's usage in WebSubmit.
        This means get the following usage details:
         - doctype: the unique ID of the document type with which the usage is associated
         - docname: the long-name of the document type
         - action id: the unique ID of the action of the doctype, with which the usage is associated
         - action name: the long name of this action
         - function step: the step in which the instance of function usage occurs
         - function score: the score (of the above-mentioned step) at which the function is called

       @param function: (string) the name of the function whose WebSubmit usage is to be examined.
       @return: tuple of tuples whereby each tuple represents one instance of the function's usage:
            (doctype, docname, action id, action name, function-step, function-score)
    """
    q = """SELECT fun.doctype, dt.ldocname, fun.action, actn.lactname, fun.step, fun.score """ +\
        """FROM sbmDOCTYPE AS dt LEFT JOIN sbmFUNCTIONS AS fun ON (fun.doctype=dt.sdocname) """ +\
        """LEFT JOIN sbmIMPLEMENT as imp ON (fun.action=imp.actname AND fun.doctype=imp.docname) """ +\
        """LEFT JOIN sbmACTION AS actn ON (actn.sactname=imp.actname) WHERE fun.function=%s """ +\
        """ORDER BY dt.sdocname ASC, fun.action ASC, fun.step ASC, fun.score ASC"""
    return run_sql(q, (function,))

def get_number_of_functions_with_funcname(funcname):
    """Return the number of Functions found in the WebSubmit DB for a given function name.
       @param funcname: (string) the name of the function
       @return: an integer count of the number of Functions in the WebSubmit database for this function name.
    """
    q = """SELECT COUNT(function) FROM sbmALLFUNCDESCR where function=%s"""
    return int(run_sql(q, (funcname,))[0][0])

def insert_function_details(function, fundescr):
    """"""
    numrows_function = get_number_of_functions_with_funcname(function)
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
    numrows_function = get_number_of_functions_with_funcname(funcname)
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

# Functions relating to WebSubmit ELEMENTS, their addition, and their modification:

def get_number_elements_with_elname(elname):
    """Return the number of Elements found for a given element name/id.
       @param elname: Element name/id (name) to query for
       @return: an integer count of the number of Elements in the WebSubmit database for this elname.
    """
    q = """SELECT COUNT(name) FROM sbmFIELDDESC where name=%s"""
    return int(run_sql(q, (elname,))[0][0])

def get_doctype_action_pagenb_for_submissions_using_element(elname):
    """Get and return a tuple of tuples containing the doctype, the action, and the
       page number (pagenb) for the instances of use of the element identified by "elname".
       I.e. get the information about which submission pages the element is used on.
       @param elname: The unique identifier for an element ("name" in "sbmFIELDDESC",
                      "fidesc" in "sbmFIELD").
       @return: tuple of tuples (doctype, action, pagenb)
    """
    q = """SELECT subm.docname, subm.actname, sf.pagenb FROM sbmIMPLEMENT AS subm LEFT JOIN sbmFIELD AS sf ON sf.subname=CONCAT(subm.actname, subm.docname) WHERE sf.fidesc=%s ORDER BY sf.subname ASC, sf.pagenb ASC"""
    return run_sql(q, (elname,))

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

def get_all_element_names():
    """Return a list of the names of all "elements" in the WebSubmit DB.
       @return: a list of strings, where each string is a WebSubmit element
    """
    q = """SELECT DISTINCT(name) FROM sbmFIELDDESC ORDER BY name"""
    res = run_sql(q)
    return map(lambda x: str(x[0]), res)

def get_element_details(elname):
    """Get and return a tuple of tuples for all ELEMENTS with the element name "elname".
       @param elname: ELEMENT name (elname).
       @return: tuple of tuples (one tuple per element): (marccode,type,size,rows,cols,maxlength,
                                                            val,fidesc,cd,md,modifytext)
    """
    q = "SELECT el.marccode, el.type, el.size, el.rows, el.cols, el.maxlength, " + \
           "el.val, el.fidesc, el.cd, el.md, el.modifytext FROM sbmFIELDDESC AS el WHERE el.name=%s"
    return run_sql(q, (elname,))

def update_element_details(elname, elmarccode, eltype, elsize, elrows, elcols, elmaxlength, \
                           elval, elfidesc, elmodifytext):
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
       @return: 0 (ZERO) if update is performed; 1 (ONE) if update not performed due to rows existing for
                 given Element.
    """
    # Check record with code 'elname' does not already exist:
    numrows_elname = get_number_elements_with_elname(elname)
    if numrows_elname == 1:
        q = """UPDATE sbmFIELDDESC SET marccode=%s, type=%s, size=%s, rows=%s, cols=%s, maxlength=%s, """ +\
            """val=%s, fidesc=%s, modifytext=%s, md=CURDATE() WHERE name=%s"""
        run_sql(q, ( elmarccode,
                     (eltype != "" and eltype) or (None),
                     (elsize != "" and elsize) or (None),
                     (elrows != "" and elrows) or (None),
                     (elcols != "" and elcols) or (None),
                     (elmaxlength != "" and elmaxlength) or (None),
                     (elval != "" and elval) or (None),
                     (elfidesc != "" and elfidesc) or (None),
                     (elmodifytext != "" and elmodifytext) or (None),
                     elname
                   ) )
        return 0 # Everything is OK
    else:
        return 1 # Everything not OK: Either no rows or more than one row for element "elname"

def insert_element_details(elname, elmarccode, eltype, elsize, elrows, elcols, \
                           elmaxlength, elval, elfidesc, elmodifytext):
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
       @return: 0 (ZERO) if insert is performed; 1 (ONE) if insert not performed due to rows existing for
                 given Element.
    """
    # Check element record with code 'elname' does not already exist:
    numrows_elname = get_number_elements_with_elname(elname)
    if numrows_elname == 0:
        # insert new Check:
        q = """INSERT INTO sbmFIELDDESC (name, alephcode, marccode, type, size, rows, cols, """ +\
            """maxlength, val, fidesc, cd, md, modifytext, fddfi2) VALUES(%s, NULL, """ +\
            """%s, %s, %s, %s, %s, %s, %s, %s, CURDATE(), CURDATE(), %s, NULL)"""
        run_sql(q, ( elname,
                     elmarccode,
                     (eltype != "" and eltype) or (None),
                     (elsize != "" and elsize) or (None),
                     (elrows != "" and elrows) or (None),
                     (elcols != "" and elcols) or (None),
                     (elmaxlength != "" and elmaxlength) or (None),
                     (elval != "" and elval) or (None),
                     (elfidesc != "" and elfidesc) or (None),
                     (elmodifytext != "" and elmodifytext) or (None)
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
       @return: an integer count of the number of document types in the WebSubmit database for this doctype id.
    """
    q = """SELECT COUNT(sdocname) FROM sbmDOCTYPE where sdocname=%s"""
    return int(run_sql(q, (docid,))[0][0])

def get_number_functions_doctype(doctype):
    """Return the number of FUNCTIONS found for a given DOCUMENT TYPE.
       @param doctype: unique ID of doctype for which the number of functions are to be counted
       @return: an integer count of the number of functions in the WebSubmit database for this doctype.
    """
    q = """SELECT COUNT(doctype) FROM sbmFUNCTIONS where doctype=%s"""
    return int(run_sql(q, (doctype,))[0][0])

def get_number_functions_action_doctype(doctype, action):
    """Return the number of FUNCTIONS found for a given ACTION of a given DOCUMENT TYPE.
       @param doctype: unique ID of doctype for which the number of functions are to be counted
       @param action: the action (of the document type "doctype") that owns the functions to be counted
       @return: an integer count of the number of functions in the WebSubmit database for this doctype/action.
    """
    q = """SELECT COUNT(doctype) FROM sbmFUNCTIONS where doctype=%s AND action=%s"""
    return int(run_sql(q, (doctype, action))[0][0])

def get_number_of_functions_in_step_of_submission(doctype, action, step):
    """Return the number of FUNCTIONS within a step of a submission.
       @param doctype: (string) unique ID of a doctype
       @param action:  (string) unique ID of an action
       @param step:   (integer) the number of the step in which the functions to be counted are situated
       @return: an integer count of the number of functions found within the step of the submission
    """
    q = """SELECT COUNT(doctype) FROM sbmFUNCTIONS where doctype=%s AND action=%s AND step=%s"""
    return int(run_sql(q, (doctype, action, step))[0][0])

def get_number_categories_doctype(doctype):
    """Return the number of CATEGORIES (used to distinguish between submissions) found for a given DOCUMENT TYPE.
       @param doctype: unique ID of doctype for which submission categories are to be counted
       @return: an integer count of the number of categories in the WebSubmit database for this doctype.
    """
    q = """SELECT COUNT(doctype) FROM sbmCATEGORIES where doctype=%s"""
    return int(run_sql(q, (doctype,))[0][0])

def get_number_categories_doctype_category(doctype, categ):
    """Return the number of CATEGORIES (used to distinguish between submissions) found for a given
        DOCUMENT TYPE/CATEGORY NAME. Basically, test to see whether a given category already exists
        for a given document type.
       @param doctype: unique ID of doctype for which the submission category is to be tested
       @param categ: the category ID of the category to be tested for
       @return: an integer count of the number of categories in the WebSubmit database for this doctype.
    """
    q = """SELECT COUNT(sname) FROM sbmCATEGORIES where doctype=%s and sname=%s"""
    return int(run_sql(q, (doctype, categ))[0][0])

def get_number_parameters_doctype(doctype):
    """Return the number of PARAMETERS (used by functions) found for a given DOCUMENT TYPE.
       @param doctype: unique ID of doctype whose parameters are to be counted
       @return: an integer count of the number of parameters in the WebSubmit database for this doctype.
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
       @return: an integer count of the number of fields in the WebSubmit database for these submission(s)
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
       @return: an integer count of the number of submissions found for this doctype/action ID
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

def get_all_category_details_for_doctype(doctype):
    """Return all details (short-name, long-name, position number) of all CATEGORIES found for a
       given document type. If the position number is NULL, it will be assigned a value of zero.
       Categories will be ordered primarily by ascending position number and then by ascending
       alphabetical order of short-name.
       @param doctype: (string) The document type for which categories are to be retrieved.
       @return: (tuple) of tuples whereby each tuple is a row containing 3 items:
                            (short-name, long-name, position)
    """
    q = """SELECT sname, lname, score FROM sbmCATEGORIES where doctype=%s ORDER BY score ASC,""" \
        """ lname ASC"""
    return run_sql(q, (doctype,))

def get_all_categories_sname_lname_for_doctype_categsname(doctype, categsname):
    """Return the short and long names of all CATEGORIES found for a given DOCUMENT TYPE.
       @param doctype: unique ID of doctype for which submission categories are to be counted
       @return: a tuple of tuples: (sname, lname)
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

def get_all_categories_of_doctype_ordered_by_score_lname(doctype):
    """Return a tuple containing all categories of a given document type, ordered by
       ascending order of score, and ascending order of category long-name.
       @param doctype: (string) the document type ID.
       @return: (tuple) or tuples, whereby each tuple is a row representing a category, with
        the following structure:  (sname, lname, score)
    """
    qstr = """SELECT sname, lname, score FROM sbmCATEGORIES WHERE doctype=%s ORDER BY score ASC, lname ASC"""
    res = run_sql(qstr, (doctype,))
    return res

def update_score_of_doctype_category(doctype, categid, newscore):
    """Update the score of a given category of a given document type.
       @param doctype:  (string) the document type id
       @param categid:  (string) the category id
       @param newscore: (integer) the score that the category is to be given
       @return: (integer) - 0 on update of row; 1 on failure to update.
    """
    qstr = """UPDATE sbmCATEGORIES SET score=%s WHERE doctype=%s AND sname=%s"""
    res = run_sql(qstr, (newscore, doctype, categid))
    if int(res) > 0:
        ## row(s) were updated
        return 0
    else:
        ## no rows were updated
        return 1

def normalize_doctype_category_scores(doctype):
    """Get details of all categories of a given document type, ordered by score and long name;
       Loop through each category and check its score vs a counter in the result-set; if the score
       does not match the counter number, update the score of that category to match that of the
       counter. In this way, the category scores will be normalized sequentially. E.g.:
       categories numbered [1,4,6,8,9] will be allocated normalized scores [1,2,3,4,5]. I.e. the
       order won't change, but the scores will be corrected.
       @param doctype: (string) the document type id
       @return: (None)
    """
    all_categs = get_all_categories_of_doctype_ordered_by_score_lname(doctype)
    num_categs = len(all_categs)
    for row_idx in xrange(0, num_categs):
        ## Get the details of the current categories:
        cur_row_score   = row_idx + 1
        cur_categ_id    = all_categs[row_idx][0]
        cur_categ_lname = all_categs[row_idx][1]
        cur_categ_score = int(all_categs[row_idx][2])

        ## Check the score of the categ vs its position in the list:
        if cur_categ_score != cur_row_score:
            ## update this score:
            update_score_of_doctype_category(doctype=doctype,
                                             categid=cur_categ_id, newscore=cur_row_score)

def move_category_to_new_score(doctype, sourcecateg, destinationcatg):
    """Move a category of a document type from one score, to another.
       @param doctype: (string) -the ID of the document type whose categories are to be moved.
       @param sourcecateg: (string) - the category ID of the category to be moved.
       @param destinationcatg: (string) - the category ID of the category to whose position sourcecateg
        is to be moved.
       @return: (integer) 0 - successfully moved category; 1 - failed to correctly move category.
    """
    qstr_increment_scores_from_scorex = """UPDATE sbmCATEGORIES SET score=score+1 WHERE doctype=%s AND score >= %s"""
    move_categ_from_score = mave_categ_to_score = -1

    ## get the (categid, lname, score) of all categories for this document type:
    res_all_categs = get_all_categories_of_doctype_ordered_by_score_lname(doctype=doctype)
    num_categs = len(res_all_categs)

    ## if the category scores are not ordered properly (1,2,3,4,...), correct them.
    ## Also, get the row-count (therefore score-position) of the categ to be moved, and the destination score:
    for row_idx in xrange(0, num_categs):
        current_row_score = row_idx + 1
        current_categid = res_all_categs[row_idx][0]
        current_categ_score = int(res_all_categs[row_idx][2])

        ## Check the score of the categ vs its position in the list:
        if current_categ_score != current_row_score:
            ## bad score - fix it:
            update_score_of_doctype_category(doctype=doctype,
                                             categid=current_categid,
                                             newscore=current_row_score)

        if current_categid == sourcecateg:
            ## this is the place from which the category is being jumped-out:
            move_categ_from_score = current_row_score
        elif current_categid == destinationcatg:
            ## this is the place into which the categ is being jumped:
            move_categ_to_score = current_row_score

    ## If couldn't find the scores of both 'sourcecateg' and 'destinationcatg', return error:
    if -1 in (move_categ_from_score, move_categ_to_score) or \
           move_categ_from_score == mave_categ_to_score:
        ## either trying to move a categ to the same place or can't find both the source and destination categs:
        return 1

    ## add 1 to score of all categories from the score position into which the sourcecateg is to be moved:
    qres = run_sql(qstr_increment_scores_from_scorex, (doctype, move_categ_to_score))
    ## update the score of the category to be moved:
    update_score_of_doctype_category(doctype=doctype, categid=sourcecateg, newscore=move_categ_to_score)

    ## now re-order all category scores correctly:
    normalize_doctype_category_scores(doctype)
    return 0 ## return success

def move_category_by_one_place_in_score(doctype, categsname, direction):
    """Move a category up or down in score by one place.
       @param doctype: (string) - the ID of the document type to which the category belongs.
       @param categsname: (string) - the ID of the category to be moved.
       @param direction: (string) - the direction in which to move the category ('up' or 'down').
       @return: (integer) - 0 on successful move of category; 1 on failure to properly move category.
    """
    qstr_update_score = """UPDATE sbmCATEGORIES SET score=%s WHERE doctype=%s AND score=%s"""
    move_categ_score  = -1

    ## get the (categid, lname, score) of all categories for this document type:
    res_all_categs = get_all_categories_of_doctype_ordered_by_score_lname(doctype=doctype)
    num_categs = len(res_all_categs)

    ## if the category scores are not ordered properly (1,2,3,4,...), correct them
    ## Also, get the row-count (therefore score-position) of the categ to be moved
    for row_idx in xrange(0, num_categs):
        current_row_score = row_idx + 1
        current_categid = res_all_categs[row_idx][0]
        current_categ_score = int(res_all_categs[row_idx][2])

        ## Check the score of the categ vs its position in the list:
        if current_categ_score != current_row_score:
            ## bad score - fix it:
            update_score_of_doctype_category(doctype=doctype,
                                             categid=current_categid,
                                             newscore=current_row_score)

        if current_categid == categsname:
            ## this is the category to be moved:
            move_categ_score = current_row_score

    ## move the category:
    if direction.lower() == "up":
        ## Moving the category upwards (reducing its score):
        if num_categs > 1 and move_categ_score > 1:
            ## move the category above down by one place:
            run_sql(qstr_update_score, (move_categ_score, doctype, (move_categ_score - 1)))
            ## move the chosen category up:
            update_score_of_doctype_category(doctype=doctype,
                                             categid=categsname, newscore=(move_categ_score - 1))
            ## return success
            return 0
        else:
            ## return error - not enough categs, or categ already in first posn
            return 1

    elif direction.lower() == "down":
        ## move the category downwards (increasing its score):
        if num_categs > 1 and move_categ_score < num_categs:
            ## move category below, up by one place:
            run_sql(qstr_update_score, (move_categ_score, doctype, (move_categ_score + 1)))
            ## move the chosen category down:
            update_score_of_doctype_category(doctype=doctype,
                                             categid=categsname, newscore=(move_categ_score + 1))
            ## return success
            return 0
        else:
            ## return error - not enough categs, or categ already in last posn
            return 1
    else:
        ## invalid move direction - no action
        return 1

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

def get_functionname_step_score_allfunctions_afterreference_doctypesubmission(doctype, action, step, score):
    q = """SELECT function, step, score FROM sbmFUNCTIONS WHERE (doctype=%s AND action=%s) AND ((step=%s AND score > %s)""" \
        """ OR (step > %s)) ORDER BY step ASC, score ASC"""
    return run_sql(q, (doctype, action, step, score, step))

def get_functionname_step_score_allfunctions_beforereference_doctypesubmission(doctype, action, step, score):
    q = """SELECT function, step, score FROM sbmFUNCTIONS WHERE (doctype=%s AND action=%s) AND ((step=%s AND score < %s)"""
    if step > 1:
        q += """ OR (step < %s)"""
    q += """) ORDER BY step ASC, score ASC"""
    if step > 1:
        return run_sql(q, (doctype, action, step, score, step))
    else:
        return run_sql(q, (doctype, action, step, score))

def get_functionname_step_score_allfunctions_doctypesubmission(doctype, action):
    """Return the details (function name, step, score) of all functions beloning to the submission (action) of
       doctype.
       @param doctype: unique ID of doctype for which the details of the functions of the given submission
        are to be retrieved
       @param action: the action ID of the submission whose function details ore to be retrieved
       @return: a tuple of tuples: ((function, step, score),(function, step, score),[...])
    """
    q = """SELECT function, step, score FROM sbmFUNCTIONS where doctype=%s AND action=%s ORDER BY step ASC, score ASC"""
    return run_sql(q, (doctype, action))

def get_name_step_score_of_all_functions_in_step_of_submission(doctype, action, step):
    """Return a list of the details of all functions within a given step of a submission.
       The functions will be ordered in ascending order of score.
       @param doctype: (string) the unique ID of a document type
       @param action: (string) the unique ID of an action
       @param step: (integer) the step in which the functions are located
       @return: a tuple of tuples (function-name, step, score)
    """
    q = """SELECT function, step, score FROM sbmFUNCTIONS WHERE doctype=%s AND action=%s AND step=%s ORDER BY score ASC"""
    res = run_sql(q, (doctype, action, step))
    return res

def delete_function_doctypesubmission_step_score(doctype, action, function, step, score):
    """Delete a given function at a particular step/score for a given doctype submission"""
    q = """DELETE FROM sbmFUNCTIONS WHERE doctype=%s AND action=%s AND function=%s AND step=%s AND score=%s"""
    run_sql(q, (doctype, action, function, step, score))
    numrows_function_doctypesubmission_step_score = \
                get_number_of_functions_with_functionname_in_submission_at_step_and_score(doctype=doctype,
                                                                                          action=action,
                                                                                          function=function,
                                                                                          step=step,
                                                                                          score=score)
    if numrows_function_doctypesubmission_step_score == 0:
        ## Everything OK - function deleted
        return 0
    else:
        ## Everything NOT OK - still some functions remaining for doctype/action
        ## make a last attempt to delete them:
        run_sql(q, (doctype, action, function, step, score))
        ## check once more to see if functions remain:
        if get_number_of_functions_with_functionname_in_submission_at_step_and_score(doctype=doctype, action=action,
                                                                                     function=function, step=step,
                                                                                     score=score):
            ## Everything OK - all functions for this doctype/action were deleted successfully this time
            return 0
        else:
            ## still unable to recover - could not delete all functions for this doctype/action
            return 1

def delete_the_function_at_step_and_score_from_a_submission(doctype, action, function, step, score):
# THIS SHOULD REPLACE "delete_function_doctypesubmission_step_score(doctype, action, function, step, score)"
    """Delete a given function at a particular step/score for a given submission"""
    q = """DELETE FROM sbmFUNCTIONS WHERE doctype=%s AND action=%s AND function=%s AND step=%s AND score=%s"""
    run_sql(q, (doctype, action, function, step, score))
    numrows_deletedfunc = \
           get_number_of_functions_with_functionname_in_submission_at_step_and_score(doctype=doctype,
                                                                                     action=action,
                                                                                     function=function,
                                                                                     step=step,
                                                                                     score=score)
    if numrows_deletedfunc == 0:
        ## Everything OK - function deleted
        return
    else:
        ## Everything NOT OK - still some functions remaining for doctype/action
        ## make a last attempt to delete them:
        run_sql(q, (doctype, action, function, step, score))
        ## check once more to see if functions remain:
        numrows_deletedfunc = \
                get_number_of_functions_with_functionname_in_submission_at_step_and_score(doctype=doctype,
                                                                                          action=action,
                                                                                          function=function,
                                                                                          step=step,
                                                                                          score=score)
        if numrows_deletedfunc == 0:
            ## Everything OK - all functions for this doctype/action were deleted successfully this time
            return
        else:
            ## still unable to recover - could not delete all functions for this doctype/action
            msg = """Failed to delete the function [%s] at score [%s] of step [%s], from submission [%s]"""\
                  % (function, score, step, "%s%s" % (action, doctype))
            raise InvenioWebSubmitAdminWarningDeleteFailed(msg)

def delete_function_at_step_and_score_from_submission(doctype, action, function, step, score):
    """Delete the function at a particular step/score from a submission.
       @param doctype: (string) the unique ID of a document type
       @param action: (string) the unique ID of an action
       @param function: (string) the name of the function to be deleted
       @param step: (integer) the step in which the function to be deleted is found
       @param score: (integer) the score at which the function to be deleted is found
       @return: None
       @Exceptions raised:
         InvenioWebSubmitAdminWarningDeleteFailed - when unable to delete the function
    """
    q = """DELETE FROM sbmFUNCTIONS WHERE doctype=%s AND action=%s AND function=%s AND step=%s AND score=%s"""
    run_sql(q, (doctype, action, function, step, score))
    numrows_function_at_stepscore = \
            get_number_of_functions_with_functionname_in_submission_at_step_and_score(doctype=doctype,
                                                                                      action=action,
                                                                                      function=function,
                                                                                      step=step,
                                                                                      score=score)
    if numrows_function_at_stepscore == 0:
        ## Everything OK - function deleted
        return
    else:
        ## Everything NOT OK - still some functions remaining for doctype/action
        ## make a last attempt to delete them:
        run_sql(q, (doctype, action, function, step, score))
        ## check once more to see if functions remain:
        numrows_function_at_stepscore = \
           get_number_of_functions_with_functionname_in_submission_at_step_and_score(doctype=doctype,
                                                                                     action=action,
                                                                                     function=function,
                                                                                     step=step,
                                                                                     score=score)
        if numrows_function_at_stepscore == 0:
            ## Everything OK - all functions for this doctype/action were deleted successfully this time
            return
        else:
            ## still unable to recover - could not delete all functions for this doctype/action
            msg = """Failed to delete function [%s] from step [%s] and score [%s] from submission [%s]""" \
                  % (function, step, score, "%s%s" % (action, doctype))
            raise InvenioWebSubmitAdminWarningDeleteFailed(msg)

def delete_all_functions_in_step_of_submission(doctype, action, step):
    """Delete all functions from a given step of a submission.
       @param doctype: (string) the unique ID of a document type
       @param action: (string) the unique ID of an action
       @param step: (integer) the number of the step in which the functions are to be deleted
       @return: None
       @Exceptions raised:
           InvenioWebSubmitAdminWarningDeleteFailed - when unable to delete some or all of the functions
    """
    q = """DELETE FROM sbmFUNCTIONS WHERE doctype=%s AND action=%s AND step=%s"""
    run_sql(q, (doctype, action, step))
    numrows_functions_in_step = get_number_of_functions_in_step_of_submission(doctype=doctype,
                                                                              action=action,
                                                                              step=step)
    if numrows_functions_in_step == 0:
        ## all functions in step of submission deleted
        return
    else:
        ## couldn't delete all of the functions - try again
        run_sql(q, (doctype, action, step))
        numrows_functions_in_step = get_number_of_functions_in_step_of_submission(doctype=doctype,
                                                                                  action=action,
                                                                                  step=step)
        if numrows_functions_in_step == 0:
            ## success this time
            return
        else:
            msg = """Failed to delete all functions in step [%s] of submission [%s]""" % (step,
                                                                                          "%s%s" % (action, doctype))
            raise InvenioWebSubmitAdminWarningDeleteFailed(msg)

def delete_all_functions_foraction_doctype(doctype, action):
    """Delete all FUNCTIONS for a given action, belonging to a given doctype.
       @param doctype: the document type for which the functions are to be deleted
       @param action: the action that owns the functions to be deleted
       @return: 0 (ZERO) if all functions for the doctype/action are deleted successfully;
        1 (ONE) if functions for the doctype/action remain after the delete has been performed (i.e.
        the functions could not be deleted for some reason)
    """
    q = """DELETE FROM sbmFUNCTIONS WHERE doctype=%s AND action=%s"""
    run_sql(q, (doctype, action))
    numrows_functions_actiondoctype = get_number_functions_action_doctype(doctype=doctype, action=action)
    if numrows_functions_actiondoctype == 0:
        ## Everything OK - no functions remain for this doctype/action
        return 0
    else:
        ## Everything NOT OK - still some functions remaining for doctype/action
        ## make a last attempt to delete them:
        run_sql(q, (doctype, action))
        ## check once more to see if functions remain:
        if get_number_functions_action_doctype(doctype=doctype, action=action) == 0:
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
        q = """INSERT INTO sbmCATEGORIES (doctype, sname, lname, score) (SELECT %s, sname, lname, score """\
            """FROM sbmCATEGORIES WHERE doctype=%s)"""
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

def insert_function_into_submission_at_step_and_score_then_regulate_scores_of_functions_in_step(doctype, action,
                                                                                                function, step, score):
    """Insert a function into a submission at a particular score within a particular step, then regulate the scores
       of all functions within that step to spaces of 10.
       @param doctype: (string)
       @param action: (string)
       @param function: (string)
       @param step: (integer)
       @param score: (integer)
       @return: None
    """
    ## check whether function exists in WebSubmit DB:
    numrows_function = get_number_of_functions_with_funcname(funcname=function)
    if numrows_function < 1:
        msg = """Failed to insert the function [%s] into submission [%s] at step [%s] and score [%s] - """\
              """Could not find function [%s] in WebSubmit DB""" % (function, "%s%s" % (action, doctype),
                                                                    step, score, function)
        raise InvenioWebSubmitAdminWarningReferentialIntegrityViolation(msg)

    ## add 10 to the score of all functions at or below the position of this new function and within the same step
    ## (this ensures there is a vacant slot where the function is to be added)
    add_10_to_score_of_all_functions_in_step_of_submission_and_with_score_equalto_or_above_val(doctype=doctype,
                                                                                               action=action,
                                                                                               step=step,
                                                                                               fromscore=score)
    ## now insert the new function into its position:
    try:
        insert_function_into_submission_at_step_and_score(doctype=doctype, action=action,
                                                          function=function, step=step, score=score)
    except InvenioWebSubmitAdminWarningReferentialIntegrityViolation as e:
        ## The function doesn't exist in WebSubmit and therefore cannot be used in the submission
        ## regulate the scores of all functions within the step, to correct the "hole" that was made
        try:
            regulate_score_of_all_functions_in_step_to_ascending_multiples_of_10_for_submission(doctype=doctype,
                                                                                                action=action,
                                                                                                step=step)
        except InvenioWebSubmitAdminWarningDeleteFailed as f:
            ## can't regulate the functions' scores - couldn't delete some or all of them before re-inserting
            ## them in the correct position. Cannot fix this - report that some functions may have been lost.
            msg = """It wasn't possible to add the function [%s] to submission [%s] at step [%s], score [%s]."""\
                  """ Firstly, the function doesn't exist in WebSubmit. Secondly, when trying to correct the """\
                  """score of the functions within step [%s], it was not possible to delete some or all of them."""\
                  """ Some functions may have been lost - please check."""\
                  % (function, "%s%s" % (action, doctype), step, score, step)
            raise InvenioWebSubmitAdminWarningInsertFailed(msg)
        raise

    ## try to regulate the scores of the functions in the step that the new function was just inserted into:
    try:
        regulate_score_of_all_functions_in_step_to_ascending_multiples_of_10_for_submission(doctype=doctype,
                                                                                            action=action,
                                                                                            step=step)
    except InvenioWebSubmitAdminWarningDeleteFailed as e:
        ## could not correctly regulate the functions - could not delete all functions in the step
        msg = """Could not regulate the scores of all functions within step [%s] of submission [%s]."""\
              """ It was not possible to delete some or all of them. Some functions may have been lost -"""\
              """ please chack.""" % (step, "%s%s" % (action, doctype))
        raise InvenioWebSubmitAdminWarningDeleteFailed(msg)
    ## success
    return

def insert_function_into_submission_at_step_and_score(doctype, action, function, step, score):
    """Insert a function into a submission, at the position dictated by step/score.
       @param doctype: (string) the unique ID of a document type
       @param action: (string) the unique ID of an action
       @param function: (string) the unique name of a function
       @param step: (integer) the step into which the function should be inserted
       @param score: (integer) the score at which the function should be inserted
       @return:
    """
    ## check that the function exists in WebSubmit:
    numrows_function = get_number_of_functions_with_funcname(function)
    if numrows_function > 0:
        ## perform the insert
        q = """INSERT INTO sbmFUNCTIONS (doctype, action, function, step, score) VALUES(%s, %s, %s, %s, %s)"""
        run_sql(q, (doctype, action, function, step, score))
        return
    else:
        ## function doesnt exist - cannot insert a row for it in a submission!
        msg = """Failed to insert the function [%s] into submission [%s] at step [%s] and score [%s] - """\
              """Could not find function [%s] in WebSubmit DB""" % (function, "%s%s" % (action, doctype),
                                                                    step, score, function)
        raise InvenioWebSubmitAdminWarningReferentialIntegrityViolation(msg)

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

def delete_functionparameters_doctype_submission(doctype, action):
    def _get_list_params_to_delete(potential_delete_params, keep_params):
        del_params = []
        for param in potential_delete_params:
            if param[0] not in keep_params and param[0] != "":
                ## this parameter is not used by the other actions - it can be deleted
                del_params.append(param[0])
        return del_params

    ## get the parameters belonging to the given submission of the doctype:
    params_doctype_action = get_functionparameternames_doctype_action(doctype=doctype, action=action)
    ## get all parameters for the given doctype that belong to submissions OTHER than the submission for which we must
    ## delete parameters:
    params_doctype_other_actions = get_functionparameternames_doctype_not_action(doctype=doctype, action=action)
    ## "params_doctype_not_action" is a tuple of tuples, where each tuple contains only the parameter name: ((param,),(param,))
    ## make a tuple of strings, instead of this tuple of tuples:
    params_to_keep = map(lambda x: (type(x[0]) in (str, unicode) and x[0]) or (""), params_doctype_other_actions)
    delete_params = _get_list_params_to_delete(potential_delete_params=params_doctype_action, keep_params=params_to_keep)
    ## now, if there are parameters to delete, do it:
    if len(delete_params) > 0:
        q = """DELETE FROM sbmPARAMETERS WHERE doctype=%s AND (name=%s"""
        if len(delete_params) > 1:
            for i in range(1, len(delete_params)):
                q += """ OR name=%s"""
        q += """)"""
        run_sql(q, [doctype,] + delete_params)
        params_remaining_doctype_action = get_functionparameternames_doctype_action(doctype=doctype, action=action)
        if len(_get_list_params_to_delete(potential_delete_params=params_remaining_doctype_action, keep_params=params_to_keep)) == 0:
            ## Everything OK - all parameters deleted
            return 0
        else:
            ## Everything NOT OK - some parameters remain: try one final time to delete them
            run_sql(q, [doctype,] + delete_params)
            params_remaining_doctype_action = get_functionparameternames_doctype_action(doctype=doctype, action=action)
            if len(_get_list_params_to_delete(potential_delete_params=params_remaining_doctype_action, keep_params=params_to_keep)) > 0:
                ## Everything OK - deleted successfully this time
                return 0
            else:
                ## Still unable to delete - give up
                return 1
    ## no parameters to delete
    return 0

def update_value_of_function_parameter_for_doctype(doctype, paramname, paramval):
    """Update the value of a parameter as used by a document type.
       @param doctype: (string) the unique ID of a document type
       @param paramname: (string) the name of the parameter whose value is to be updated
       @param paramval: (string) the new value for the parameter
       @Exceptions raised:
           InvenioWebSubmitAdminTooManyRows - when multiple rows found for parameter
           InvenioWebSubmitAdminNoRowsFound - when no rows found for parameter
    """
    q = """UPDATE sbmPARAMETERS SET value=%s WHERE doctype=%s AND name=%s"""
    ## get number of rows found for the parameter:
    numrows_param = get_numberparams_doctype_paramname(doctype=doctype, paramname=paramname)
    if numrows_param == 1:
        run_sql(q, (paramval, doctype, paramname))
        return
    elif numrows_param > 1:
        ## multiple rows found for the parameter - not safe to edit
        msg = """When trying to update the [%s] parameter for the [%s] document type, [%s] rows were found for the parameter """\
              """- not safe to update""" % (paramname, doctype, numrows_param)
        raise InvenioWebSubmitAdminWarningTooManyRows(msg)
    else:
        ## no row for parameter found
        insert_parameter_doctype(doctype=doctype, paramname=paramname, paramval=paramval)
        numrows_param = get_numberparams_doctype_paramname(doctype=doctype, paramname=paramname)
        if numrows_param != 1:
            msg = """When trying to update the [%s] parameter for the [%s] document type, could not insert a new value"""\
                  % (paramname, doctype)
            raise InvenioWebSubmitAdminWarningNoRowsFound(msg)
        return

def get_parameters_name_and_value_for_function_of_doctype(doctype, function):
    """Get the names and values of all parameters of a given function, as they have been set for a particular document
       type.
       @param doctype: (string) the unique ID of a document type
       @param function: the name of the function from which the parameters names/values are to be retrieved
       @return: a tuple of 2-celled tuples, each tuple containing 2 strings: (parameter-name, parameter-value)
    """
    q = """SELECT param.name, param.value FROM sbmPARAMETERS AS param """\
        """LEFT JOIN sbmFUNDESC AS func ON func.param=param.name """\
        """WHERE func.function=%s AND param.doctype=%s """\
        """ORDER BY param.name ASC"""
    return run_sql(q, (function, doctype))

def get_value_of_parameter_for_doctype(doctype, parameter):
    q = """SELECT value FROM sbmPARAMETERS WHERE doctype=%s AND name=%s"""
    res = run_sql(q, (doctype, parameter))
    if len(res) > 0:
        return res[0][0]
    else:
        return None

def get_functionparameternames_doctype_action(doctype, action):
    """Get the unique NAMES function parameters for a given action of a given doctype.
       @param doctype: the document type with which the parameters are associated
       @param action: the action (of "doctype") with which the parameters are associated
       @return: a tuple of tuples, where each tuple represents a parameter name:
        (parameter name, parameter value, doctype)
    """
    q = """SELECT DISTINCT(par.name) FROM sbmFUNDESC AS fundesc """ \
           """LEFT JOIN sbmPARAMETERS AS par ON fundesc.param = par.name """ \
           """LEFT JOIN sbmFUNCTIONS AS func ON par.doctype = func.doctype AND fundesc.function = func.function """ \
           """WHERE par.doctype=%s AND func.action=%s """\
           """GROUP BY par.name """ \
           """ORDER BY fundesc.function ASC, par.name ASC"""
    return run_sql(q, (doctype, action))

def get_functionparameternames_doctype_not_action(doctype, action):
    """Get the unique NAMES function parameters for a given action of a given doctype.
       @param doctype: the document type with which the parameters are associated
       @param action: the action (of "doctype") with which the parameters are associated
       @return: a tuple of tuples, where each tuple represents a parameter name:
        (parameter name, parameter value, doctype)
    """
    q = """SELECT DISTINCT(par.name) FROM sbmFUNDESC AS fundesc """ \
           """LEFT JOIN sbmPARAMETERS AS par ON fundesc.param = par.name """ \
           """LEFT JOIN sbmFUNCTIONS AS func ON par.doctype = func.doctype AND fundesc.function = func.function """ \
           """WHERE par.doctype=%s AND func.action <> %s """\
           """GROUP BY par.name """ \
           """ORDER BY fundesc.function ASC, par.name ASC"""
    return run_sql(q, (doctype, action))

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

def insert_category_into_doctype(doctype, categ, categdescr):
    """Insert a category for a document type. It will be inserted into the last position.
       If the category already exists for that document type, the insert will fail.
       @param doctype:    (string) - the document type ID.
       @param categ:      (string) - the ID of the new category.
       @param categdescr: (string) - the new category's description.
       @return: (integer) An error code: 0 on successful insert; 1 on failure to insert.
    """
    qstr = """INSERT INTO sbmCATEGORIES (doctype, sname, lname, score) """\
           """(SELECT %s, %s, %s, COUNT(sname)+1 FROM sbmCATEGORIES WHERE doctype=%s)"""
    ## does this category already exist for this document type?
    numrows_categ = get_number_categories_doctype_category(doctype=doctype, categ=categ)
    if numrows_categ == 0:
        ## it doesn't exist for this doctype - go ahead and insert it:
        run_sql(qstr, (doctype, categ, categdescr, doctype))
        return 0
    else:
        ## the category already existed for this doctype - cannot insert
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
        ## now re-order all category scores correctly:
        normalize_doctype_category_scores(doctype)
        return 0
    else:
        ## Everything NOT OK - category still present
        ## make a last attempt to delete it:
        run_sql(q, (doctype, categ))
        ## check once more to see if category remains:
        if get_number_categories_doctype_category(doctype=doctype, categ=categ) == 0:
            ## Everything OK - category was deleted successfully this time
            ## now re-order all category scores correctly:
            normalize_doctype_category_scores(doctype)
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

def get_cd_md_numbersubmissionpages_doctype_action(doctype, action):
    """Return the creation date (cd), the modification date (md), and the number of submission pages
       for a given submission (action) of a given  document type (doctype).
       @param doctype: the document type for which the number of pages of a given submission is to be
        determined.
       @param action: the submission (action) for which the number of pages is to be determined.
       @return: a tuple of tuples, where each tuple contains the creation date, the modification date, and
        the number of pages for the given submission: ((cd, md, nbpg), (cd, md, nbpg)[,...])
    """
    q = """SELECT cd, md, nbpg FROM sbmIMPLEMENT WHERE docname=%s AND actname=%s LIMIT 1"""
    return run_sql(q, (doctype, action))

def get_numbersubmissionpages_doctype_action(doctype, action):
    """Return the number of submission pages belonging to a given submission (action) of a document type
       (doctype) as an integer. In the case that the submission does not exist, 0 (ZERO) will be returned.
       In the case that an error occurs, -1 will be returned.
       @param doctype: (string) the unique ID of a document type.
       @param action: (string) the unique name/ID of an action.
       @return: an integer - the number of pages found for the submission
    """
    q = """SELECT nbpg FROM sbmIMPLEMENT WHERE docname=%s AND actname=%s LIMIT 1"""
    res = run_sql(q, (doctype, action))
    if len(res) > 0:
        try:
            return int(res[0][0])
        except (IndexError, ValueError):
            ## unexpected result
            return -1
    else:
        return 0

def get_numberfields_submissionpage_doctype_action(doctype, action, pagenum):
    """Return the number of fields on a given page of a given submission.
       @param doctype: (string) the unique ID of the document type to which the submission belongs
       @param action: (string) the unique name/ID of the action
       @param pagenum: (integer) the number of the page on which fields are to be counted
       @return: (integer) the number of fields found on the page
    """
    q = """SELECT COUNT(subname) FROM sbmFIELD WHERE pagenb=%s AND subname=%s"""
    return int(run_sql(q, (pagenum, """%s%s""" % (action, doctype)))[0][0])

def get_number_of_fields_on_submissionpage_at_positionx(doctype, action, pagenum, positionx):
    """Return the number of fields at positionx on a given page of a given submission.
       @param doctype: (string) the unique ID of the document type to which the submission belongs
       @param action: (string) the unique name/ID of the action
       @param pagenum: (integer) the number of the page on which fields are to be counted
       @return: (integer) the number of fields found on the page
    """
    q = """SELECT COUNT(subname) FROM sbmFIELD WHERE pagenb=%s AND subname=%s AND fieldnb=%s"""
    return int(run_sql(q, (pagenum, """%s%s""" % (action, doctype), positionx))[0][0])

def swap_elements_adjacent_pages_doctype_action(doctype, action, page1, page2):
    ## get number pages belonging to submission:
    num_pages = get_numbersubmissionpages_doctype_action(doctype=doctype, action=action)
    tmp_page = num_pages + randint(3,10)
    if page1 - page2 not in (1, -1):
        ## pages are not adjacent - cannot swap
        return 1
    if page1 > num_pages or page2 > num_pages or page1 < 1 or page2 < 1:
        ## atl least one page is out of range of legal pages:
        return 2

    q = """UPDATE sbmFIELD SET pagenb=%s WHERE subname=%s AND pagenb=%s"""

    ## move fields from p1 to tmp
    run_sql(q, (tmp_page, "%s%s" % (action, doctype), page1))
    num_fields_p1 = get_numberfields_submissionpage_doctype_action(doctype=doctype, action=action, pagenum=page1)
    if num_fields_p1 != 0:
        ## problem moving some fields from page 1 - move them back from tmp
        run_sql(q, (page1, "%s%s" % (action, doctype), tmp_page))
        return 3
    ## move fields from p2 to p1
    run_sql(q, (page1, "%s%s" % (action, doctype), page2))
    num_fields_p2 = get_numberfields_submissionpage_doctype_action(doctype=doctype, action=action, pagenum=page2)
    if num_fields_p2 != 0:
        ## problem moving some fields from page 2 to page 1 - try to move everything back
        run_sql(q, (page2, "%s%s" % (action, doctype), page1))
        run_sql(q, (page1, "%s%s" % (action, doctype), tmp_page))
        return 4
    ## move fields from tmp_page to page2:
    run_sql(q, (page2, "%s%s" % (action, doctype), tmp_page))
    num_fields_tmp_page = get_numberfields_submissionpage_doctype_action(doctype=doctype, action=action, pagenum=tmp_page)
    if num_fields_tmp_page != 0:
        ## problem moving some fields from tmp_page to page 2
        ## stop - this problem should be examined by admin
        return 5
    ## success - update modification date for all fields on the swapped pages
    update_modificationdate_fields_submissionpage(doctype=doctype, action=action, subpage=page1)
    update_modificationdate_fields_submissionpage(doctype=doctype, action=action, subpage=page2)
    return 0

def update_modificationdate_fields_submissionpage(doctype, action, subpage):
    q = """UPDATE sbmFIELD SET md=CURDATE() WHERE subname=%s AND pagenb=%s"""
    run_sql(q, ("%s%s" % (action, doctype), subpage))
    return 0

def update_modificationdate_of_field_on_submissionpage(doctype, action, subpage, fieldnb):
    q = """UPDATE sbmFIELD SET md=CURDATE() WHERE subname=%s AND pagenb=%s AND fieldnb=%s"""
    run_sql(q, ("%s%s" % (action, doctype), subpage, fieldnb))
    return 0

def decrement_by_one_pagenumber_submissionelements_abovepage(doctype, action, frompage):
    q = """UPDATE sbmFIELD SET pagenb=pagenb-1, md=CURDATE() WHERE subname=%s AND pagenb > %s"""
    run_sql(q, ("%s%s" % (action, doctype), frompage))
    return 0

def get_details_and_description_of_all_fields_on_submissionpage(doctype, action, pagenum):
    """Get the details and descriptions of all fields on a given submission page, ordered by ascending field number.
       @param doctype: (string) the unique ID of a document type
       @param action: (string) the unique ID of an action
       @param pagenum: (integer) the number of the page on which the fields to be displayed are found
       @return: a tuple of tuples. Each tuple represents one field on the page.
        (fieldname, field-label, check-name, field-type, size, rows, cols, field-description, field-default-value)
    """
    q = """SELECT field.fidesc, field.fitext, field.checkn, el.type, el.size, el.rows, el.cols, el.fidesc, IFNULL(el.val,"") """\
        """FROM sbmFIELD AS field """\
        """LEFT JOIN sbmFIELDDESC AS el ON el.name=field.fidesc """\
        """WHERE field.subname=%s AND field.pagenb=%s """\
        """ORDER BY field.fieldnb ASC"""
    res = run_sql(q, ("%s%s" % (action, doctype), pagenum))
    return res

def insert_field_onto_submissionpage(doctype, action, pagenum, fieldname, fieldtext, fieldlevel, fieldshortdesc, fieldcheck):
    """Insert a field onto a given submission page, in the last position.
       @param doctype: (string) the unique ID of a document type
       @param action: (string) the unique ID of an action
       @param pagenum: (integer) the number of the page onto which the field is to be added
       @param fieldname: (string) the "element name" of the field to be added to the page
       @param fieldtext: (string) the label to be displayed for the fieldon a submission page
       @param fieldlevel: (char) the level of a field ('M' or 'O') - Mandatory or Optional
       @param fieldshortdesc: (string) the short description for a field
       @param fieldcheck: (string) the name of a check to be associated with a field
       @return: None
       @Exceptions raised:
            InvenioWebSubmitAdminWarningInsertFailed - raised if it was not possible to insert the row for the field
    """
    ## get the number of fields on the page onto which the new field is to be inserted:
    numfields_preinsert = get_numberfields_submissionpage_doctype_action(doctype=doctype, action=action, pagenum=pagenum)
    q = """INSERT INTO sbmFIELD (subname, pagenb, fieldnb, fidesc, fitext, level, sdesc, checkn, cd, md, """ \
        """fiefi1, fiefi2) """\
        """(SELECT %s, %s, COUNT(subname)+1, %s, %s, %s, %s, %s, CURDATE(), CURDATE(), NULL, NULL FROM sbmFIELD """ \
        """WHERE subname=%s AND pagenb=%s)"""
    run_sql(q, ("%s%s" % (action, doctype), pagenum, fieldname, fieldtext,
                fieldlevel, fieldshortdesc, fieldcheck, "%s%s" % (action, doctype), pagenum))
    numfields_postinsert = get_numberfields_submissionpage_doctype_action(doctype=doctype, action=action, pagenum=pagenum)
    if not (numfields_postinsert > numfields_preinsert):
        ## seems as though the new field was not inserted:
        msg = """Failed when trying to add a new field to page %s of submission %s""" % (pagenum, "%s%s" % (action, doctype))
        raise InvenioWebSubmitAdminWarningInsertFailed(msg)
    return

def delete_a_field_from_submissionpage(doctype, action, pagenum, fieldposn):
    q = """DELETE FROM sbmFIELD WHERE subname=%s AND pagenb=%s AND fieldnb=%s"""
    run_sql(q, ("""%s%s""" % (action, doctype), pagenum, fieldposn))
    ## check number of fields at deleted field's position. If 0, promote all fields below it by 1 posn;
    ## If field(s) still exists at deleted field's posn, report error.
    numfields_deletedfieldposn = \
        get_number_of_fields_on_submissionpage_at_positionx(doctype=doctype, action=action, pagenum=pagenum, positionx=fieldposn)

    if numfields_deletedfieldposn == 0:
        ## everything OK - field was successfully deleted
        return 0
    else:
        ## everything NOT OK - couldn't delete field - retry
        run_sql(q, ("""%s%s""" % (action, doctype), pagenum, fieldposn))
        numfields_deletedfieldposn = \
            get_number_of_fields_on_submissionpage_at_positionx(doctype=doctype, action=action, pagenum=pagenum, positionx=fieldposn)
        if numfields_deletedfieldposn == 0:
            ## success this time
            return 0
        else:
            ## still unable to delete all fields - return fail code
            return 1

def update_details_of_a_field_on_a_submissionpage(doctype, action, pagenum, fieldposn,
                                                  fieldtext, fieldlevel, fieldshortdesc, fieldcheck):
    """Update the details of one field, as found at a given location on a given submission page.
       @param doctype: (string) unique ID for a document type
       @param action: (string) unique ID for an action
       @param pagenum: (integer) number of page on which field is found
       @param fieldposn: (integer) number of field on page
       @param fieldtext: (string) text label for field on page
       @param fieldlevel: (char) level of field (should be 'M' or 'O' - mandatory or optional)
       @param fieldshortdesc: (string) short description of field
       @param fieldcheck: (string) name of JavaScript Check to be applied to field
       @return: None
       @Exceptions raised:
           InvenioWebSubmitAdminWarningTooManyRows - when multiple rows found for field
           InvenioWebSubmitAdminWarningNoRowsFound - when no rows found for field
    """
    q = """UPDATE sbmFIELD SET fitext=%s, level=%s, sdesc=%s, checkn=%s, md=CURDATE() WHERE subname=%s AND pagenb=%s AND fieldnb=%s"""
    queryargs = (fieldtext, fieldlevel, fieldshortdesc, fieldcheck, "%s%s" % (action, doctype), pagenum, fieldposn)
    ## get number of rows found for field:
    numrows_field = get_number_of_fields_on_submissionpage_at_positionx(doctype=doctype, action=action,
                                                                        pagenum=pagenum, positionx=fieldposn)
    if numrows_field == 1:
        run_sql(q, queryargs)
        return
    elif numrows_field > 1:
        ## multiple rows found for the field at this position - not safe to edit
        msg = """When trying to update the field in position %s on page %s of the submission %s, %s rows were found for the field""" \
              % (fieldposn, pagenum, "%s%s" % (action, doctype), numrows_field)
        raise InvenioWebSubmitAdminWarningTooManyRows(msg)
    else:
        ## no row for field found
        msg = """When trying to update the field in position %s on page %s of the submission %s, no rows were found for the field""" \
              % (fieldposn, pagenum, "%s%s" % (action, doctype))
        raise InvenioWebSubmitAdminWarningNoRowsFound(msg)

def delete_a_field_from_submissionpage_then_reorder_fields_below_to_fill_vacant_position(doctype,
                                                                                         action,
                                                                                         pagenum,
                                                                                         fieldposn):
    """Delete a submission field from a given page of a given document-type submission.
       E.g. Delete the field in position 3, from page 2 of the "SBI" submission of the
       "TEST" document-type.
       @param doctype: (string) the unique ID of the document type
       @param action: (string) the unique name/ID of the submission/action
       @param pagenum: (integer) the number of the page from which the field is to be
        deleted
       @param fieldposn: (integer) the number of the field to be deleted (e.g. field at position
        number 1, or number 2, etc.)
       @return: An integer number containing the number of rows deleted; -OR-
        An error string in the event that something goes wrong.
    """
    delete_res = delete_a_field_from_submissionpage(doctype=doctype, action=action, pagenum=pagenum, fieldposn=fieldposn)
    if delete_res == 0:
        ## deletion was successful - demote fields below deleted field into gap:
        update_res = decrement_position_of_all_fields_atposition_greaterthan_positionx_on_submissionpage(doctype=doctype,
                                                                                                         action=action,
                                                                                                         pagenum=pagenum,
                                                                                                         positionx=fieldposn,
                                                                                                         decrement=1)
        ## update the modification date of the page:
        update_modification_date_for_submission(doctype=doctype, action=action)
        return 0
    else:
        ## could not delete field! return an appropriate error message
        return delete_res

def update_modification_date_for_submission(doctype, action):
    """Update the "last-modification" date for a submission to the current date (today).
       @param doctype: (string) the unique ID of a document type
       @param action: (string) the unique ID of an action
       @return: None
    """
    q = """UPDATE sbmIMPLEMENT SET md=CURDATE() WHERE docname=%s AND actname=%s"""
    run_sql(q, (doctype, action))
    return

def move_field_on_submissionpage_from_positionx_to_positiony(doctype, action, pagenum, movefieldfrom, movefieldto):
    ## get number of fields on submission page:
    try:
        movefieldfrom = int(movefieldfrom)
        movefieldto = int(movefieldto)
    except ValueError:
        return 1
        #return 'WRN_WEBSUBMITADMIN_INVALID_FIELD_NUMBERS_SUPPLIED_WHEN_TRYING_TO_MOVE_FIELD_ON_SUBMISSION_PAGE'
    numfields_page = get_numberfields_submissionpage_doctype_action(doctype=doctype, action=action, pagenum=pagenum)

    if movefieldfrom > numfields_page or movefieldto > numfields_page or movefieldfrom < 1 or \
           movefieldto < 1 or movefieldfrom == movefieldto:
        ## invalid move-field coordinates:
        return 1
        #return 'WRN_WEBSUBMITADMIN_INVALID_FIELD_NUMBERS_SUPPLIED_WHEN_TRYING_TO_MOVE_FIELD_ON_SUBMISSION_PAGE'

    q = """UPDATE sbmFIELD SET fieldnb=%s WHERE subname=%s AND pagenb=%s AND fieldnb=%s"""
    ## process movement:
    if movefieldfrom - movefieldto in (1, -1):
        ## fields are adjacent - swap them around:
        tmp_fieldnb = numfields_page + randint(3,10)

        ## move field from position 'movefieldfrom' to tempoary position 'tmp_fieldnb':
        run_sql(q, (tmp_fieldnb, "%s%s" % (action, doctype), pagenum, movefieldfrom))
        num_fields_posn_movefieldfrom = \
              get_number_of_fields_on_submissionpage_at_positionx(doctype=doctype, action=action, pagenum=pagenum, positionx=movefieldfrom)

        if num_fields_posn_movefieldfrom != 0:
            ## problem moving the field from its position to the temporary position
            ## try to move it back, and return with an error
            return 2
            #return 'WRN_WEBSUBMITADMIN_UNABLE_TO_SWAP_TWO_FIELDS_ON_SUBMISSION_PAGE_COULDNT_MOVE_FIELD1_TO_TEMP_POSITION'

        ## move field from position 'movefieldto' to position 'movefieldfrom':
        run_sql(q, (movefieldfrom, "%s%s" % (action, doctype), pagenum, movefieldto))
        num_fields_posn_movefieldto = \
              get_number_of_fields_on_submissionpage_at_positionx(doctype=doctype, action=action, pagenum=pagenum, positionx=movefieldto)
        if num_fields_posn_movefieldto != 0:
            ## problem moving the field at 'movefieldto' into the position 'movefieldfrom'
            ## try to reverse the changes made so far, then return with an error:

            ## move field at temporary posn back to 'movefieldfrom' position:
            run_sql(q, (movefieldfrom, "%s%s" % (action, doctype), pagenum, tmp_fieldnb))
            return 3
            #return 'WRN_WEBSUBMITADMIN_UNABLE_TO_SWAP_TWO_FIELDS_ON_SUBMISSION_PAGE_COULDNT_MOVE_FIELD2_TO_FIELD1_POSITION'

        ## move field from temporary position 'tmp_fieldnb' to position 'movefieldto':
        run_sql(q, (movefieldto, "%s%s" % (action, doctype), pagenum, tmp_fieldnb))
        num_fields_posn_tmp_fieldnb = \
              get_number_of_fields_on_submissionpage_at_positionx(doctype=doctype, action=action, pagenum=pagenum, positionx=tmp_fieldnb)
        if num_fields_posn_tmp_fieldnb != 0:
            ## problem moving the field from the temporary position to position 'movefieldto'
            ## stop - admin should examine and fix this problem
            return 4
            #return 'WRN_WEBSUBMITADMIN_UNABLE_TO_SWAP_TWO_FIELDS_ON_SUBMISSION_PAGE_COULDNT_MOVE_FIELD1_TO_POSITION_FIELD2_FROM_TEMPORARY_POSITION'
        ## successfully swapped fields - update modification date of the swapped fields and of the submission
        update_modificationdate_of_field_on_submissionpage(doctype=doctype, action=action, subpage=pagenum, fieldnb=movefieldfrom)
        update_modificationdate_of_field_on_submissionpage(doctype=doctype, action=action, subpage=pagenum, fieldnb=movefieldto)
        update_modification_date_for_submission(doctype=doctype, action=action)
        return 0
    else:
        ## fields not adjacent - perform a move:
        tmp_fieldnb = 0 - randint(3,10)

        ## move field from position 'movefieldfrom' to tempoary position 'tmp_fieldnb':
        run_sql(q, (tmp_fieldnb, "%s%s" % (action, doctype), pagenum, movefieldfrom))
        num_fields_posn_movefieldfrom = \
              get_number_of_fields_on_submissionpage_at_positionx(doctype=doctype, action=action, pagenum=pagenum, positionx=movefieldfrom)

        if num_fields_posn_movefieldfrom != 0:
            ## problem moving the field from its position to the temporary position
            ## try to move it back, and return with an error
            return 2
            #return 'WRN_WEBSUBMITADMIN_UNABLE_TO_SWAP_TWO_FIELDS_ON_SUBMISSION_PAGE_COULDNT_MOVE_FIELD1_TO_TEMP_POSITION'

        ## fill the gap created by the moved field by decrementing by one the position of all fields below it:
        qres = decrement_position_of_all_fields_atposition_greaterthan_positionx_on_submissionpage(doctype=doctype, action=action,
                                                                                                   pagenum=pagenum, positionx=movefieldfrom,
                                                                                                   decrement=1)
        if movefieldfrom < numfields_page:
            ## check that there is now a field in the position of "movefieldfrom":
            num_fields_posn_movefieldfrom = \
              get_number_of_fields_on_submissionpage_at_positionx(doctype=doctype, action=action, pagenum=pagenum, positionx=movefieldfrom)
            if num_fields_posn_movefieldfrom == 0:
                ## no field there - it was not possible to decrement the field position of all fields below the field moved 'tmp_fieldnb'
                ## try to move the field back from 'tmp_fieldnb'
                run_sql(q, (movefieldfrom, "%s%s" % (action, doctype), pagenum, tmp_fieldnb))
                ## return an ERROR message
                return 5
                #return 'WRN_WEBSUBMITADMIN_UNABLE_TO_MOVE_FIELD_TO_NEW_POSITION_ON_SUBMISSION_PAGE_COULDNT_DECREMENT_POSITION_OF_FIELDS_BELOW_FIELD1'

        ## now increment (by one) the position of the fields at and below the field at position 'movefieldto':
        qres = increment_position_of_all_fields_atposition_greaterthan_positionx_on_submissionpage(doctype=doctype, action=action,
                                                                                                   pagenum=pagenum, positionx=movefieldto-1,
                                                                                                   increment=1)
        ## there should now be an empty space at position 'movefieldto':
        num_fields_posn_movefieldto = \
          get_number_of_fields_on_submissionpage_at_positionx(doctype=doctype, action=action, pagenum=pagenum, positionx=movefieldto)
        if num_fields_posn_movefieldto != 0:
            ## there isn't! the increment of position has failed - return warning:
            return 6
            #return 'WRN_WEBSUBMITADMIN_UNABLE_TO_MOVE_FIELD_TO_NEW_POSITION_ON_SUBMISSION_PAGE_COULDNT_INCREMENT_POSITION_OF_FIELDS_AT_AND_BELOW_FIELD2'

        ## Move field from temporary position to position 'movefieldto':
        run_sql(q, (movefieldto, "%s%s" % (action, doctype), pagenum, tmp_fieldnb))
        num_fields_posn_movefieldto = \
          get_number_of_fields_on_submissionpage_at_positionx(doctype=doctype, action=action, pagenum=pagenum, positionx=movefieldto)
        if num_fields_posn_movefieldto == 0:
            ## failed to move field1 from temp posn to final posn
            return 4
            #return 'WRN_WEBSUBMITADMIN_UNABLE_TO_SWAP_TWO_FIELDS_ON_SUBMISSION_PAGE_COULDNT_MOVE_FIELD1_TO_POSITION_FIELD2_FROM_TEMPORARY_POSITION'

        ## successfully moved field - update modification date of the moved field and of the submission
        update_modificationdate_of_field_on_submissionpage(doctype=doctype, action=action, subpage=pagenum, fieldnb=movefieldfrom)
        update_modification_date_for_submission(doctype=doctype, action=action)
        return 0

def increment_position_of_all_fields_atposition_greaterthan_positionx_on_submissionpage(doctype, action, pagenum, positionx, increment=1):
    """Increment (by the number provided via the "increment" parameter) the position of all fields (on a given submission page)
       found at a position greater than that of positionx
       @param doctype:   (string)  the unique ID of a document type
       @param action:    (string)  the unique name/ID of the action
       @param pagenum:   (integer) the number of the submission page on which the fields are situated
       @param positionx: (integer) the position after which fields' positions are to be promoted
       @param increment: (integer) the number by which to increment the field positions (defaults to 1)
       @return:
    """
    if type(increment) is not int:
        increment = 1
    q = """UPDATE sbmFIELD SET fieldnb=fieldnb+%s WHERE subname=%s AND pagenb=%s AND fieldnb > %s"""
    res = run_sql(q, (increment, "%s%s" % (action, doctype), pagenum, positionx))
    try:
        return int(res)
    except ValueError:
        return None

def decrement_position_of_all_fields_atposition_greaterthan_positionx_on_submissionpage(doctype, action, pagenum, positionx, decrement=1):
    """Decrement (by the number provided via the "decrement" parameter) the position of all fields (on a given submission page)
       found at a position greater than that of positionx
       @param doctype:   (string)  the unique ID of a document type
       @param action:    (string)  the unique name/ID of the action
       @param pagenum:   (integer) the number of the submission page on which the fields are situated
       @param positionx: (integer) the position after which fields' positions are to be promoted
       @param decrement: (integer) the number by which to increment the field positions (defaults to 1)
       @return:
    """
    if type(decrement) is not int:
        decrement = 1
    q = """UPDATE sbmFIELD SET fieldnb=fieldnb-%s WHERE subname=%s AND pagenb=%s AND fieldnb > %s"""
    res = run_sql(q, (decrement, "%s%s" % (action, doctype), pagenum, positionx))
    try:
        return int(res)
    except ValueError:
        return None

def delete_allfields_submissionpage_doctype_action(doctype, action, pagenum):
    q = """DELETE FROM sbmFIELD WHERE pagenb=%s AND subname=%s"""
    run_sql(q, (pagenum, """%s%s""" % (action, doctype)))
    numrows_fields = get_numberfields_submissionpage_doctype_action(doctype=doctype,
                                                                        action=action, pagenum=pagenum)
    if numrows_fields == 0:
        ## everything OK - all fields deleted
        return 0
    else:
        ## everything NOT OK - couldn't delete all fields for page
        ## retry
        run_sql(q, (pagenum, doctype, action))
        numrows_fields = get_numberfields_submissionpage_doctype_action(doctype=doctype,
                                                                            action=action, pagenum=pagenum)
        if numrows_fields == 0:
            ## success this time
            return 0
        else:
            ## still unable to delete all fields - return fail code
            return 1

def get_details_allsubmissionfields_on_submission_page(doctype, action, pagenum):
    """Get the details of all submission elements belonging to a particular page of the submission.
       Results are returned ordered by field number.
       @param doctype: (string) the unique ID of a document type
       @param action: (string) the unique name/ID of an action
       @param pagenum: (string/integer): the integer number of the page for which element details are
        to be retrieved
       @return: a tuple of tuples: (subname, fieldnb, fidesc, fitext, level, sdesc, checkn, cd, md). Each
        tuple contains the details of one element.
    """
    q = """SELECT subname, fieldnb, fidesc, fitext, level, sdesc, checkn, cd, md FROM sbmFIELD """\
        """WHERE subname=%s AND pagenb=%s ORDER BY fieldnb ASC"""
    return run_sql(q, ("%s%s" % (action, doctype), pagenum))

def get_details_of_field_at_positionx_on_submissionpage(doctype, action, pagenum, fieldposition):
    """Get the details of a particular field in a submission page.
       @param doctype: (string) the unique ID of a document type
       @param action: (string) the unique name/ID of an action
       @param pagenum: (integer) the number of the submission page on which the field is found
       @param fieldposition: (integer) the position on the submission page of the field for which details
        are to be retrieved.
       @return: a tuple of the field's details: (subname, fieldnb, fidesc, fitext, level, sdesc, checkn, cd, md). Each
        tuple contains the details of one element.
    """
    fielddets = []
    q = """SELECT subname, fieldnb, fidesc, fitext, level, sdesc, checkn, cd, md FROM sbmFIELD """\
        """WHERE subname=%s AND pagenb=%s AND fieldnb=%s LIMIT 1"""
    res = run_sql(q, ("%s%s" % (action, doctype), pagenum, fieldposition))
    if len(res) > 0:
        fielddets = res[0]
    return fielddets

def decrement_by_one_number_submissionpages_doctype_action(doctype, action):
    numrows_submission = get_number_submissions_doctype_action(doctype, action)
    if numrows_submission == 1:
        ## there is only one row for this submission - can update
        q = """UPDATE sbmIMPLEMENT SET nbpg=IFNULL(nbpg, 1)-1, md=CURDATE() WHERE docname=%s AND actname=%s and IFNULL(nbpg, 1) > 0"""
        run_sql(q, (doctype, action))
        return 0 ## Everything OK
    else:
        ## Everything NOT OK - either multiple rows exist for submission, or submission doesn't exist
        return 1

def add_submission_page_doctype_action(doctype, action):
    """Increment the number of pages associated with a given submission by 1
       @param doctype: the unique ID of the document type that owns the submission.
       @param action: the action name/ID of the given submission of the document type, for which the number
        of pages is to be incremented.
       @return: an integer error code. 0 (ZERO) means that the update was performed without error; 1 (ONE) means
        that there was a problem and the update could not be performed. Problems could be: multiple rows found for
        the submission; no rows found for the submission.
    """
    numrows_submission = get_number_submissions_doctype_action(doctype, action)
    if numrows_submission == 1:
        ## there is only one row for this submission - can update
        q = """UPDATE sbmIMPLEMENT SET nbpg=IFNULL(nbpg, 0)+1, md=CURDATE() WHERE docname=%s AND actname=%s"""
        run_sql(q, (doctype, action))
        return 0 ## Everything OK
    else:
        ## Everything NOT OK - either multiple rows exist for submission, or submission doesn't exist
        return 1
