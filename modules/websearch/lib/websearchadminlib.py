## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

# pylint: disable=C0301

"""Invenio WebSearch Administrator Interface."""

__revision__ = "$Id$"

import cgi
import random
import time
import sys
from invenio.dateutils import strftime
import os
import traceback

if sys.hexversion < 0x2040000:
    # pylint: disable=W0622
    from sets import Set as set
    # pylint: enable=W0622

from invenio.config import \
     CFG_CACHEDIR, \
     CFG_SITE_LANG, \
     CFG_SITE_NAME, \
     CFG_SITE_URL,\
     CFG_WEBCOMMENT_ALLOW_COMMENTS, \
     CFG_WEBSEARCH_SHOW_COMMENT_COUNT, \
     CFG_WEBCOMMENT_ALLOW_REVIEWS, \
     CFG_WEBSEARCH_SHOW_REVIEW_COUNT, \
     CFG_BIBRANK_SHOW_CITATION_LINKS, \
     CFG_INSPIRE_SITE, \
     CFG_CERN_SITE
from invenio.bibrankadminlib import \
     write_outcome, \
     modify_translations, \
     get_def_name, \
     get_name, \
     get_languages, \
     addadminbox, \
     tupletotable, \
     createhiddenform
from invenio.dbquery import \
     run_sql, \
     get_table_update_time
from invenio.websearch_external_collections import \
     external_collections_dictionary, \
     external_collection_sort_engine_by_name, \
     external_collection_get_state, \
     external_collection_get_update_state_list, \
     external_collection_apply_changes
from invenio.websearch_external_collections_utils import \
     get_collection_descendants
from invenio.websearch_external_collections_config import CFG_EXTERNAL_COLLECTION_STATES_NAME
#from invenio.bibformat_elements import bfe_references
#from invenio.bibformat_engine import BibFormatObject
from invenio.bibdocfile import BibRecDocs
from invenio.messages import gettext_set_language
#from invenio.bibrank_citation_searcher import get_cited_by
from invenio.access_control_admin import acc_get_action_id
from invenio.access_control_config import VIEWRESTRCOLL
from invenio.errorlib import register_exception
from invenio.intbitset import intbitset
from invenio.bibrank_citation_searcher import get_cited_by, get_cited_by_count
from invenio.bibrecord import record_get_field_instances

def getnavtrail(previous = ''):
    """Get the navtrail"""

    navtrail = """<a class="navtrail" href="%s/help/admin">Admin Area</a> """ % (CFG_SITE_URL,)
    navtrail = navtrail + previous
    return navtrail

def fix_collection_scores():
    """
    Re-calculate and re-normalize de scores of the collection relationship.
    """
    for id_dad in intbitset(run_sql("SELECT id_dad FROM collection_collection")):
        for index, id_son in enumerate(run_sql("SELECT id_son FROM collection_collection WHERE id_dad=%s ORDER BY score DESC", (id_dad, ))):
            run_sql("UPDATE collection_collection SET score=%s WHERE id_dad=%s AND id_son=%s", (index * 10 + 10, id_dad, id_son[0]))

def perform_modifytranslations(colID, ln, sel_type='', trans=[], confirm=-1, callback='yes'):
    """Modify the translations of a collection
    sel_type - the nametype to modify
    trans - the translations in the same order as the languages from get_languages()"""
    output = ''
    subtitle = ''
    sitelangs = get_languages()
    if sel_type in ('r', 'v', 'l'):
        table = 'collectionbox'
        identifier_column = "id_collection"
    else:
        table = 'collection'
        identifier_column = None
    if type(trans) is str:
        trans = [trans]
    if confirm in ["2", 2] and colID:
        finresult = modify_translations(colID, sitelangs, sel_type, trans, table, identifier_column)
    col_dict = dict(get_def_name('', "collection"))

    if colID and col_dict.has_key(int(colID)):
        colID = int(colID)
        subtitle = """<a name="3">3. Modify translations for collection '%s'</a>&nbsp;&nbsp;&nbsp;<small>[<a href="%s/help/admin/websearch-admin-guide#3.3">?</a>]</small>""" % (col_dict[colID], CFG_SITE_URL)

        if sel_type == '':
            sel_type = get_col_nametypes()[0][0]

        header = ['Language', 'Translation']
        actions = []

        types = get_col_nametypes()
        types.extend([('v', '"Focus on" box'), ('r', '"Narrow by" box'), ('l', '"Latest additions" box')])
        if len(types) > 1:
            text  = """
            <span class="adminlabel">Name type</span>
            <select name="sel_type" class="admin_w200">
            """
            for (key, value) in types:
                text += """<option value="%s" %s>%s""" % (key, key == sel_type and 'selected="selected"' or '', value)
                trans_names = get_name(colID, ln, key, "collection")
                if trans_names and trans_names[0][0]:
                    text += ": %s" % trans_names[0][0]
                text += "</option>"
            text += """</select>"""

            output += createhiddenform(action="modifytranslations#3",
                                       text=text,
                                       button="Select",
                                       colID=colID,
                                       ln=ln,
                                       confirm=0)

        if confirm in [-1, "-1", 0, "0"]:
            trans = []
            for (key, value) in sitelangs:
                try:
                    trans_names = get_name(colID, key, sel_type, table, identifier_column)
                    trans.append(trans_names[0][0])
                except StandardError, e:
                    trans.append('')

        for nr in range(0, len(sitelangs)):
            actions.append(["%s" % (sitelangs[nr][1],)])
            actions[-1].append('<input type="text" name="trans" size="30" value="%s"/>' % trans[nr])

        text = tupletotable(header=header, tuple=actions)
        output += createhiddenform(action="modifytranslations#3",
                                   text=text,
                                   button="Modify",
                                   colID=colID,
                                   sel_type=sel_type,
                                   ln=ln,
                                   confirm=2)

        if sel_type and len(trans) and confirm in ["2", 2]:
            output += write_outcome(finresult)

    body = [output]

    if callback:
        return perform_editcollection(colID, ln, "perform_modifytranslations", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_modifyrankmethods(colID, ln, func='', rnkID='', confirm=0, callback='yes'):
    """Modify which rank methods is visible to the collection
    func - remove or add rank method
    rnkID - the id of the rank method."""

    output = ""
    subtitle = ""

    col_dict = dict(get_def_name('', "collection"))
    rnk_dict = dict(get_def_name('', "rnkMETHOD"))
    if colID and col_dict.has_key(int(colID)):
        colID = int(colID)
        if func in ["0", 0] and confirm in ["1", 1]:
            finresult = attach_rnk_col(colID, rnkID)
        elif func in ["1", 1] and confirm in ["1", 1]:
            finresult = detach_rnk_col(colID, rnkID)

        subtitle = """<a name="9">9. Modify rank options for collection '%s'</a>&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/websearch-admin-guide#3.9">?</a>]</small>""" % (col_dict[colID], CFG_SITE_URL)
        output  = """
        <dl>
        <dt>The rank methods enabled for the collection '%s' is:</dt>
        """ % col_dict[colID]

        rnkmethods = get_col_rnk(colID, ln)
        output += """<dd>"""
        if not rnkmethods:
            output += """No rank methods"""
        else:
            for id, name in rnkmethods:
                output += """%s, """ % name
        output += """</dd>
        </dl>
        """

        rnk_list = get_def_name('', "rnkMETHOD")
        rnk_dict_in_col = dict(get_col_rnk(colID, ln))
        rnk_list = filter(lambda x: not rnk_dict_in_col.has_key(x[0]), rnk_list)
        if rnk_list:
            text  = """
            <span class="adminlabel">Enable:</span>
            <select name="rnkID" class="admin_w200">
            <option value="-1">- select rank method -</option>
            """
            for (id, name) in rnk_list:
                text += """<option value="%s" %s>%s</option>""" % (id, (func in ["0", 0] and confirm in ["0", 0] and int(rnkID) == int(id)) and 'selected="selected"' or '' , name)
            text += """</select>"""
            output += createhiddenform(action="modifyrankmethods#9",
                                       text=text,
                                       button="Enable",
                                       colID=colID,
                                       ln=ln,
                                       func=0,
                                       confirm=1)

        if confirm in ["1", 1] and func in ["0", 0] and int(rnkID) != -1:
            output += write_outcome(finresult)
        elif confirm not in ["0", 0] and func in ["0", 0]:
            output += """<b><span class="info">Please select a rank method.</span></b>"""

        coll_list = get_col_rnk(colID, ln)
        if coll_list:
            text  = """
            <span class="adminlabel">Disable:</span>
            <select name="rnkID" class="admin_w200">
            <option value="-1">- select rank method-</option>
            """

            for (id, name) in coll_list:
                text += """<option value="%s" %s>%s</option>""" % (id, (func in ["1", 1] and confirm in ["0", 0] and int(rnkID) == int(id)) and 'selected="selected"' or '' , name)
            text += """</select>"""
            output += createhiddenform(action="modifyrankmethods#9",
                                       text=text,
                                       button="Disable",
                                       colID=colID,
                                       ln=ln,
                                       func=1,
                                       confirm=1)

        if confirm in ["1", 1] and func in ["1", 1] and int(rnkID) != -1:
            output += write_outcome(finresult)
        elif confirm not in ["0", 0] and func in ["1", 1]:
            output += """<b><span class="info">Please select a rank method.</span></b>"""

    body = [output]

    if callback:
        return perform_editcollection(colID, ln, "perform_modifyrankmethods", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_addcollectiontotree(colID, ln, add_dad='', add_son='', rtype='', mtype='', callback='yes', confirm=-1):
    """Form to add a collection to the tree.
    add_dad - the dad to add the collection to
    add_son - the collection to add
    rtype - add it as a regular or virtual
    mtype - add it to the regular or virtual tree."""

    output = ""
    output2 = ""
    subtitle = """Attach collection to tree&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/websearch-admin-guide#2.2">?</a>]</small>""" % (CFG_SITE_URL)

    col_dict = dict(get_def_name('', "collection"))
    if confirm not in [-1, "-1"] and not (add_son and add_dad and rtype):
        output2 += """<b><span class="info">All fields must be filled.</span></b><br /><br />
        """
    elif add_son and add_dad and rtype:
        add_son = int(add_son)
        add_dad = int(add_dad)
        if confirm not in [-1, "-1"]:
            if add_son == add_dad:
                output2 += """<b><span class="info">Cannot add a collection as a pointer to itself.</span></b><br /><br />
                """
            elif check_col(add_dad, add_son):
                res = add_col_dad_son(add_dad, add_son, rtype)
                output2 += write_outcome(res)
                if res[0] == 1:
                    output2 += """<b><span class="info"><br /> The collection will appear on your website after the next webcoll run. You can either run it manually or wait until bibsched does it for you.</span></b><br /><br />
                    """
            else:
                output2 += """<b><span class="info">Cannot add the collection '%s' as a %s subcollection of '%s' since it will either create a loop, or the association already exists.</span></b><br /><br />
                """ % (col_dict[add_son], (rtype=="r" and 'regular' or 'virtual'), col_dict[add_dad])
        add_son = ''
        add_dad = ''
        rtype = ''

    tree = get_col_tree(colID)
    col_list = col_dict.items()
    col_list.sort(compare_on_val)

    output = show_coll_not_in_tree(colID, ln, col_dict)
    text = """
    <span class="adminlabel">Attach collection:</span>
    <select name="add_son" class="admin_w200">
    <option value="">- select collection -</option>
    """
    for (id, name) in col_list:
        if id != colID:
            text += """<option value="%s" %s>%s</option>""" % (id, str(id)==str(add_son) and 'selected="selected"' or '', name)
    text += """
    </select><br />
    <span class="adminlabel">to parent collection:</span>
    <select name="add_dad" class="admin_w200">
    <option value="">- select parent collection -</option>
    """

    for (id, name) in col_list:
        text += """<option value="%s" %s>%s</option>
        """ % (id, str(id)==add_dad and 'selected="selected"' or '', name)
    text += """</select><br />
    """

    text += """
    <span class="adminlabel">with relationship:</span>
    <select name="rtype" class="admin_w200">
    <option value="">- select relationship -</option>
    <option value="r" %s>Regular (Narrow by...)</option>
    <option value="v" %s>Virtual (Focus on...)</option>
    </select>
    """ % ((rtype=="r" and 'selected="selected"' or ''), (rtype=="v" and 'selected="selected"' or ''))
    output += createhiddenform(action="%s/admin/websearch/websearchadmin.py/addcollectiontotree" % CFG_SITE_URL,
                               text=text,
                               button="Add",
                               colID=colID,
                               ln=ln,
                               confirm=1)
    output += output2

    #output += perform_showtree(colID, ln)
    body = [output]

    if callback:
        return perform_index(colID, ln, mtype="perform_addcollectiontotree", content=addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_addcollection(colID, ln, colNAME='', dbquery='', callback="yes", confirm=-1):
    """form to add a new collection.
    colNAME - the name of the new collection
    dbquery - the dbquery of the new collection"""

    output = ""
    subtitle = """Create new collection&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/websearch-admin-guide#2.1">?</a>]</small>""" % (CFG_SITE_URL)
    text = """
    <span class="adminlabel">Default name</span>
    <input class="admin_w200" type="text" name="colNAME" value="%s" /><br />
    """ % colNAME
    output = createhiddenform(action="%s/admin/websearch/websearchadmin.py/addcollection" % CFG_SITE_URL,
                              text=text,
                              colID=colID,
                              ln=ln,
                              button="Add collection",
                              confirm=1)
    if colNAME and confirm in ["1", 1]:
        res = add_col(colNAME, '')
        output += write_outcome(res)
        if res[0] == 1:
            output += perform_addcollectiontotree(colID=colID, ln=ln, add_son=res[1], callback='')
    elif confirm not in ["-1", -1]:
        output += """<b><span class="info">Please give the collection a name.</span></b>"""

    body = [output]

    if callback:
        return perform_index(colID, ln=ln, mtype="perform_addcollection", content=addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_modifydbquery(colID, ln, dbquery='', callback='yes', confirm=-1):
    """form to modify the dbquery of the collection.
    dbquery - the dbquery of the collection."""

    subtitle = ''
    output  = ""

    col_dict = dict(get_def_name('', "collection"))
    if colID and col_dict.has_key(int(colID)):
        colID = int(colID)
        subtitle = """<a name="1">1. Modify collection query for collection '%s'</a>&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/websearch-admin-guide#3.1">?</a>]</small>""" % (col_dict[colID], CFG_SITE_URL)

        if confirm == -1:
            res = run_sql("SELECT dbquery FROM collection WHERE id=%s" % colID)
            dbquery = res[0][0]
        if not dbquery:
            dbquery = ''

        reg_sons = len(get_col_tree(colID, 'r'))
        vir_sons = len(get_col_tree(colID, 'v'))
        if reg_sons > 1:
            if dbquery:
                output += "Warning: This collection got subcollections, and should because of this not have a collection query, for further explanation, check the WebSearch Guide<br />"
        elif reg_sons <= 1:
            if not dbquery:
                output += "Warning: This collection does not have any subcollections, and should because of this have a collection query, for further explanation, check the WebSearch Guide<br />"

        text = """
        <span class="adminlabel">Query</span>
        <input class="admin_w200" type="text" name="dbquery" value="%s" /><br />
        """ % cgi.escape(dbquery, 1)
        output += createhiddenform(action="modifydbquery",
                                   text=text,
                                   button="Modify",
                                   colID=colID,
                                   ln=ln,
                                   confirm=1)

        if confirm in ["1", 1]:
            res = modify_dbquery(colID, dbquery)
            if res:
                if dbquery == "":
                    text = """<b><span class="info">Query removed for this collection.</span></b>"""
                else:
                    text = """<b><span class="info">Query set for this collection.</span></b>"""
            else:
                text = """<b><span class="info">Sorry, could not change query.</span></b>"""
            output += text

    body = [output]

    if callback:
        return perform_editcollection(colID, ln, "perform_modifydbquery", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_modifycollectiontree(colID, ln, move_up='', move_down='', move_from='', move_to='', delete='', rtype='', callback='yes', confirm=0):
    """to modify the collection tree: move a collection up and down, delete a collection, or change the father of the collection.
    colID - the main collection of the tree, the root
    move_up - move this collection up (is not the collection id, but the place in the tree)
    move_up - move this collection down (is not the collection id, but the place in the tree)
    move_from - move this collection from the current positon (is not the collection id, but the place in the tree)
    move_to - move the move_from collection and set this as it's father. (is not the collection id, but the place in the tree)
    delete - delete this collection from the tree  (is not the collection id, but the place in the tree)
    rtype - the type of the collection in the tree, regular or virtual"""

    colID = int(colID)
    tree = get_col_tree(colID, rtype)
    col_dict = dict(get_def_name('', "collection"))

    subtitle = """Modify collection tree: %s&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/websearch-admin-guide#2.3">?</a>]&nbsp;&nbsp;&nbsp;<a href="%s/admin/websearch/websearchadmin.py/showtree?colID=%s&amp;ln=%s">Printer friendly version</a></small>""" % (col_dict[colID], CFG_SITE_URL, CFG_SITE_URL, colID, ln)
    fin_output = ""
    output = ""

    try:
        if move_up:
            move_up = int(move_up)
            switch = find_last(tree, move_up)
            if switch and switch_col_treescore(tree[move_up], tree[switch]):
                output += """<b><span class="info">Moved the %s collection '%s' up and '%s' down.</span></b><br /><br />
                """ % ((rtype=="r" and 'regular' or 'virtual'), col_dict[tree[move_up][0]], col_dict[tree[switch][0]])
            else:
                output += """<b><span class="info">Could not move the %s collection '%s' up and '%s' down.</span></b><br /><br />
                """ % ((rtype=="r" and 'regular' or 'virtual'), col_dict[tree[move_up][0]], col_dict[tree[switch][0]])
        elif move_down:
            move_down = int(move_down)
            switch = find_next(tree, move_down)
            if switch and switch_col_treescore(tree[move_down], tree[switch]):
                output += """<b><span class="info">Moved the %s collection '%s' down and '%s' up.</span></b><br /><br />
                """ % ((rtype=="r" and 'regular' or 'virtual'), col_dict[tree[move_down][0]], col_dict[tree[switch][0]])
            else:
                output += """<b><span class="info">Could not move the %s collection '%s' up and '%s' down.</span></b><br /><br />
                """ % ((rtype=="r" and 'regular' or 'virtual'), col_dict[tree[move_up][0]],col_dict[tree[switch][0]])
        elif delete:
            delete = int(delete)
            if confirm in [0, "0"]:
                if col_dict[tree[delete][0]] != col_dict[tree[delete][3]]:
                    text = """<b>Do you want to remove the %s collection '%s' and its subcollections in the %s collection '%s'.</b>
                    """ % ((tree[delete][4]=="r" and 'regular' or 'virtual'), col_dict[tree[delete][0]], (rtype=="r" and 'regular' or 'virtual'), col_dict[tree[delete][3]])
                else:
                    text = """<b>Do you want to remove all subcollections of the %s collection '%s'.</b>
                    """ % ((rtype=="r" and 'regular' or 'virtual'), col_dict[tree[delete][3]])

                output += createhiddenform(action="%s/admin/websearch/websearchadmin.py/modifycollectiontree#tree" % CFG_SITE_URL,
                                           text=text,
                                           button="Confirm",
                                           colID=colID,
                                           delete=delete,
                                           rtype=rtype,
                                           ln=ln,
                                           confirm=1)
                output += createhiddenform(action="%s/admin/websearch/websearchadmin.py/index?mtype=perform_modifycollectiontree#tree" % CFG_SITE_URL,
                                           text="<b>To cancel</b>",
                                           button="Cancel",
                                           colID=colID,
                                           ln=ln)
            else:
                if remove_col_subcol(tree[delete][0], tree[delete][3], rtype):
                    if col_dict[tree[delete][0]] != col_dict[tree[delete][3]]:
                        output += """<b><span class="info">Removed the %s collection '%s' and its subcollections in subdirectory '%s'.</span></b><br /><br />
                        """ % ((tree[delete][4]=="r" and 'regular' or 'virtual'), col_dict[tree[delete][0]], col_dict[tree[delete][3]])
                    else:
                        output += """<b><span class="info">Removed the subcollections of the %s collection '%s'.</span></b><br /><br />
                        """ % ((rtype=="r" and 'regular' or 'virtual'), col_dict[tree[delete][3]])

                else:
                    output += """<b><span class="info">Could not remove the collection from the tree.</span></b><br /><br />
                    """
                delete = ''
        elif move_from and not move_to:
            move_from_rtype = move_from[0]
            move_from_id = int(move_from[1:len(move_from)])
            text = """<b>Select collection to place the %s collection '%s' under.</b><br /><br />
            """ % ((move_from_rtype=="r" and 'regular' or 'virtual'), col_dict[tree[move_from_id][0]])
            output += createhiddenform(action="%s/admin/websearch/websearchadmin.py/index?mtype=perform_modifycollectiontree#tree" % CFG_SITE_URL,
                                       text=text,
                                       button="Cancel",
                                       colID=colID,
                                       ln=ln)
        elif move_from and move_to:
            move_from_rtype = move_from[0]
            move_from_id = int(move_from[1:len(move_from)])
            move_to_rtype = move_to[0]
            move_to_id = int(move_to[1:len(move_to)])
            tree_from = get_col_tree(colID, move_from_rtype)
            tree_to = get_col_tree(colID, move_to_rtype)

            if confirm in [0, '0']:
                if move_from_id == move_to_id and move_from_rtype == move_to_rtype:
                    output += """<b><span class="info">Cannot move to itself.</span></b><br /><br />
                    """
                elif tree_from[move_from_id][3] == tree_to[move_to_id][0] and move_from_rtype==move_to_rtype:
                    output += """<b><span class="info">The collection is already there.</span></b><br /><br />
                    """
                elif check_col(tree_to[move_to_id][0], tree_from[move_from_id][0]) or (tree_to[move_to_id][0] == 1 and tree_from[move_from_id][3] == tree_to[move_to_id][0] and move_from_rtype != move_to_rtype):
                    text = """<b>Move %s collection '%s' to the %s collection '%s'.</b>
                    """ % ((tree_from[move_from_id][4]=="r" and 'regular' or 'virtual'), col_dict[tree_from[move_from_id][0]], (tree_to[move_to_id][4]=="r" and 'regular' or 'virtual'), col_dict[tree_to[move_to_id][0]])
                    output += createhiddenform(action="%s/admin/websearch/websearchadmin.py/modifycollectiontree#tree" % CFG_SITE_URL,
                                               text=text,
                                               button="Confirm",
                                               colID=colID,
                                               move_from=move_from,
                                               move_to=move_to,
                                               ln=ln,
                                               rtype=rtype,
                                               confirm=1)
                    output += createhiddenform(action="%s/admin/websearch/websearchadmin.py/index?mtype=perform_modifycollectiontree#tree" % CFG_SITE_URL,
                                               text="""<b>To cancel</b>""",
                                               button="Cancel",
                                               colID=colID,
                                               ln=ln)
                else:
                    output += """<b><span class="info">Cannot move the collection '%s' and set it as a subcollection of '%s' since it will create a loop.</span></b><br /><br />
                    """ % (col_dict[tree_from[move_from_id][0]], col_dict[tree_to[move_to_id][0]])
            else:
                if (move_to_id != 0 and move_col_tree(tree_from[move_from_id], tree_to[move_to_id])) or (move_to_id == 0 and move_col_tree(tree_from[move_from_id], tree_to[move_to_id], move_to_rtype)):
                    output += """<b><span class="info">Moved %s collection '%s' to the %s collection '%s'.</span></b><br /><br />
                    """ % ((move_from_rtype=="r" and 'regular' or 'virtual'), col_dict[tree_from[move_from_id][0]], (move_to_rtype=="r" and 'regular' or 'virtual'), col_dict[tree_to[move_to_id][0]])
                else:
                    output += """<b><span class="info">Could not move %s collection '%s' to the %s collection '%s'.</span></b><br /><br />
                    """ % ((move_from_rtype=="r" and 'regular' or 'virtual'), col_dict[tree_from[move_from_id][0]], (move_to_rtype=="r" and 'regular' or 'virtual'), col_dict[tree_to[move_to_id][0]])
            move_from = ''
            move_to = ''
        else:
            output += """
            """
    except StandardError, e:
        register_exception()
        return """<b><span class="info">An error occured.</span></b>
        """

    output += """<table border ="0" width="100%">
    <tr><td width="50%">
    <b>Narrow by collection:</b>
    </td><td width="50%">
    <b>Focus on...:</b>
    </td></tr><tr><td valign="top">
    """

    tree = get_col_tree(colID, 'r')
    output += create_colltree(tree, col_dict, colID, ln, move_from, move_to, 'r', "yes")
    output += """</td><td valign="top">
    """
    tree = get_col_tree(colID, 'v')
    output += create_colltree(tree, col_dict, colID, ln, move_from, move_to, 'v', "yes")
    output += """</td>
    </tr>
    </table>
    """

    body = [output]

    if callback:
        return perform_index(colID, ln, mtype="perform_modifycollectiontree", content=addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_showtree(colID, ln):
    """create collection tree/hiarchy"""

    col_dict = dict(get_def_name('', "collection"))
    subtitle = "Collection tree: %s" % col_dict[int(colID)]
    output = """<table border ="0" width="100%">
    <tr><td width="50%">
    <b>Narrow by collection:</b>
    </td><td width="50%">
    <b>Focus on...:</b>
    </td></tr><tr><td valign="top">
    """
    tree = get_col_tree(colID, 'r')
    output += create_colltree(tree, col_dict, colID, ln, '', '', 'r', '')
    output += """</td><td valign="top">
    """
    tree = get_col_tree(colID, 'v')
    output += create_colltree(tree, col_dict, colID, ln, '', '', 'v', '')
    output += """</td>
    </tr>
    </table>
    """

    body = [output]

    return addadminbox(subtitle, body)

def perform_addportalbox(colID, ln, title='', body='', callback='yes', confirm=-1):
    """form to add a new portalbox
    title - the title of the portalbox
    body - the body of the portalbox"""

    col_dict = dict(get_def_name('', "collection"))
    colID = int(colID)
    subtitle = """<a name="5.1"></a>Create new portalbox"""
    text = """
    <span class="adminlabel">Title</span>
    <textarea cols="50" rows="1" class="admin_wvar" type="text" name="title">%s</textarea><br />
    <span class="adminlabel">Body</span>
    <textarea cols="50" rows="10" class="admin_wvar" type="text" name="body">%s</textarea><br />
    """ % (cgi.escape(title), cgi.escape(body))
    output = createhiddenform(action="addportalbox#5.1",
                              text=text,
                              button="Add",
                              colID=colID,
                              ln=ln,
                              confirm=1)

    if body and confirm in [1, "1"]:
        res = add_pbx(title, body)
        output += write_outcome(res)
        if res[1] == 1:
            output += """<b><span class="info"><a href="addexistingportalbox?colID=%s&amp;ln=%s&amp;pbxID=%s#5">Add portalbox to collection</a></span></b>""" % (colID, ln, res[1])
    elif confirm not in [-1, "-1"]:
        output  += """<b><span class="info">Body field must be filled.</span></b>
        """

    body = [output]

    return perform_showportalboxes(colID, ln, content=addadminbox(subtitle, body))

def perform_addexistingportalbox(colID, ln, pbxID=-1, score=0, position='', sel_ln='', callback='yes', confirm=-1):
    """form to add an existing portalbox to a collection.
    colID - the collection to add the portalbox to
    pbxID - the portalbox to add
    score - the importance of the portalbox.
    position - the position of the portalbox on the page
    sel_ln - the language of the portalbox"""

    subtitle = """<a name="5.2"></a>Add existing portalbox to collection"""
    output  = ""

    colID = int(colID)
    res = get_pbx()
    pos = get_pbx_pos()
    lang = dict(get_languages())
    col_dict = dict(get_def_name('', "collection"))
    pbx_dict = dict(map(lambda x: (x[0], x[1]), res))

    col_pbx = get_col_pbx(colID)
    col_pbx = dict(map(lambda x: (x[0], x[5]), col_pbx))
    if len(res) > 0:
        text  = """
        <span class="adminlabel">Portalbox</span>
        <select name="pbxID" class="admin_w200">
        <option value="-1">- Select portalbox -</option>
        """
        for (id, t_title, t_body) in res:
            text += """<option value="%s" %s>%s - %s...</option>\n""" % \
                     (id, id  == int(pbxID) and 'selected="selected"' or '',
                      t_title[:40], cgi.escape(t_body[0:40 - min(40, len(t_title))]))
        text += """</select><br />
        <span class="adminlabel">Language</span>
        <select name="sel_ln" class="admin_w200">
        <option value="">- Select language -</option>
        """
        listlang = lang.items()
        listlang.sort()
        for (key, name) in listlang:
            text += """<option value="%s" %s>%s</option>
            """ % (key, key == sel_ln and 'selected="selected"' or '', name)
        text += """</select><br />
        <span class="adminlabel">Position</span>
        <select name="position" class="admin_w200">
        <option value="">- Select position -</option>
        """
        listpos = pos.items()
        listpos.sort()
        for (key, name) in listpos:
            text += """<option value="%s" %s>%s</option>""" % (key, key==position and 'selected="selected"' or '', name)
        text += "</select>"
        output += createhiddenform(action="addexistingportalbox#5.2",
                                   text=text,
                                   button="Add",
                                   colID=colID,
                                   ln=ln,
                                   confirm=1)
    else:
        output  = """No existing portalboxes to add, please create a new one.
        """

    if pbxID > -1 and position and sel_ln and confirm in [1, "1"]:
        pbxID = int(pbxID)
        res = add_col_pbx(colID, pbxID, sel_ln, position, '')
        output += write_outcome(res)
    elif pbxID > -1 and confirm not in [-1, "-1"]:
        output  += """<b><span class="info">All fields must be filled.</span></b>
        """

    body = [output]

    output = "<br />" + addadminbox(subtitle, body)
    return perform_showportalboxes(colID, ln, content=output)

def perform_deleteportalbox(colID, ln, pbxID=-1, callback='yes', confirm=-1):
    """form to delete a portalbox which is not in use.
    colID - the current collection.
    pbxID - the id of the portalbox"""

    subtitle = """<a name="5.3"></a>Delete an unused portalbox"""
    output  = ""

    colID = int(colID)
    if pbxID not in [-1, "-1"] and confirm in [1, "1"]:
        ares = get_pbx()
        pbx_dict = dict(map(lambda x: (x[0], x[1]), ares))
        if pbx_dict.has_key(int(pbxID)):
            pname = pbx_dict[int(pbxID)]
            ares = delete_pbx(int(pbxID))
        else:
            return """<b><span class="info">This portalbox does not exist</span></b>"""

    res = get_pbx()
    col_dict = dict(get_def_name('', "collection"))
    pbx_dict = dict(map(lambda x: (x[0], x[1]), res))
    col_pbx = get_col_pbx()
    col_pbx = dict(map(lambda x: (x[0], x[5]), col_pbx))

    if len(res) > 0:
        text  = """
        <span class="adminlabel">Portalbox</span>
        <select name="pbxID" class="admin_w200">
        """
        text += """<option value="-1">- Select portalbox -"""
        for (id, t_title, t_body) in res:
            if not col_pbx.has_key(id):
                text += """<option value="%s" %s>%s - %s...""" % (id, id  == int(pbxID) and 'selected="selected"' or '', t_title, cgi.escape(t_body[0:10]))
            text += "</option>"
        text += """</select><br />"""

        output += createhiddenform(action="deleteportalbox#5.3",
                                   text=text,
                                   button="Delete",
                                   colID=colID,
                                   ln=ln,
                                   confirm=1)

    if pbxID not in [-1, "-1"]:
        pbxID = int(pbxID)
        if confirm in [1, "1"]:
            output += write_outcome(ares)
    elif confirm not in [-1, "-1"]:
        output  += """<b><span class="info">Choose a portalbox to delete.</span></b>
        """

    body = [output]

    output = "<br />" + addadminbox(subtitle, body)
    return perform_showportalboxes(colID, ln, content=output)

def perform_modifyportalbox(colID, ln, pbxID=-1, score='', position='', sel_ln='', title='', body='', callback='yes', confirm=-1):
    """form to modify a portalbox in a collection, or change the portalbox itself.
    colID - the id of the collection.
    pbxID - the portalbox to change
    score - the score of the portalbox connected to colID which should be changed.
    position - the position of the portalbox in collection colID to change."""

    subtitle  = ""
    output  = ""

    colID = int(colID)
    res = get_pbx()
    pos = get_pbx_pos()
    lang = dict(get_languages())
    col_dict = dict(get_def_name('', "collection"))
    pbx_dict = dict(map(lambda x: (x[0], x[1]), res))
    col_pbx = get_col_pbx(colID)
    col_pbx = dict(map(lambda x: (x[0], x[5]), col_pbx))

    if pbxID not in [-1, "-1"]:
        pbxID = int(pbxID)
        subtitle = """<a name="5.4"></a>Modify portalbox '%s' for this collection""" % pbx_dict[pbxID]
        col_pbx = get_col_pbx(colID)
        if not (score and position) and not (body and title):
            for (id_pbx, id_collection, tln, score, position, title, body) in col_pbx:
                if id_pbx == pbxID:
                    break

        output += """Collection (presentation) specific values (Changes implies only to this collection.)<br />"""
        text = """
        <span class="adminlabel">Position</span>
        <select name="position" class="admin_w200">
        """
        listpos = pos.items()
        listpos.sort()
        for (key, name) in listpos:
            text += """<option value="%s" %s>%s""" % (key, key==position and 'selected="selected"' or '', name)
            text += "</option>"
        text += """</select><br />"""

        output += createhiddenform(action="modifyportalbox#5.4",
                                   text=text,
                                   button="Modify",
                                   colID=colID,
                                   pbxID=pbxID,
                                   score=score,
                                   title=title,
                                   body=cgi.escape(body, 1),
                                   sel_ln=sel_ln,
                                   ln=ln,
                                   confirm=3)

        if pbxID > -1 and score and position and confirm in [3, "3"]:
            pbxID = int(pbxID)
            res = modify_pbx(colID, pbxID, sel_ln, score, position, '', '')
            res2 = get_pbx()
            pbx_dict = dict(map(lambda x: (x[0], x[1]), res2))
            output += write_outcome(res)
        output += """<br />Portalbox (content) specific values (any changes appears everywhere the portalbox is used.)"""
        text = """
        <span class="adminlabel">Title</span>
        <textarea cols="50" rows="1" class="admin_wvar" type="text" name="title">%s</textarea><br />
        """ % cgi.escape(title)

        text += """
        <span class="adminlabel">Body</span>
        <textarea cols="50" rows="10" class="admin_wvar" type="text" name="body">%s</textarea><br />
        """ % cgi.escape(body)

        output += createhiddenform(action="modifyportalbox#5.4",
                                   text=text,
                                   button="Modify",
                                   colID=colID,
                                   pbxID=pbxID,
                                   sel_ln=sel_ln,
                                   score=score,
                                   position=position,
                                   ln=ln,
                                   confirm=4)

        if pbxID > -1 and confirm in [4, "4"]:
            pbxID = int(pbxID)
            res = modify_pbx(colID, pbxID, sel_ln, '', '', title, body)
            output += write_outcome(res)
    else:
        output  = """No portalbox to modify."""

    body = [output]

    output = "<br />" + addadminbox(subtitle, body)
    return perform_showportalboxes(colID, ln, content=output)

def perform_switchpbxscore(colID, id_1, id_2, sel_ln, ln):
    """Switch the score of id_1 and id_2 in collection_portalbox.
    colID - the current collection
    id_1/id_2 - the id's to change the score for.
    sel_ln - the language of the portalbox"""
    output = ""
    res = get_pbx()
    pbx_dict = dict(map(lambda x: (x[0], x[1]), res))
    res = switch_pbx_score(colID, id_1, id_2, sel_ln)
    output += write_outcome(res)
    return perform_showportalboxes(colID, ln, content=output)

def perform_showportalboxes(colID, ln, callback='yes', content='', confirm=-1):
    """show the portalboxes of this collection.
    colID - the portalboxes to show the collection for."""

    colID = int(colID)
    col_dict = dict(get_def_name('', "collection"))

    subtitle = """<a name="5">5. Modify portalboxes for collection '%s'</a>&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/websearch-admin-guide#3.5">?</a>]</small>""" % (col_dict[colID], CFG_SITE_URL)
    output  = ""
    pos = get_pbx_pos()

    output = """<dl>
     <dt>Portalbox actions (not related to this collection)</dt>
     <dd><a href="addportalbox?colID=%s&amp;ln=%s#5.1">Create new portalbox</a></dd>
     <dd><a href="deleteportalbox?colID=%s&amp;ln=%s#5.3">Delete an unused portalbox</a></dd>
     <dt>Collection specific actions</dt>
     <dd><a href="addexistingportalbox?colID=%s&amp;ln=%s#5.2">Add existing portalbox to collection</a></dd>
    </dl>
    """  % (colID, ln, colID, ln, colID, ln)

    header = ['Position', 'Language', '', 'Title', 'Actions']
    actions = []
    sitelangs = get_languages()
    lang = dict(sitelangs)

    pos_list = pos.items()
    pos_list.sort()

    if len(get_col_pbx(colID)) > 0:
        for (key, value) in sitelangs:
            for (pos_key, pos_value) in pos_list:
                res = get_col_pbx(colID, key, pos_key)
                i = 0
                for (pbxID, colID_pbx, tln, score, position, title, body) in res:
                    move = """<table cellspacing="1" cellpadding="0" border="0"><tr><td>"""
                    if i != 0:
                        move += """<a href="%s/admin/websearch/websearchadmin.py/switchpbxscore?colID=%s&amp;ln=%s&amp;id_1=%s&amp;id_2=%s&amp;sel_ln=%s&amp;rand=%s#5"><img border="0" src="%s/img/smallup.gif" title="Move portalbox up" alt="up" /></a>""" % (CFG_SITE_URL, colID, ln, pbxID, res[i - 1][0], tln, random.randint(0, 1000), CFG_SITE_URL)
                    else:
                        move += "&nbsp;&nbsp;&nbsp;"
                    move += "</td><td>"
                    i += 1
                    if i != len(res):
                        move += """<a href="%s/admin/websearch/websearchadmin.py/switchpbxscore?colID=%s&amp;ln=%s&amp;id_1=%s&amp;id_2=%s&amp;sel_ln=%s&amp;rand=%s#5"><img border="0" src="%s/img/smalldown.gif" title="Move portalbox down" alt="down" /></a>""" % (CFG_SITE_URL, colID, ln, pbxID, res[i][0], tln, random.randint(0, 1000), CFG_SITE_URL)
                    move += """</td></tr></table>"""
                    actions.append(["%s" % (i==1 and pos[position] or ''), "%s" % (i==1 and lang[tln] or ''), move, "%s" % title])

                    for col in [(('Modify', 'modifyportalbox'), ('Remove', 'removeportalbox'),)]:
                        actions[-1].append('<a href="%s/admin/websearch/websearchadmin.py/%s?colID=%s&amp;ln=%s&amp;pbxID=%s&amp;sel_ln=%s#5.4">%s</a>' % (CFG_SITE_URL, col[0][1], colID, ln, pbxID, tln, col[0][0]))
                        for (str, function) in col[1:]:
                            actions[-1][-1] += ' / <a href="%s/admin/websearch/websearchadmin.py/%s?colID=%s&amp;ln=%s&amp;pbxID=%s&amp;sel_ln=%s#5.5">%s</a>' % (CFG_SITE_URL, function, colID, ln, pbxID, tln, str)
        output += tupletotable(header=header, tuple=actions)
    else:
        output += """No portalboxes exists for this collection"""

    output += content
    body = [output]

    if callback:
        return perform_editcollection(colID, ln, "perform_showportalboxes", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_removeportalbox(colID, ln, pbxID='', sel_ln='', callback='yes', confirm=0):
    """form to remove a portalbox from a collection.
    colID - the current collection, remove the portalbox from this collection.
    sel_ln - remove the portalbox with this language
    pbxID - remove the portalbox with this id"""

    subtitle = """<a name="5.5"></a>Remove portalbox"""
    output  = ""

    col_dict = dict(get_def_name('', "collection"))
    res = get_pbx()
    pbx_dict = dict(map(lambda x: (x[0], x[1]), res))

    if colID and pbxID and sel_ln:
        colID = int(colID)
        pbxID = int(pbxID)

        if confirm in ["0", 0]:
            text = """Do you want to remove the portalbox '%s' from the collection '%s'.""" % (pbx_dict[pbxID], col_dict[colID])
            output += createhiddenform(action="removeportalbox#5.5",
                                       text=text,
                                       button="Confirm",
                                       colID=colID,
                                       pbxID=pbxID,
                                       sel_ln=sel_ln,
                                       confirm=1)
        elif confirm in ["1", 1]:
            res = remove_pbx(colID, pbxID, sel_ln)
            output += write_outcome(res)

    body = [output]

    output = "<br />" + addadminbox(subtitle, body)
    return perform_showportalboxes(colID, ln, content=output)

def perform_switchfmtscore(colID, type, id_1, id_2, ln):
    """Switch the score of id_1 and id_2 in the table type.
    colID - the current collection
    id_1/id_2 - the id's to change the score for.
    type - like "format" """

    fmt_dict = dict(get_def_name('', "format"))
    res = switch_score(colID, id_1, id_2, type)
    output = write_outcome(res)
    return perform_showoutputformats(colID, ln, content=output)

def perform_switchfldscore(colID, id_1, id_2, fmeth, ln):
    """Switch the score of id_1 and id_2 in collection_field_fieldvalue.
    colID - the current collection
    id_1/id_2 - the id's to change the score for."""

    fld_dict = dict(get_def_name('', "field"))
    res = switch_fld_score(colID, id_1, id_2)

    output = write_outcome(res)

    if fmeth == "soo":
        return perform_showsortoptions(colID, ln, content=output)
    elif fmeth == "sew":
        return perform_showsearchfields(colID, ln, content=output)
    elif fmeth == "seo":
        return perform_showsearchoptions(colID, ln, content=output)

def perform_switchfldvaluescore(colID, id_1, id_fldvalue_1, id_fldvalue_2, ln):
    """Switch the score of id_1 and id_2 in collection_field_fieldvalue.
    colID - the current collection
    id_1/id_2 - the id's to change the score for."""

    name_1 = run_sql("SELECT name from fieldvalue where id=%s", (id_fldvalue_1, ))[0][0]
    name_2 = run_sql("SELECT name from fieldvalue where id=%s", (id_fldvalue_2, ))[0][0]
    res = switch_fld_value_score(colID, id_1, id_fldvalue_1, id_fldvalue_2)
    output = write_outcome(res)
    return perform_modifyfield(colID, fldID=id_1, ln=ln, content=output)

def perform_addnewfieldvalue(colID, fldID, ln, name='', value='', callback="yes", confirm=-1):
    """form to add a new fieldvalue.
    name - the name of the new fieldvalue
    value - the value of the new fieldvalue
    """

    output = ""
    subtitle = """<a name="7.4"></a>Add new value"""
    text = """
    <span class="adminlabel">Display name</span>
    <input class="admin_w200" type="text" name="name" value="%s" /><br />
    <span class="adminlabel">Search value</span>
    <input class="admin_w200" type="text" name="value" value="%s" /><br />
    """ % (name, value)
    output = createhiddenform(action="%s/admin/websearch/websearchadmin.py/addnewfieldvalue" % CFG_SITE_URL,
                              text=text,
                              colID=colID,
                              fldID=fldID,
                              ln=ln,
                              button="Add",
                              confirm=1)
    if name and value and confirm in ["1", 1]:
        res = add_fldv(name, value)
        output += write_outcome(res)
        if res[0] == 1:
            res = add_col_fld(colID, fldID, 'seo', res[1])
            if res[0] == 0:
                output += "<br />" + write_outcome(res)
    elif confirm not in ["-1", -1]:
        output += """<b><span class="info">Please fill in name and value.</span></b>
        """

    body = [output]

    output = "<br />" + addadminbox(subtitle, body)
    return perform_modifyfield(colID, fldID=fldID, ln=ln, content=output)

def perform_modifyfieldvalue(colID, fldID, fldvID, ln, name='', value='', callback="yes", confirm=-1):
    """form to modify a fieldvalue.
    name - the name of the fieldvalue
    value - the value of the fieldvalue
    """

    if confirm in [-1, "-1"]:
        res = get_fld_value(fldvID)
        (id, name, value) = res[0]
    output = ""
    subtitle = """<a name="7.4"></a>Modify existing value"""

    output = """<dl>
     <dt><b><span class="info">Warning: Modifications done below will also inflict on all places the modified data is used.</span></b></dt>
    </dl>"""

    text = """
    <span class="adminlabel">Display name</span>
    <input class="admin_w200" type="text" name="name" value="%s" /><br />
    <span class="adminlabel">Search value</span>
    <input class="admin_w200" type="text" name="value" value="%s" /><br />
    """ % (name, value)
    output += createhiddenform(action="%s/admin/websearch/websearchadmin.py/modifyfieldvalue" % CFG_SITE_URL,
                              text=text,
                              colID=colID,
                              fldID=fldID,
                              fldvID=fldvID,
                              ln=ln,
                              button="Update",
                              confirm=1)
    output += createhiddenform(action="%s/admin/websearch/websearchadmin.py/modifyfieldvalue" % CFG_SITE_URL,
                              text="Delete value and all associations",
                              colID=colID,
                              fldID=fldID,
                              fldvID=fldvID,
                              ln=ln,
                              button="Delete",
                              confirm=2)
    if name and value and confirm in ["1", 1]:
        res = update_fldv(fldvID, name, value)
        output += write_outcome(res)
        #if res:
        #    output += """<b><span class="info">Operation successfully completed.</span></b>"""
        #else:
        #    output += """<b><span class="info">Operation failed.</span></b>"""
    elif confirm in ["2", 2]:
        res = delete_fldv(fldvID)
        output += write_outcome(res)
    elif confirm not in ["-1", -1]:
        output += """<b><span class="info">Please fill in name and value.</span></b>"""

    body = [output]

    output = "<br />" + addadminbox(subtitle, body)
    return perform_modifyfield(colID, fldID=fldID, ln=ln, content=output)

def perform_removefield(colID, ln, fldID='', fldvID='', fmeth='', callback='yes', confirm=0):
    """form to remove a field from a collection.
    colID - the current collection, remove the field from this collection.
    sel_ln - remove the field with this language
    fldID - remove the field with this id"""

    if fmeth == "soo":
        field = "sort option"
    elif fmeth == "sew":
        field = "search field"
    elif fmeth == "seo":
        field = "search option"
    else:
        field = "field"

    subtitle = """<a name="6.4"><a name="7.4"><a name="8.4"></a>Remove %s""" % field
    output  = ""
    col_dict = dict(get_def_name('', "collection"))
    fld_dict = dict(get_def_name('', "field"))
    res = get_fld_value()
    fldv_dict = dict(map(lambda x: (x[0], x[1]), res))

    if colID and fldID:
        colID = int(colID)
        fldID = int(fldID)
        if fldvID and fldvID != "None":
            fldvID = int(fldvID)

        if confirm in ["0", 0]:
            text = """Do you want to remove the %s '%s' %s from the collection '%s'.""" % (field, fld_dict[fldID], (fldvID not in["", "None"] and "with value '%s'" % fldv_dict[fldvID] or ''), col_dict[colID])
            output += createhiddenform(action="removefield#6.5",
                                       text=text,
                                       button="Confirm",
                                       colID=colID,
                                       fldID=fldID,
                                       fldvID=fldvID,
                                       fmeth=fmeth,
                                       confirm=1)
        elif confirm in ["1", 1]:
            res = remove_fld(colID, fldID, fldvID)
            output += write_outcome(res)

    body = [output]

    output = "<br />" + addadminbox(subtitle, body)

    if fmeth == "soo":
        return perform_showsortoptions(colID, ln, content=output)
    elif fmeth == "sew":
        return perform_showsearchfields(colID, ln, content=output)
    elif fmeth == "seo":
        return perform_showsearchoptions(colID, ln, content=output)

def perform_removefieldvalue(colID, ln, fldID='', fldvID='', fmeth='', callback='yes', confirm=0):
    """form to remove a field from a collection.
    colID - the current collection, remove the field from this collection.
    sel_ln - remove the field with this language
    fldID - remove the field with this id"""

    subtitle = """<a name="7.4"></a>Remove value"""
    output  = ""

    col_dict = dict(get_def_name('', "collection"))
    fld_dict = dict(get_def_name('', "field"))
    res = get_fld_value()
    fldv_dict = dict(map(lambda x: (x[0], x[1]), res))

    if colID and fldID:
        colID = int(colID)
        fldID = int(fldID)
        if fldvID and fldvID != "None":
            fldvID = int(fldvID)

        if confirm in ["0", 0]:
            text = """Do you want to remove the value '%s' from the search option '%s'.""" % (fldv_dict[fldvID], fld_dict[fldID])
            output += createhiddenform(action="removefieldvalue#7.4",
                                       text=text,
                                       button="Confirm",
                                       colID=colID,
                                       fldID=fldID,
                                       fldvID=fldvID,
                                       fmeth=fmeth,
                                       confirm=1)
        elif confirm in ["1", 1]:
            res = remove_fld(colID, fldID, fldvID)
            output += write_outcome(res)

    body = [output]

    output = "<br />" + addadminbox(subtitle, body)
    return perform_modifyfield(colID, fldID=fldID, ln=ln, content=output)

def perform_rearrangefieldvalue(colID, fldID, ln, callback='yes', confirm=-1):
    """rearrang the fieldvalues alphabetically
    colID - the collection
    fldID - the field to rearrange the fieldvalue for
    """

    subtitle = "Order values alphabetically"
    output  = ""
    col_fldv = get_col_fld(colID, 'seo', fldID)
    col_fldv = dict(map(lambda x: (x[1], x[0]), col_fldv))
    fldv_names = get_fld_value()
    fldv_names = map(lambda x: (x[0], x[1]), fldv_names)
    if not col_fldv.has_key(None):
        vscore = len(col_fldv)
        for (fldvID, name) in fldv_names:
            if col_fldv.has_key(fldvID):
                run_sql("UPDATE collection_field_fieldvalue SET score_fieldvalue=%s WHERE id_collection=%s and id_field=%s and id_fieldvalue=%s", (vscore, colID, fldID, fldvID))
                vscore -= 1
        output += write_outcome((1, ""))
    else:
        output += write_outcome((0, (0, "No values to order")))

    body = [output]

    output = "<br />" + addadminbox(subtitle, body)
    return perform_modifyfield(colID, fldID, ln, content=output)

def perform_rearrangefield(colID, ln, fmeth, callback='yes', confirm=-1):
    """rearrang the fields alphabetically
    colID - the collection
    """

    subtitle = "Order fields alphabetically"
    output  = ""
    col_fld = dict(map(lambda x: (x[0], x[1]), get_col_fld(colID, fmeth)))
    fld_names =  get_def_name('', "field")

    if len(col_fld) > 0:
        score = len(col_fld)
        for (fldID, name) in fld_names:
            if col_fld.has_key(fldID):
                run_sql("UPDATE collection_field_fieldvalue SET score=%s WHERE id_collection=%s and id_field=%s", (score, colID, fldID))
                score -= 1
        output += write_outcome((1, ""))
    else:
        output += write_outcome((0, (0, "No fields to order")))

    body = [output]

    output = "<br />" + addadminbox(subtitle, body)
    if fmeth == "soo":
        return perform_showsortoptions(colID, ln, content=output)
    elif fmeth == "sew":
        return perform_showsearchfields(colID, ln, content=output)
    elif fmeth == "seo":
        return perform_showsearchoptions(colID, ln, content=output)

def perform_addexistingfieldvalue(colID, fldID, fldvID=-1, ln=CFG_SITE_LANG, callback='yes', confirm=-1):
    """form to add an existing fieldvalue to a field.
    colID - the collection
    fldID - the field to add the fieldvalue to
    fldvID - the fieldvalue to add"""

    subtitle = """</a><a name="7.4"></a>Add existing value to search option"""
    output  = ""

    if fldvID not in [-1, "-1"] and confirm in [1, "1"]:
        fldvID = int(fldvID)
        ares = add_col_fld(colID, fldID, 'seo', fldvID)

    colID = int(colID)
    fldID = int(fldID)
    lang = dict(get_languages())
    res =  get_def_name('', "field")
    col_dict = dict(get_def_name('', "collection"))
    fld_dict = dict(res)
    col_fld = dict(map(lambda x: (x[0], x[1]), get_col_fld(colID, 'seo')))
    fld_value  = get_fld_value()
    fldv_dict = dict(map(lambda x: (x[0], x[1]), fld_value))

    text = """
    <span class="adminlabel">Value</span>
    <select name="fldvID" class="admin_w200">
    <option value="-1">- Select value -</option>
    """

    res = run_sql("SELECT id,name,value FROM fieldvalue ORDER BY name")
    for (id, name, value) in res:
        text += """<option value="%s" %s>%s - %s</option>
        """ % (id, id  == int(fldvID) and 'selected="selected"' or '', name, value)
    text += """</select><br />"""

    output += createhiddenform(action="addexistingfieldvalue#7.4",
                               text=text,
                               button="Add",
                               colID=colID,
                               fldID=fldID,
                               ln=ln,
                               confirm=1)

    if fldvID not in [-1, "-1"] and confirm in [1, "1"]:
        output += write_outcome(ares)
    elif confirm in [1, "1"]:
        output += """<b><span class="info">Select a value to add and try again.</span></b>"""

    body = [output]

    output = "<br />" + addadminbox(subtitle, body)
    return perform_modifyfield(colID, fldID, ln, content=output)

def perform_addexistingfield(colID, ln, fldID=-1, fldvID=-1, fmeth='', callback='yes', confirm=-1):
    """form to add an existing field to a collection.
    colID - the collection to add the field to
    fldID - the field to add
    sel_ln - the language of the field"""

    subtitle = """<a name="6.2"></a><a name="7.2"></a><a name="8.2"></a>Add existing field to collection"""
    output  = ""

    if fldID not in [-1, "-1"] and confirm in [1, "1"]:
        fldID = int(fldID)
        ares = add_col_fld(colID, fldID, fmeth, fldvID)

    colID = int(colID)
    lang = dict(get_languages())
    res =  get_def_name('', "field")
    col_dict = dict(get_def_name('', "collection"))
    fld_dict = dict(res)
    col_fld = dict(map(lambda x: (x[0], x[1]), get_col_fld(colID, fmeth)))
    fld_value  = get_fld_value()
    fldv_dict = dict(map(lambda x: (x[0], x[1]), fld_value))

    if fldvID:
        fldvID = int(fldvID)
    text  = """
    <span class="adminlabel">Field</span>
    <select name="fldID" class="admin_w200">
    <option value="-1">- Select field -</option>
    """
    for (id, var) in res:
        if fmeth == 'seo' or (fmeth != 'seo' and not col_fld.has_key(id)):
            text += """<option value="%s" %s>%s</option>
            """ % (id, '', fld_dict[id])

    text += """</select><br />"""

    output += createhiddenform(action="addexistingfield#6.2",
                               text=text,
                               button="Add",
                               colID=colID,
                               fmeth=fmeth,
                               ln=ln,
                               confirm=1)

    if fldID not in [-1, "-1"] and confirm in [1, "1"]:
        output += write_outcome(ares)
    elif fldID in [-1, "-1"] and confirm not in [-1, "-1"]:
        output  += """<b><span class="info">Select a field.</span></b>
        """

    body = [output]

    output = "<br />" + addadminbox(subtitle, body)
    if fmeth == "soo":
        return perform_showsortoptions(colID, ln, content=output)
    elif fmeth == "sew":
        return perform_showsearchfields(colID, ln, content=output)
    elif fmeth == "seo":
        return perform_showsearchoptions(colID, ln, content=output)

def perform_showsortoptions(colID, ln, callback='yes', content='', confirm=-1):
    """show the sort fields of this collection.."""

    colID = int(colID)
    col_dict = dict(get_def_name('', "collection"))
    fld_dict = dict(get_def_name('', "field"))
    fld_type = get_sort_nametypes()

    subtitle = """<a name="8">8. Modify sort options for collection '%s'</a>&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/websearch-admin-guide#3.8">?</a>]</small>""" % (col_dict[colID], CFG_SITE_URL)
    output = """<dl>
     <dt>Field actions (not related to this collection)</dt>
     <dd>Go to the BibIndex interface to modify the available sort options</dd>
     <dt>Collection specific actions
     <dd><a href="addexistingfield?colID=%s&amp;ln=%s&amp;fmeth=soo#8.2">Add sort option to collection</a></dd>
     <dd><a href="rearrangefield?colID=%s&amp;ln=%s&amp;fmeth=soo#8.2">Order sort options alphabetically</a></dd>
    </dl>
    """  % (colID, ln, colID, ln)

    header = ['', 'Sort option', 'Actions']

    actions = []
    sitelangs = get_languages()
    lang = dict(sitelangs)

    fld_type_list = fld_type.items()

    if len(get_col_fld(colID, 'soo')) > 0:
        res = get_col_fld(colID, 'soo')
        i = 0

        for (fldID, fldvID, stype, score, score_fieldvalue) in res:
            move = """<table cellspacing="1" cellpadding="0" border="0"><tr><td>"""
            if i != 0:
                move += """<a href="%s/admin/websearch/websearchadmin.py/switchfldscore?colID=%s&amp;ln=%s&amp;id_1=%s&amp;id_2=%s&amp;fmeth=soo&amp;rand=%s#8"><img border="0" src="%s/img/smallup.gif" title="Move up"></a>""" % (CFG_SITE_URL, colID, ln, fldID, res[i - 1][0], random.randint(0, 1000), CFG_SITE_URL)
            else:
                move += "&nbsp;&nbsp;&nbsp;&nbsp;"
            move += "</td><td>"
            i += 1
            if i != len(res):
                move += """<a href="%s/admin/websearch/websearchadmin.py/switchfldscore?colID=%s&amp;ln=%s&amp;id_1=%s&amp;id_2=%s&amp;fmeth=soo&amp;rand=%s#8"><img border="0" src="%s/img/smalldown.gif" title="Move down"></a>""" % (CFG_SITE_URL, colID, ln, fldID, res[i][0], random.randint(0, 1000), CFG_SITE_URL)
            move += """</td></tr></table>"""

            actions.append([move, fld_dict[int(fldID)]])

            for col in [(('Remove sort option', 'removefield'),)]:
                actions[-1].append('<a href="%s/admin/websearch/websearchadmin.py/%s?colID=%s&amp;ln=%s&amp;fldID=%s&amp;fmeth=soo#8.4">%s</a>' % (CFG_SITE_URL, col[0][1], colID, ln, fldID, col[0][0]))
                for (str, function) in col[1:]:
                    actions[-1][-1] += ' / <a href="%s/admin/websearch/websearchadmin.py/%s?colID=%s&amp;ln=%s&amp;fldID=%s&amp;fmeth=soo#8.5">%s</a>' % (CFG_SITE_URL, function, colID, ln, fldID, str)
        output += tupletotable(header=header, tuple=actions)
    else:
        output += """No sort options exists for this collection"""

    output += content

    body = [output]

    if callback:
        return perform_editcollection(colID, ln, "perform_showsortoptions", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_showsearchfields(colID, ln, callback='yes', content='', confirm=-1):
    """show the search fields of this collection.."""

    colID = int(colID)
    col_dict = dict(get_def_name('', "collection"))
    fld_dict = dict(get_def_name('', "field"))
    fld_type = get_sort_nametypes()

    subtitle = """<a name="6">6. Modify search fields for collection '%s'</a>&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/websearch-admin-guide#3.6">?</a>]</small>""" % (col_dict[colID], CFG_SITE_URL)
    output = """<dl>
     <dt>Field actions (not related to this collection)</dt>
     <dd>Go to the BibIndex interface to modify the available search fields</dd>
     <dt>Collection specific actions
     <dd><a href="addexistingfield?colID=%s&amp;ln=%s&amp;fmeth=sew#6.2">Add search field to collection</a></dd>
     <dd><a href="rearrangefield?colID=%s&amp;ln=%s&amp;fmeth=sew#6.2">Order search fields alphabetically</a></dd>
    </dl>
    """  % (colID, ln, colID, ln)

    header = ['', 'Search field', 'Actions']

    actions = []
    sitelangs = get_languages()
    lang = dict(sitelangs)

    fld_type_list = fld_type.items()

    if len(get_col_fld(colID, 'sew')) > 0:
        res = get_col_fld(colID, 'sew')
        i = 0

        for (fldID, fldvID, stype, score, score_fieldvalue) in res:
            move = """<table cellspacing="1" cellpadding="0" border="0"><tr><td>"""
            if i != 0:
                move += """<a href="%s/admin/websearch/websearchadmin.py/switchfldscore?colID=%s&amp;ln=%s&amp;id_1=%s&amp;id_2=%s&amp;fmeth=sew&amp;rand=%s#6"><img border="0" src="%s/img/smallup.gif" title="Move up"></a>""" % (CFG_SITE_URL, colID, ln, fldID, res[i - 1][0], random.randint(0, 1000), CFG_SITE_URL)
            else:
                move += "&nbsp;&nbsp;&nbsp;"
            move += "</td><td>"
            i += 1
            if i != len(res):
                move += '<a href="%s/admin/websearch/websearchadmin.py/switchfldscore?colID=%s&amp;ln=%s&amp;id_1=%s&amp;id_2=%s&amp;fmeth=sew&amp;rand=%s#6"><img border="0" src="%s/img/smalldown.gif" title="Move down"></a>' % (CFG_SITE_URL, colID, ln, fldID, res[i][0], random.randint(0, 1000), CFG_SITE_URL)
            move += """</td></tr></table>"""

            actions.append([move, fld_dict[int(fldID)]])

            for col in [(('Remove search field', 'removefield'),)]:
                actions[-1].append('<a href="%s/admin/websearch/websearchadmin.py/%s?colID=%s&amp;ln=%s&amp;fldID=%s&amp;fmeth=sew#6.4">%s</a>' % (CFG_SITE_URL, col[0][1], colID, ln, fldID, col[0][0]))
                for (str, function) in col[1:]:
                    actions[-1][-1] += ' / <a href="%s/admin/websearch/websearchadmin.py/%s?colID=%s&amp;ln=%s&amp;fldID=%s#6.5">%s</a>' % (CFG_SITE_URL, function, colID, ln, fldID, str)
        output += tupletotable(header=header, tuple=actions)
    else:
        output += """No search fields exists for this collection"""

    output += content

    body = [output]

    if callback:
        return perform_editcollection(colID, ln, "perform_showsearchfields", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_showsearchoptions(colID, ln, callback='yes', content='', confirm=-1):
    """show the sort and search options of this collection.."""

    colID = int(colID)
    col_dict = dict(get_def_name('', "collection"))
    fld_dict = dict(get_def_name('', "field"))
    fld_type = get_sort_nametypes()

    subtitle = """<a name="7">7. Modify search options for collection '%s'</a>&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/websearch-admin-guide#3.7">?</a>]</small>""" % (col_dict[colID], CFG_SITE_URL)
    output = """<dl>
     <dt>Field actions (not related to this collection)</dt>
     <dd>Go to the BibIndex interface to modify the available search options</dd>
     <dt>Collection specific actions
     <dd><a href="addexistingfield?colID=%s&amp;ln=%s&amp;fmeth=seo#7.2">Add search option to collection</a></dd>
     <dd><a href="rearrangefield?colID=%s&amp;ln=%s&amp;fmeth=seo#7.2">Order search options alphabetically</a></dd>
    </dl>
    """  % (colID, ln, colID, ln)

    header = ['', 'Search option', 'Actions']

    actions = []
    sitelangs = get_languages()
    lang = dict(sitelangs)

    fld_type_list = fld_type.items()
    fld_distinct = run_sql("SELECT distinct(id_field) FROM collection_field_fieldvalue WHERE type='seo' AND id_collection=%s ORDER by score desc", (colID, ))

    if len(fld_distinct) > 0:
        i = 0
        for (id) in fld_distinct:
            fldID = id[0]
            col_fld = get_col_fld(colID, 'seo', fldID)

            move = ""
            if i != 0:
                move += """<a href="%s/admin/websearch/websearchadmin.py/switchfldscore?colID=%s&amp;ln=%s&amp;id_1=%s&amp;id_2=%s&amp;fmeth=seo&amp;rand=%s#7"><img border="0" src="%s/img/smallup.gif" title="Move up"></a>""" % (CFG_SITE_URL, colID, ln, fldID, fld_distinct[i - 1][0], random.randint(0, 1000), CFG_SITE_URL)
            else:
                move += "&nbsp;&nbsp;&nbsp;"

            i += 1
            if i != len(fld_distinct):
                move += '<a href="%s/admin/websearch/websearchadmin.py/switchfldscore?colID=%s&amp;ln=%s&amp;id_1=%s&amp;id_2=%s&amp;fmeth=seo&amp;rand=%s#7"><img border="0" src="%s/img/smalldown.gif" title="Move down"></a>' % (CFG_SITE_URL, colID, ln, fldID, fld_distinct[i][0], random.randint(0, 1000), CFG_SITE_URL)

            actions.append([move, "%s" % fld_dict[fldID]])
            for col in [(('Modify values', 'modifyfield'), ('Remove search option', 'removefield'),)]:
                actions[-1].append('<a href="%s/admin/websearch/websearchadmin.py/%s?colID=%s&amp;ln=%s&amp;fldID=%s#7.3">%s</a>' % (CFG_SITE_URL, col[0][1], colID, ln, fldID, col[0][0]))
                for (str, function) in col[1:]:
                    actions[-1][-1] += ' / <a href="%s/admin/websearch/websearchadmin.py/%s?colID=%s&amp;ln=%s&amp;fldID=%s&amp;fmeth=seo#7.3">%s</a>' % (CFG_SITE_URL, function, colID, ln, fldID, str)
        output += tupletotable(header=header, tuple=actions)
    else:
        output += """No search options exists for this collection"""

    output += content

    body = [output]

    if callback:
        return perform_editcollection(colID, ln, "perform_showsearchoptions", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)


def perform_modifyfield(colID, fldID, fldvID='', ln=CFG_SITE_LANG, content='', callback='yes', confirm=0):
    """Modify the fieldvalues for a field"""

    colID = int(colID)
    col_dict = dict(get_def_name('', "collection"))
    fld_dict = dict(get_def_name('', "field"))
    fld_type = get_sort_nametypes()
    fldID = int(fldID)

    subtitle = """<a name="7.3">Modify values for field '%s'</a>""" % (fld_dict[fldID])
    output = """<dl>
     <dt>Value specific actions
     <dd><a href="addexistingfieldvalue?colID=%s&amp;ln=%s&amp;fldID=%s#7.4">Add existing value to search option</a></dd>
     <dd><a href="addnewfieldvalue?colID=%s&amp;ln=%s&amp;fldID=%s#7.4">Add new value to search option</a></dd>
     <dd><a href="rearrangefieldvalue?colID=%s&amp;ln=%s&amp;fldID=%s#7.4">Order values alphabetically</a></dd>
    </dl>
    """  % (colID, ln, fldID, colID, ln, fldID, colID, ln, fldID)
    header = ['', 'Value name', 'Actions']

    actions = []
    sitelangs = get_languages()
    lang = dict(sitelangs)

    fld_type_list = fld_type.items()
    col_fld = list(get_col_fld(colID, 'seo', fldID))
    if len(col_fld) == 1 and col_fld[0][1] is None:
        output += """<b><span class="info">No values added for this search option yet</span></b>"""
    else:
        j = 0
        for (fldID, fldvID, stype, score, score_fieldvalue) in col_fld:
            fieldvalue = get_fld_value(fldvID)
            move = ""
            if j != 0:
                move += """<a href="%s/admin/websearch/websearchadmin.py/switchfldvaluescore?colID=%s&amp;ln=%s&amp;id_1=%s&amp;id_fldvalue_1=%s&amp;id_fldvalue_2=%s&amp;rand=%s#7.3"><img border="0" src="%s/img/smallup.gif" title="Move up"></a>""" % (CFG_SITE_URL, colID, ln, fldID, fldvID, col_fld[j - 1][1], random.randint(0, 1000), CFG_SITE_URL)
            else:
                move += "&nbsp;&nbsp;&nbsp;"

            j += 1
            if j != len(col_fld):
                move += """<a href="%s/admin/websearch/websearchadmin.py/switchfldvaluescore?colID=%s&amp;ln=%s&amp;id_1=%s&amp;id_fldvalue_1=%s&amp;id_fldvalue_2=%s&amp;rand=%s#7.3"><img border="0" src="%s/img/smalldown.gif" title="Move down"></a>""" % (CFG_SITE_URL, colID, ln, fldID, fldvID, col_fld[j][1], random.randint(0, 1000), CFG_SITE_URL)

            if fieldvalue[0][1] != fieldvalue[0][2] and fldvID is not None:
                actions.append([move, "%s - %s" % (fieldvalue[0][1], fieldvalue[0][2])])
            elif fldvID is not None:
                actions.append([move, "%s" % fieldvalue[0][1]])

            move = ''
            for col in [(('Modify value', 'modifyfieldvalue'), ('Remove value', 'removefieldvalue'),)]:
                actions[-1].append('<a href="%s/admin/websearch/websearchadmin.py/%s?colID=%s&amp;ln=%s&amp;fldID=%s&amp;fldvID=%s&amp;fmeth=seo#7.4">%s</a>' % (CFG_SITE_URL, col[0][1], colID, ln, fldID, fldvID, col[0][0]))
                for (str, function) in col[1:]:
                    actions[-1][-1] += ' / <a href="%s/admin/websearch/websearchadmin.py/%s?colID=%s&amp;ln=%s&amp;fldID=%s&amp;fldvID=%s#7.4">%s</a>' % (CFG_SITE_URL, function, colID, ln, fldID, fldvID, str)
        output += tupletotable(header=header, tuple=actions)

    output += content

    body = [output]

    output = "<br />" + addadminbox(subtitle, body)
    if len(col_fld) == 0:
        output = content
    return perform_showsearchoptions(colID, ln, content=output)

def perform_showoutputformats(colID, ln, callback='yes', content='', confirm=-1):
    """shows the outputformats of the current collection
    colID - the collection id."""

    colID = int(colID)
    col_dict = dict(get_def_name('', "collection"))

    subtitle = """<a name="10">10. Modify output formats for collection '%s'</a>&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/websearch-admin-guide#3.10">?</a>]</small>""" % (col_dict[colID], CFG_SITE_URL)
    output = """
    <dl>
     <dt>Output format actions (not specific to the chosen collection)
     <dd>Go to the BibFormat interface to modify</dd>
     <dt>Collection specific actions
     <dd><a href="addexistingoutputformat?colID=%s&amp;ln=%s#10.2">Add existing output format to collection</a></dd>
    </dl>
    """  % (colID, ln)

    header = ['', 'Code', 'Output format', 'Actions']
    actions = []

    col_fmt = get_col_fmt(colID)
    fmt_dict = dict(get_def_name('', "format"))

    i = 0
    if len(col_fmt) > 0:
        for (id_format, colID_fld, code, score) in col_fmt:
            move = """<table cellspacing="1" cellpadding="0" border="0"><tr><td>"""
            if i != 0:
                move += """<a href="%s/admin/websearch/websearchadmin.py/switchfmtscore?colID=%s&amp;ln=%s&amp;type=format&amp;id_1=%s&amp;id_2=%s&amp;rand=%s#10"><img border="0" src="%s/img/smallup.gif" title="Move format up"></a>""" % (CFG_SITE_URL, colID, ln, id_format, col_fmt[i - 1][0], random.randint(0, 1000), CFG_SITE_URL)
            else:
                move += "&nbsp;&nbsp;&nbsp;"
            move += "</td><td>"
            i += 1
            if i != len(col_fmt):
                move += '<a href="%s/admin/websearch/websearchadmin.py/switchfmtscore?colID=%s&amp;ln=%s&amp;type=format&amp;id_1=%s&amp;id_2=%s&amp;rand=%s#10"><img border="0" src="%s/img/smalldown.gif" title="Move format down"></a>' % (CFG_SITE_URL, colID, ln, id_format, col_fmt[i][0], random.randint(0, 1000), CFG_SITE_URL)
            move += """</td></tr></table>"""

            actions.append([move, code, fmt_dict[int(id_format)]])
            for col in [(('Remove', 'removeoutputformat'),)]:
                actions[-1].append('<a href="%s/admin/websearch/websearchadmin.py/%s?colID=%s&amp;ln=%s&amp;fmtID=%s#10">%s</a>' % (CFG_SITE_URL, col[0][1], colID, ln, id_format, col[0][0]))
                for (str, function) in col[1:]:
                    actions[-1][-1] += ' / <a href="%s/admin/websearch/websearchadmin.py/%s?colID=%s&amp;ln=%s&amp;fmtID=%s#10">%s</a>' % (CFG_SITE_URL, function, colID, ln, id_format, str)
        output += tupletotable(header=header, tuple=actions)
    else:
        output += """No output formats exists for this collection"""
    output += content

    body = [output]

    if callback:
        return perform_editcollection(colID, ln, "perform_showoutputformats", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def external_collections_build_select(colID, external_collection):
    output = '<select name="state" class="admin_w200">'

    if external_collection.parser:
        max_state = 4
    else:
        max_state = 2

    num_selected = external_collection_get_state(external_collection, colID)

    for num in range(max_state):
        state_name = CFG_EXTERNAL_COLLECTION_STATES_NAME[num]
        if num == num_selected:
            selected = ' selected'
        else:
            selected = ''
        output += '<option value="%(num)d"%(selected)s>%(state_name)s</option>' % {'num': num, 'selected': selected, 'state_name': state_name}

    output += '</select>\n'
    return output

def perform_manage_external_collections(colID, ln, callback='yes', content='', confirm=-1):
    """Show the interface to configure external collections to the user."""

    colID = int(colID)

    subtitle = """<a name="11">11. Configuration of related external collections</a>
    &nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/websearch-admin-guide#3.11">?</a>]</small>""" % CFG_SITE_URL
    output = '<form action="update_external_collections" method="POST"><input type="hidden" name="colID" value="%(colID)d">' % {'colID': colID}

    table_header = ['External collection', 'Mode', 'Apply also to daughter collections?']
    table_content = []

    external_collections = external_collection_sort_engine_by_name(external_collections_dictionary.values())
    for external_collection in external_collections:
        collection_name = external_collection.name
        select = external_collections_build_select(colID, external_collection)
        recurse = '<input type=checkbox name="recurse" value="%(collection_name)s">' % {'collection_name': collection_name}
        table_content.append([collection_name, select, recurse])

    output += tupletotable(header=table_header, tuple=table_content)

    output += '<input class="adminbutton" type="submit" value="Modify"/>'
    output += '</form>'

    return addadminbox(subtitle, [output])

def perform_update_external_collections(colID, ln, state_list, recurse_list):
    colID = int(colID)
    changes = []
    output = ""

    if not state_list:
        return 'Warning : No state found.<br />' + perform_manage_external_collections(colID, ln)

    external_collections = external_collection_sort_engine_by_name(external_collections_dictionary.values())

    if len(external_collections) != len(state_list):
        return 'Warning : Size of state_list different from external_collections!<br />' + perform_manage_external_collections(colID, ln)

    for (external_collection, state) in zip(external_collections, state_list):
        state = int(state)
        collection_name = external_collection.name
        recurse = recurse_list and collection_name in recurse_list
        oldstate = external_collection_get_state(external_collection, colID)
        if oldstate != state or recurse:
            changes += external_collection_get_update_state_list(external_collection, colID, state, recurse)

    external_collection_apply_changes(changes)

    return output + '<br /><br />' + perform_manage_external_collections(colID, ln)

def perform_showdetailedrecordoptions(colID, ln, callback='yes', content='', confirm=-1):
    """Show the interface to configure detailed record page to the user."""

    colID = int(colID)

    subtitle = """<a name="12">12. Configuration of detailed record page</a>
    &nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/websearch-admin-guide#3.12">?</a>]</small>""" % CFG_SITE_URL
    output = '''<form action="update_detailed_record_options" method="post">
    <table><tr><td>
    <input type="hidden" name="colID" value="%(colID)d">
    <dl>
    <dt><b>Show tabs:</b></dt>
    <dd>
    ''' % {'colID': colID}

    for (tab_id, tab_info) in get_detailed_page_tabs(colID).iteritems():
        if tab_id == 'comments' and \
           not CFG_WEBCOMMENT_ALLOW_REVIEWS and \
           not CFG_WEBCOMMENT_ALLOW_COMMENTS:
            continue
        check = ''
        output += '''<input type="checkbox" id="id%(tabid)s" name="tabs" value="%(tabid)s" %(check)s />
        <label for="id%(tabid)s">&nbsp;%(label)s</label><br />
        ''' % {'tabid':tab_id,
               'check':((tab_info['visible'] and 'checked="checked"') or ''),
               'label':tab_info['label']}

    output += '</dd></dl></td><td>'
    output += '</td></tr></table><input class="adminbutton" type="submit" value="Modify"/>'
    output += '''<input type="checkbox" id="recurse" name="recurse" value="1" />
        <label for="recurse">&nbsp;Also apply to subcollections</label>'''
    output += '</form>'

    return addadminbox(subtitle, [output])

def perform_update_detailed_record_options(colID, ln, tabs, recurse):
    """Update the preferences for the tab to show/hide in the detailed record page."""
    colID = int(colID)
    changes = []
    output = '<b><span class="info">Operation successfully completed.</span></b>'


    if '' in tabs:
        tabs.remove('')
        tabs.append('metadata')

    def update_settings(colID, tabs, recurse):
        run_sql("DELETE FROM collectiondetailedrecordpagetabs WHERE id_collection=%s", (colID, ))
        run_sql("REPLACE INTO collectiondetailedrecordpagetabs" + \
                " SET id_collection=%s, tabs=%s", (colID, ';'.join(tabs)))
 ##        for enabled_tab in tabs:
##             run_sql("REPLACE INTO collectiondetailedrecordpagetabs" + \
##                 " SET id_collection='%s', tabs='%s'" % (colID, ';'.join(tabs)))
        if recurse:
            for descendant_id in get_collection_descendants(colID):
                update_settings(descendant_id, tabs, recurse)

    update_settings(colID, tabs, recurse)
##     for colID in colIDs:
##         run_sql("DELETE FROM collectiondetailedrecordpagetabs WHERE id_collection='%s'" % colID)
##         for enabled_tab in tabs:
##             run_sql("REPLACE INTO collectiondetailedrecordpagetabs" + \
##                 " SET id_collection='%s', tabs='%s'" % (colID, ';'.join(tabs)))

    #if callback:
    return perform_editcollection(colID, ln, "perform_modifytranslations",
                                  '<br /><br />' + output + '<br /><br />' + \
                                  perform_showdetailedrecordoptions(colID, ln))
    #else:
    #    return addadminbox(subtitle, body)
    #return output + '<br /><br />' + perform_showdetailedrecordoptions(colID, ln)


def perform_addexistingoutputformat(colID, ln, fmtID=-1, callback='yes', confirm=-1):
    """form to add an existing output format to a collection.
    colID - the collection the format should be added to
    fmtID - the format to add."""

    subtitle = """<a name="10.2"></a>Add existing output format to collection"""
    output  = ""

    if fmtID not in [-1, "-1"] and confirm in [1, "1"]:
        ares = add_col_fmt(colID, fmtID)
    colID = int(colID)
    res = get_def_name('', "format")
    fmt_dict = dict(res)
    col_dict = dict(get_def_name('', "collection"))
    col_fmt = get_col_fmt(colID)
    col_fmt = dict(map(lambda x: (x[0], x[2]), col_fmt))

    if len(res) > 0:
        text  = """
        <span class="adminlabel">Output format</span>
        <select name="fmtID" class="admin_w200">
        <option value="-1">- Select output format -</option>
        """
        for (id, name) in res:
            if not col_fmt.has_key(id):
                text += """<option value="%s" %s>%s</option>
                """ % (id, id  == int(fmtID) and 'selected="selected"' or '', name)
        text += """</select><br />
        """
        output += createhiddenform(action="addexistingoutputformat#10.2",
                                   text=text,
                                   button="Add",
                                   colID=colID,
                                   ln=ln,
                                   confirm=1)
    else:
        output  = """No existing output formats to add, please create a new one."""

    if fmtID not in [-1, "-1"] and confirm in [1, "1"]:
        output += write_outcome(ares)
    elif fmtID in [-1, "-1"] and confirm not in [-1, "-1"]:
        output  += """<b><span class="info">Please select output format.</span></b>"""

    body = [output]

    output = "<br />" + addadminbox(subtitle, body)
    return perform_showoutputformats(colID, ln, content=output)

def perform_deleteoutputformat(colID, ln, fmtID=-1, callback='yes', confirm=-1):
    """form to delete an output format not in use.
    colID - the collection id of the current collection.
    fmtID - the format id to delete."""

    subtitle = """<a name="10.3"></a>Delete an unused output format"""
    output  = """
    <dl>
     <dd>Deleting an output format will also delete the translations associated.</dd>
    </dl>
    """

    colID = int(colID)
    if fmtID not in [-1, "-1"] and confirm in [1, "1"]:
        fmt_dict = dict(get_def_name('', "format"))
        old_colNAME = fmt_dict[int(fmtID)]
        ares = delete_fmt(int(fmtID))

    res = get_def_name('', "format")
    fmt_dict = dict(res)
    col_dict = dict(get_def_name('', "collection"))
    col_fmt = get_col_fmt()
    col_fmt = dict(map(lambda x: (x[0], x[2]), col_fmt))

    if len(res) > 0:
        text  = """
        <span class="adminlabel">Output format</span>
        <select name="fmtID" class="admin_w200">
        """
        text += """<option value="-1">- Select output format -"""
        for (id, name) in res:
            if not col_fmt.has_key(id):
                text += """<option value="%s" %s>%s""" % (id, id  == int(fmtID) and 'selected="selected"' or '', name)
            text += "</option>"
        text += """</select><br />"""

        output += createhiddenform(action="deleteoutputformat#10.3",
                                   text=text,
                                   button="Delete",
                                   colID=colID,
                                   ln=ln,
                                   confirm=0)

    if fmtID not in [-1, "-1"]:
        fmtID = int(fmtID)
        if confirm in [0, "0"]:
            text = """<b>Do you want to delete the output format '%s'.</b>
            """ % fmt_dict[fmtID]
            output += createhiddenform(action="deleteoutputformat#10.3",
                                       text=text,
                                       button="Confirm",
                                       colID=colID,
                                       fmtID=fmtID,
                                       ln=ln,
                                       confirm=1)

        elif confirm in [1, "1"]:
            output += write_outcome(ares)
    elif confirm not in [-1, "-1"]:
        output  += """<b><span class="info">Choose a output format to delete.</span></b>
        """
    body = [output]

    output = "<br />" + addadminbox(subtitle, body)
    return perform_showoutputformats(colID, ln, content=output)

def perform_removeoutputformat(colID, ln, fmtID='', callback='yes', confirm=0):
    """form to remove an output format from a collection.
    colID - the collection id of the current collection.
    fmtID - the format id.
    """

    subtitle = """<a name="10.5"></a>Remove output format"""
    output  = ""

    col_dict = dict(get_def_name('', "collection"))
    fmt_dict = dict(get_def_name('', "format"))

    if colID and fmtID:
        colID = int(colID)
        fmtID = int(fmtID)

        if confirm in ["0", 0]:
            text = """Do you want to remove the output format '%s' from the collection '%s'.""" % (fmt_dict[fmtID], col_dict[colID])
            output += createhiddenform(action="removeoutputformat#10.5",
                                       text=text,
                                       button="Confirm",
                                       colID=colID,
                                       fmtID=fmtID,
                                       confirm=1)
        elif confirm in ["1", 1]:
            res = remove_fmt(colID, fmtID)
            output += write_outcome(res)

    body = [output]

    output = "<br />" + addadminbox(subtitle, body)
    return perform_showoutputformats(colID, ln, content=output)

def perform_index(colID=1, ln=CFG_SITE_LANG, mtype='', content='', confirm=0):
    """The index method, calling methods to show the collection tree, create new collections and add collections to tree.
    """

    subtitle = "Overview"
    colID = int(colID)
    col_dict = dict(get_def_name('', "collection"))

    output = ""
    fin_output = ""
    if not col_dict.has_key(1):
        res = add_col(CFG_SITE_NAME, '')
        if res:
            fin_output += """<b><span class="info">Created root collection.</span></b><br />"""
        else:
            return "Cannot create root collection, please check database."
    if CFG_SITE_NAME != run_sql("SELECT name from collection WHERE id=1")[0][0]:
        res = run_sql("update collection set name=%s where id=1", (CFG_SITE_NAME, ))
        if res:
            fin_output += """<b><span class="info">The name of the root collection has been modified to be the same as the %(sitename)s installation name given prior to installing %(sitename)s.</span><b><br />""" % {'sitename' : CFG_SITE_NAME}
        else:
            return "Error renaming root collection."
    fin_output += """
    <table>
    <tr>
    <td>0.&nbsp;<small><a href="%s/admin/websearch/websearchadmin.py?colID=%s&amp;ln=%s&amp;mtype=perform_showall">Show all</a></small></td>
    <td>1.&nbsp;<small><a href="%s/admin/websearch/websearchadmin.py?colID=%s&amp;ln=%s&amp;mtype=perform_addcollection">Create new collection</a></small></td>
    <td>2.&nbsp;<small><a href="%s/admin/websearch/websearchadmin.py?colID=%s&amp;ln=%s&amp;mtype=perform_addcollectiontotree">Attach collection to tree</a></small></td>
    <td>3.&nbsp;<small><a href="%s/admin/websearch/websearchadmin.py?colID=%s&amp;ln=%s&amp;mtype=perform_modifycollectiontree">Modify collection tree</a></small></td>
    <td>4.&nbsp;<small><a href="%s/admin/websearch/websearchadmin.py?colID=%s&amp;ln=%s&amp;mtype=perform_checkwebcollstatus">Webcoll Status</a></small></td>
    </tr><tr>
    <td>5.&nbsp;<small><a href="%s/admin/websearch/websearchadmin.py?colID=%s&amp;ln=%s&amp;mtype=perform_checkcollectionstatus">Collection Status</a></small></td>
    <td>6.&nbsp;<small><a href="%s/admin/websearch/websearchadmin.py?colID=%s&amp;ln=%s&amp;mtype=perform_checkexternalcollections">Check external collections</a></small></td>
    <td>7.&nbsp;<small><a href="%s/admin/websearch/websearchadmin.py?colID=%s&amp;ln=%s&amp;mtype=perform_checksearchservices">Search services</a></small></td>
    <td>8.&nbsp;<small><a href="%s/help/admin/websearch-admin-guide?ln=%s">Guide</a></small></td>
    </tr>
    </table>
    """ % (CFG_SITE_URL, colID, ln, CFG_SITE_URL, colID, ln, CFG_SITE_URL, colID, ln, CFG_SITE_URL, colID, ln, CFG_SITE_URL, colID, ln, CFG_SITE_URL, colID, ln, CFG_SITE_URL, colID, ln, CFG_SITE_URL, colID, ln, CFG_SITE_URL, ln)

    if mtype == "":
        fin_output += """<br /><br /><b><span class="info">To manage the collections, select an item from the menu.</span><b><br />"""

    if mtype == "perform_addcollection" and content:
        fin_output += content
    elif mtype == "perform_addcollection" or mtype == "perform_showall":
        fin_output += perform_addcollection(colID=colID, ln=ln, callback='')
        fin_output += "<br />"

    if mtype == "perform_addcollectiontotree" and content:
        fin_output += content
    elif mtype == "perform_addcollectiontotree" or mtype == "perform_showall":
        fin_output += perform_addcollectiontotree(colID=colID, ln=ln, callback='')
        fin_output += "<br />"

    if mtype == "perform_modifycollectiontree" and content:
        fin_output += content
    elif mtype == "perform_modifycollectiontree" or mtype == "perform_showall":
        fin_output += perform_modifycollectiontree(colID=colID, ln=ln, callback='')
        fin_output += "<br />"

    if mtype == "perform_checkwebcollstatus" and content:
        fin_output += content
    elif mtype == "perform_checkwebcollstatus" or mtype == "perform_showall":
        fin_output += perform_checkwebcollstatus(colID, ln, callback='')

    if mtype == "perform_checkcollectionstatus" and content:
        fin_output += content
    elif mtype == "perform_checkcollectionstatus" or mtype == "perform_showall":
        fin_output += perform_checkcollectionstatus(colID, ln, callback='')

    if mtype == "perform_checkexternalcollections" and content:
        fin_output += content
    elif mtype == "perform_checkexternalcollections" or mtype == "perform_showall":
        fin_output += perform_checkexternalcollections(colID, ln, callback='')

    if mtype == "perform_checksearchservices" and content:
        fin_output += content
    elif mtype == "perform_checksearchservices" or mtype == "perform_showall":
        fin_output += perform_checksearchservices(colID, ln, callback='')

    body = [fin_output]
    body = [fin_output]

    return addadminbox('<b>Menu</b>', body)

def show_coll_not_in_tree(colID, ln, col_dict):
    """Returns collections not in tree"""

    tree = get_col_tree(colID)
    in_tree = {}
    output = "These collections are not in the tree, and should be added:<br />"
    for (id, up, down, dad, reltype) in tree:
        in_tree[id] = 1
        in_tree[dad] = 1
    res = run_sql("SELECT id from collection")
    if len(res) != len(in_tree):
        for id in res:
            if not in_tree.has_key(id[0]):
                output += """<a href="%s/admin/websearch/websearchadmin.py/editcollection?colID=%s&amp;ln=%s" title="Edit collection">%s</a> ,
                """ % (CFG_SITE_URL, id[0], ln, col_dict[id[0]])
        output += "<br /><br />"
    else:
        output = ""
    return output

def create_colltree(tree, col_dict, colID, ln, move_from='', move_to='', rtype='', edit=''):
    """Creates the presentation of the collection tree, with the buttons for modifying it.
    tree - the tree to present, from get_tree()
    col_dict - the name of the collections in a dictionary
    colID - the collection id to start with
    move_from - if a collection to be moved has been chosen
    move_to - the collection which should be set as father of move_from
    rtype - the type of the tree, regular or virtual
    edit - if the method should output the edit buttons."""

    if move_from:
        move_from_rtype = move_from[0]
        move_from_id = int(move_from[1:len(move_from)])
        tree_from = get_col_tree(colID, move_from_rtype)
        tree_to = get_col_tree(colID, rtype)

    tables = 0
    tstack = []
    i = 0

    text = """
    <table border ="0" cellspacing="0" cellpadding="0">"""
    for i in range(0, len(tree)):
        id_son = tree[i][0]
        up = tree[i][1]
        down = tree[i][2]
        dad = tree[i][3]
        reltype = tree[i][4]
        tmove_from = ""

        j = i
        while j > 0:
            j = j - 1
            try:
                if tstack[j][1] == dad:
                    table = tstack[j][2]
                    for k in range(0, tables - table):
                        tables = tables - 1
                        text += """</table></td></tr>
                        """
                    break
            except StandardError, e:
                pass
        text += """<tr><td>
        """

        if i > 0 and tree[i][1] == 0:
            tables = tables + 1
            text += """</td><td></td><td></td><td></td><td><table border="0" cellspacing="0" cellpadding="0"><tr><td>
            """

        if i == 0:
            tstack.append((id_son, dad, 1))
        else:
            tstack.append((id_son, dad, tables))

        if up == 1 and edit:
            text += """<a href="%s/admin/websearch/websearchadmin.py/modifycollectiontree?colID=%s&amp;ln=%s&amp;move_up=%s&amp;rtype=%s#%s"><img border="0" src="%s/img/smallup.gif" title="Move collection up"></a>""" % (CFG_SITE_URL, colID, ln, i, rtype, tree[i][0], CFG_SITE_URL)
        else:
            text += """&nbsp;"""
        text += "</td><td>"

        if down == 1 and edit:
            text += """<a href="%s/admin/websearch/websearchadmin.py/modifycollectiontree?colID=%s&amp;ln=%s&amp;move_down=%s&amp;rtype=%s#%s"><img border="0" src="%s/img/smalldown.gif" title="Move collection down"></a>""" % (CFG_SITE_URL, colID, ln, i, rtype, tree[i][0], CFG_SITE_URL)
        else:
            text += """&nbsp;"""
        text += "</td><td>"

        if edit:
            if move_from and move_to:
                tmove_from = move_from
                move_from = ''
            if not (move_from == "" and i == 0) and not (move_from != "" and int(move_from[1:len(move_from)]) == i and rtype == move_from[0]):
                check = "true"
                if move_from:
                    #if tree_from[move_from_id][0] == tree_to[i][0] or not check_col(tree_to[i][0], tree_from[move_from_id][0]):
                    #    check = ''
                    #elif not check_col(tree_to[i][0], tree_from[move_from_id][0]):
                    #    check = ''
                    #if not check and (tree_to[i][0] == 1 and tree_from[move_from_id][3] == tree_to[i][0] and move_from_rtype != rtype):
                    #    check = "true"
                    if check:
                        text += """<a href="%s/admin/websearch/websearchadmin.py/modifycollectiontree?colID=%s&amp;ln=%s&amp;move_from=%s&amp;move_to=%s%s&amp;rtype=%s#tree"><img border="0" src="%s/img/move_to.gif" title="Move '%s' to '%s'"></a>
                """ % (CFG_SITE_URL, colID, ln, move_from, rtype, i, rtype, CFG_SITE_URL,  col_dict[tree_from[int(move_from[1:len(move_from)])][0]], col_dict[tree_to[i][0]])
                else:
                    try:
                        text += """<a href="%s/admin/websearch/websearchadmin.py/modifycollectiontree?colID=%s&amp;ln=%s&amp;move_from=%s%s&amp;rtype=%s#%s"><img border="0" src="%s/img/move_from.gif" title="Move '%s' from this location."></a>""" % (CFG_SITE_URL, colID, ln, rtype, i, rtype, tree[i][0], CFG_SITE_URL, col_dict[tree[i][0]])
                    except KeyError:
                        pass
            else:
                text += """<img border="0" src="%s/img/white_field.gif">
                """ % CFG_SITE_URL
        else:
            text += """<img border="0" src="%s/img/white_field.gif">
                """ % CFG_SITE_URL

        text += """
        </td>
        <td>"""

        if edit:
            try:
                text += """<a href="%s/admin/websearch/websearchadmin.py/modifycollectiontree?colID=%s&amp;ln=%s&amp;delete=%s&amp;rtype=%s#%s"><img border="0" src="%s/img/iconcross.gif" title="Remove colletion from tree"></a>""" % (CFG_SITE_URL, colID, ln, i, rtype, tree[i][0], CFG_SITE_URL)
            except KeyError:
                pass
        elif i != 0:
            text += """<img border="0" src="%s/img/white_field.gif">
        """ % CFG_SITE_URL

        text += """</td><td>
        """

        if tmove_from:
            move_from = tmove_from

        try:
            text += """<a name="%s"></a>%s<a href="%s/admin/websearch/websearchadmin.py/editcollection?colID=%s&amp;ln=%s" title="Edit collection">%s</a>%s%s%s""" % (tree[i][0], (reltype=="v" and '<i>' or ''), CFG_SITE_URL, tree[i][0], ln, col_dict[id_son], (move_to=="%s%s" %(rtype, i) and '&nbsp;<img border="0" src="%s/img/move_to.gif">' % CFG_SITE_URL or ''), (move_from=="%s%s" % (rtype, i) and '&nbsp;<img border="0" src="%s/img/move_from.gif">' % CFG_SITE_URL or ''), (reltype=="v" and '</i>' or ''))
        except KeyError:
            pass

        text += """</td></tr>
        """

    while tables > 0:
        text += """</table></td></tr>
        """
        tables = tables - 1
    text += """</table>"""

    return text

def perform_deletecollection(colID, ln, confirm=-1, callback='yes'):
    """form to delete a collection
    colID - id of collection
    """

    subtitle =''
    output  = """
    <span class="warning">
    <strong>
    <dl>
     <dt>WARNING:</dt>
     <dd>When deleting a collection, you also deletes all data related to the collection like translations, relations to other collections and information about which rank methods to use.
     <br />For more information, please go to the <a title="See guide" href="%s/help/admin/websearch-admin-guide">WebSearch guide</a> and read the section regarding deleting a collection.</dd>
    </dl>
    </strong>
    </span>
    """ % CFG_SITE_URL

    col_dict = dict(get_def_name('', "collection"))
    if colID != 1 and colID and col_dict.has_key(int(colID)):
        colID = int(colID)
        subtitle = """<a name="4">4. Delete collection '%s'</a>&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/websearch-admin-guide#3.4">?</a>]</small>""" % (col_dict[colID], CFG_SITE_URL)
        res = run_sql("SELECT id_dad,id_son,type,score from collection_collection WHERE id_dad=%s", (colID, ))
        res2 = run_sql("SELECT id_dad,id_son,type,score from collection_collection WHERE id_son=%s", (colID, ))

        if not res and not res2:
            if confirm in ["-1", -1]:
                text = """Do you want to delete this collection."""
                output += createhiddenform(action="deletecollection#4",
                                           text=text,
                                           colID=colID,
                                           button="Delete",
                                           confirm=0)
            elif confirm in ["0", 0]:
                text = """Are you sure you want to delete this collection."""
                output += createhiddenform(action="deletecollection#4",
                                           text=text,
                                           colID=colID,
                                           button="Confirm",
                                           confirm=1)
            elif confirm in ["1", 1]:
                result = delete_col(colID)
                if not result:
                    raise Exception
        else:
            output = """<b><span class="info">Can not delete a collection that is a part of the collection tree, remove collection from the tree and try again.</span></b>"""
    else:
        subtitle = """4. Delete collection"""
        output = """<b><span class="info">Not possible to delete the root collection</span></b>"""

    body = [output]

    if callback:
        return perform_editcollection(colID, ln, "perform_deletecollection", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_editcollection(colID=1, ln=CFG_SITE_LANG, mtype='', content=''):
    """interface to modify a collection. this method is calling other methods which again is calling this and sending back the output of the method.
    if callback, the method will call perform_editcollection, if not, it will just return its output.
    colID - id of the collection
    mtype - the method that called this method.
    content - the output from that method."""

    colID = int(colID)
    col_dict = dict(get_def_name('', "collection"))
    if not col_dict.has_key(colID):
        return """<b><span class="info">Collection deleted.</span></b>
        """

    fin_output = """
    <table>
    <tr>
    <td><b>Menu</b></td>
    </tr>
    <tr>
    <td>0.&nbsp;<small><a href="editcollection?colID=%s&amp;ln=%s">Show all</a></small></td>
    <td>1.&nbsp;<small><a href="editcollection?colID=%s&amp;ln=%s&amp;mtype=perform_modifydbquery">Modify collection query</a></small></td>
    <td>2.&nbsp;<small><a href="editcollection?colID=%s&amp;ln=%s&amp;mtype=perform_modifyrestricted">Modify access restrictions</a></small></td>
    <td>3.&nbsp;<small><a href="editcollection?colID=%s&amp;ln=%s&amp;mtype=perform_modifytranslations">Modify translations</a></small></td>
    <td>4.&nbsp;<small><a href="editcollection?colID=%s&amp;ln=%s&amp;mtype=perform_deletecollection">Delete collection</a></small></td>
    </tr><tr>
    <td>5.&nbsp;<small><a href="editcollection?colID=%s&amp;ln=%s&amp;mtype=perform_showportalboxes">Modify portalboxes</a></small></td>
    <td>6.&nbsp;<small><a href="editcollection?colID=%s&amp;ln=%s&amp;mtype=perform_showsearchfields#6">Modify search fields</a></small></td>
    <td>7.&nbsp;<small><a href="editcollection?colID=%s&amp;ln=%s&amp;mtype=perform_showsearchoptions#7">Modify search options</a></small></td>
    <td>8.&nbsp;<small><a href="editcollection?colID=%s&amp;ln=%s&amp;mtype=perform_showsortoptions#8">Modify sort options</a></small></td>
    <td>9.&nbsp;<small><a href="editcollection?colID=%s&amp;ln=%s&amp;mtype=perform_modifyrankmethods#9">Modify rank options</a></small></td>
    </tr><tr>
    <td>10.&nbsp;<small><a href="editcollection?colID=%s&amp;ln=%s&amp;mtype=perform_showoutputformats#10">Modify output formats</a></small></td>
    <td>11.&nbsp;<small><a href="editcollection?colID=%s&amp;ln=%s&amp;mtype=perform_manage_external_collections#11">Configuration of related external collections</a></small></td>
    <td>12.&nbsp;<small><a href="editcollection?colID=%s&amp;ln=%s&amp;mtype=perform_showdetailedrecordoptions#12">Detailed record page options</a></small></td>
    </tr>
    </table>
    """ % (colID, ln, colID, ln, colID, ln, colID, ln, colID, ln, colID, ln, colID, ln, colID, ln, colID, ln, colID, ln, colID, ln, colID, ln, colID, ln)

    if mtype == "perform_modifydbquery" and content:
        fin_output += content
    elif mtype == "perform_modifydbquery" or not mtype:
        fin_output += perform_modifydbquery(colID, ln, callback='')

    if mtype == "perform_modifyrestricted" and content:
        fin_output += content
    elif mtype == "perform_modifyrestricted" or not mtype:
        fin_output += perform_modifyrestricted(colID, ln, callback='')

    if mtype == "perform_modifytranslations" and content:
        fin_output += content
    elif mtype == "perform_modifytranslations" or not mtype:
        fin_output += perform_modifytranslations(colID, ln, callback='')

    if mtype == "perform_deletecollection" and content:
        fin_output += content
    elif mtype == "perform_deletecollection" or not mtype:
        fin_output += perform_deletecollection(colID, ln, callback='')

    if mtype == "perform_showportalboxes" and content:
        fin_output += content
    elif mtype == "perform_showportalboxes" or not mtype:
        fin_output += perform_showportalboxes(colID, ln, callback='')

    if mtype == "perform_showsearchfields" and content:
        fin_output += content
    elif mtype == "perform_showsearchfields" or not mtype:
        fin_output += perform_showsearchfields(colID, ln, callback='')

    if mtype == "perform_showsearchoptions" and content:
        fin_output += content
    elif mtype == "perform_showsearchoptions" or not mtype:
        fin_output += perform_showsearchoptions(colID, ln, callback='')

    if mtype == "perform_showsortoptions" and content:
        fin_output += content
    elif mtype == "perform_showsortoptions" or not mtype:
        fin_output += perform_showsortoptions(colID, ln, callback='')

    if mtype == "perform_modifyrankmethods" and content:
        fin_output += content
    elif  mtype == "perform_modifyrankmethods" or not mtype:
        fin_output += perform_modifyrankmethods(colID, ln, callback='')

    if mtype == "perform_showoutputformats" and content:
        fin_output += content
    elif mtype == "perform_showoutputformats" or not mtype:
        fin_output += perform_showoutputformats(colID, ln, callback='')

    if mtype == "perform_manage_external_collections" and content:
        fin_output += content
    elif mtype == "perform_manage_external_collections" or not mtype:
        fin_output += perform_manage_external_collections(colID, ln, callback='')

    if mtype == "perform_showdetailedrecordoptions" and content:
        fin_output += content
    elif mtype == "perform_showdetailedrecordoptions" or not mtype:
        fin_output += perform_showdetailedrecordoptions(colID, ln, callback='')

    return addadminbox("Overview of edit options for collection '%s'" % col_dict[colID],  [fin_output])

def perform_checkwebcollstatus(colID, ln, confirm=0, callback='yes'):
    """Check status of the collection tables with respect to the webcoll cache."""

    subtitle = """<a name="11"></a>Webcoll Status&nbsp;&nbsp;&nbsp;[<a href="%s/help/admin/websearch-admin-guide#5">?</a>]""" % CFG_SITE_URL
    output  = ""

    colID = int(colID)
    col_dict = dict(get_def_name('', "collection"))

    output += """<br /><b>Last updates:</b><br />"""
    collection_table_update_time = ""
    collection_web_update_time = ""

    collection_table_update_time = get_table_update_time('collection')
    output += "Collection table last updated: %s<br />" % collection_table_update_time

    try:
        file = open("%s/collections/last_updated" % CFG_CACHEDIR)
        collection_web_update_time = file.readline().strip()
        output += "Collection cache last updated: %s<br />" % collection_web_update_time
        file.close()
    except:
        pass

    # reformat collection_web_update_time to the format suitable for comparisons
    try:
        collection_web_update_time = strftime("%Y-%m-%d %H:%M:%S",
                           time.strptime(collection_web_update_time, "%d %b %Y %H:%M:%S"))
    except ValueError, e:
        pass

    if collection_table_update_time > collection_web_update_time:
        output += """<br /><b><span class="info">Warning: The collections have been modified since last time Webcoll was executed, to process the changes, Webcoll must be executed.</span></b><br />"""

    header = ['ID', 'Name', 'Time', 'Status', 'Progress']
    actions = []
    output += """<br /><b>Last BibSched tasks:</b><br />"""

    res = run_sql("select id, proc, host, user, runtime, sleeptime, arguments, status, progress from schTASK where proc='webcoll' and runtime< now() ORDER by runtime")
    if len(res) > 0:
        (id, proc, host, user, runtime, sleeptime, arguments, status, progress) = res[len(res) - 1]
        webcoll__update_time = runtime
        actions.append([id, proc, runtime, (status !="" and status or ''), (progress !="" and progress or '')])
    else:
        actions.append(['', 'webcoll', '', '', 'Not executed yet'])

    res = run_sql("select id, proc, host, user, runtime, sleeptime, arguments, status, progress from schTASK where proc='bibindex' and runtime< now() ORDER by runtime")

    if len(res) > 0:
        (id, proc, host, user, runtime, sleeptime, arguments, status, progress) = res[len(res) - 1]
        actions.append([id, proc, runtime, (status !="" and status or ''), (progress !="" and progress or '')])
    else:
        actions.append(['', 'bibindex', '', '', 'Not executed yet'])

    output += tupletotable(header=header, tuple=actions)
    output += """<br /><b>Next scheduled BibSched run:</b><br />"""
    actions = []

    res = run_sql("select id, proc, host, user, runtime, sleeptime, arguments, status, progress from schTASK where proc='webcoll' and runtime > now() ORDER by runtime")

    webcoll_future = ""
    if len(res) > 0:
        (id, proc, host, user, runtime, sleeptime, arguments, status, progress) = res[0]
        webcoll__update_time = runtime
        actions.append([id, proc, runtime, (status !="" and status or ''), (progress !="" and progress or '')])
        webcoll_future = "yes"
    else:
        actions.append(['', 'webcoll', '', '', 'Not scheduled'])

    res = run_sql("select id, proc, host, user, runtime, sleeptime, arguments, status, progress from schTASK where proc='bibindex' and runtime > now() ORDER by runtime")

    bibindex_future = ""
    if len(res) > 0:
        (id, proc, host, user, runtime, sleeptime, arguments, status, progress) = res[0]
        actions.append([id, proc, runtime, (status !="" and status or ''), (progress !="" and progress or '')])
        bibindex_future = "yes"
    else:
        actions.append(['', 'bibindex', '', '', 'Not scheduled'])

    output += tupletotable(header=header, tuple=actions)

    if webcoll_future == "":
        output += """<br /><b><span class="info">Warning: Webcoll is not scheduled for a future run by bibsched, any updates to the collection will not be processed.</span></b><br />"""
    if bibindex_future == "":
        output += """<br /><b><span class="info">Warning: Bibindex is not scheduled for a future run by bibsched, any updates to the records will not be processed.</span></b><br />"""

    body = [output]

    if callback:
        return perform_index(colID, ln, "perform_checkwebcollstatus", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_modifyrestricted(colID, ln, rest='', callback='yes', confirm=-1):
    """modify which apache group is allowed to access the collection.
    rest - the groupname"""

    subtitle = ''
    output  = ""

    col_dict = dict(get_def_name('', "collection"))
    action_id = acc_get_action_id(VIEWRESTRCOLL)
    if colID and col_dict.has_key(int(colID)):
        colID = int(colID)
        subtitle = """<a name="2">2. Modify access restrictions for collection '%s'</a>&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/websearch-admin-guide#3.2">?</a>]</small>""" % (col_dict[colID], CFG_SITE_URL)

        output = """<p>Please note that Invenio versions greater than <em>0.92.1</em> manage collection restriction via the standard
        <strong><a href="/admin/webaccess/webaccessadmin.py/showactiondetails?id_action=%i">WebAccess Admin Interface</a></strong> (action '%s').</p>
        """ % (action_id, VIEWRESTRCOLL)
    body = [output]

    if callback:
        return perform_editcollection(colID, ln, "perform_modifyrestricted", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_checkcollectionstatus(colID, ln, confirm=0, callback='yes'):
    """Check the configuration of the collections."""

    from invenio.search_engine import collection_restricted_p, restricted_collection_cache

    subtitle = """<a name="11"></a>Collection Status&nbsp;&nbsp;&nbsp;[<a href="%s/help/admin/websearch-admin-guide#6">?</a>]""" % CFG_SITE_URL
    output  = ""

    colID = int(colID)
    col_dict = dict(get_def_name('', "collection"))
    collections = run_sql("SELECT id, name, dbquery, nbrecs FROM collection "
            "ORDER BY id")

    header = ['ID', 'Name','Query', 'Subcollections', 'Restricted', 'Hosted',
            'I18N', 'Status', 'Number of records']
    rnk_list = get_def_name('', "rnkMETHOD")
    actions = []

    restricted_collection_cache.recreate_cache_if_needed()

    for (id, name, dbquery, nbrecs) in collections:
        reg_sons = col_has_son(id, 'r')
        vir_sons = col_has_son(id, 'v')
        status = ""
        hosted = ""

        if str(dbquery).startswith("hostedcollection:"): hosted = """<b><span class="info">Yes</span></b>"""
        else: hosted = """<b><span class="info">No</span></b>"""

        langs = run_sql("SELECT ln from collectionname where id_collection=%s", (id, ))
        i8n = ""

        if len(langs) > 0:
            for lang in langs:
                i8n += "%s, " % lang
        else:
            i8n = """<b><span class="info">None</span></b>"""
        if reg_sons and dbquery:
            status = """<b><span class="warning">1:Conflict</span></b>"""
        elif not dbquery and not reg_sons:
            status = """<b><span class="warning">2:Empty</span></b>"""

        if (reg_sons or vir_sons):
            subs = """<b><span class="info">Yes</span></b>"""
        else:
            subs = """<b><span class="info">No</span></b>"""

        if dbquery is None:
            dbquery = """<b><span class="info">No</span></b>"""

        restricted = collection_restricted_p(name, recreate_cache_if_needed=False)
        if restricted:
            restricted = """<b><span class="warning">Yes</span></b>"""
            if status:
                status += """<b><span class="warning">,3:Restricted</span></b>"""
            else:
                status += """<b><span class="warning">3:Restricted</span></b>"""
        else:
            restricted = """<b><span class="info">No</span></b>"""

        if status == "":
            status = """<b><span class="info">OK</span></b>"""

        actions.append([id, """<a href="%s/admin/websearch/websearchadmin.py/editcollection?colID=%s&amp;ln=%s">%s</a>""" % (CFG_SITE_URL, id, ln, name), dbquery, subs, restricted, hosted, i8n, status, nbrecs])

    output += tupletotable(header=header, tuple=actions)

    body = [output]

    return addadminbox(subtitle, body)

    if callback:
        return perform_index(colID, ln, "perform_checkcollectionstatus", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_checkexternalcollections(colID, ln, icl=None, update="", confirm=0, callback='yes'):
    """Check the external collections for inconsistencies."""

    subtitle = """<a name="7"></a>Check external collections&nbsp;&nbsp;&nbsp;[<a href="%s/help/admin/websearch-admin-guide#7">?</a>]""" % CFG_SITE_URL
    output  = ""

    colID = int(colID)

    if icl:
        if update == "add":
            # icl : the "inconsistent list" comes as a string, it has to be converted back into a list
            icl = eval(icl)
            #icl = icl[1:-1].split(',')
            for collection in icl:
                #collection = str(collection[1:-1])
                query_select = "SELECT name FROM externalcollection WHERE name like '%(name)s';" % {'name': collection}
                results_select = run_sql(query_select)
                if not results_select:
                    query_insert = "INSERT INTO externalcollection (name) VALUES ('%(name)s');" % {'name': collection}
                    run_sql(query_insert)
                    output += """<br /><span class=info>New collection \"%s\" has been added to the database table \"externalcollection\".</span><br />""" % (collection)
                else:
                    output += """<br /><span class=info>Collection \"%s\" has already been added to the database table \"externalcollection\" or was already there.</span><br />""" % (collection)
        elif update == "del":
            # icl : the "inconsistent list" comes as a string, it has to be converted back into a list
            icl = eval(icl)
            #icl = icl[1:-1].split(',')
            for collection in icl:
                #collection = str(collection[1:-1])
                query_select = "SELECT id FROM externalcollection WHERE name like '%(name)s';" % {'name': collection}
                results_select = run_sql(query_select)
                if results_select:
                    query_delete = "DELETE FROM externalcollection WHERE id like '%(id)s';" % {'id': results_select[0][0]}
                    query_delete_states = "DELETE FROM collection_externalcollection WHERE id_externalcollection like '%(id)s';" % {'id': results_select[0][0]}
                    run_sql(query_delete)
                    run_sql(query_delete_states)
                    output += """<br /><span class=info>Collection \"%s\" has been deleted from the database table \"externalcollection\".</span><br />""" % (collection)
                else:
                    output += """<br /><span class=info>Collection \"%s\" has already been delete from the database table \"externalcollection\" or was never there.</span><br />""" % (collection)

    external_collections_file = []
    external_collections_db = []

    for coll in external_collections_dictionary.values():
        external_collections_file.append(coll.name)
    external_collections_file.sort()

    query = """SELECT name from externalcollection"""
    results = run_sql(query)
    for result in results:
        external_collections_db.append(result[0])
    external_collections_db.sort()

    number_file = len(external_collections_file)
    number_db = len(external_collections_db)

    if external_collections_file == external_collections_db:
        output += """<br /><span class="info">External collections are consistent.</span><br /><br />
                    &nbsp;&nbsp;&nbsp;- database table \"externalcollection\" has %(number_db)s collections<br />
                    &nbsp;&nbsp;&nbsp;- configuration file \"websearch_external_collections_config.py\" has %(number_file)s collections""" % {
                        "number_db" : number_db,
                        "number_file" : number_file}

    elif len(external_collections_file) > len(external_collections_db):
        external_collections_diff = list(set(external_collections_file) - set(external_collections_db))
        external_collections_db.extend(external_collections_diff)
        external_collections_db.sort()
        if external_collections_file == external_collections_db:
            output += """<br /><span class="warning">There is an inconsistency:</span><br /><br />
                        &nbsp;&nbsp;&nbsp;- database table \"externalcollection\" has %(number_db)s collections
                        &nbsp;(<span class="warning">missing: %(diff)s</span>)<br />
                        &nbsp;&nbsp;&nbsp;- configuration file \"websearch_external_collections_config.py\" has %(number_file)s collections
                        <br /><br /><a href="%(site_url)s/admin/websearch/websearchadmin.py/checkexternalcollections?colID=%(colID)s&amp;icl=%(diff)s&amp;update=add&amp;ln=%(ln)s">
                        Click here</a> to update your database adding the missing collections. If the problem persists please check your configuration manually.""" % {
                            "number_db" : number_db,
                            "number_file" : number_file,
                            "diff" : external_collections_diff,
                            "site_url" : CFG_SITE_URL,
                            "colID" : colID,
                            "ln" : ln}
        else:
            output += """<br /><span class="warning">There is an inconsistency:</span><br /><br />
                        &nbsp;&nbsp;&nbsp;- database table \"externalcollection\" has %(number_db)s collections<br />
                        &nbsp;&nbsp;&nbsp;- configuration file \"websearch_external_collections_config.py\" has %(number_file)s collections
                        <br /><br /><span class="warning">The external collections do not match.</span>
                        <br />To fix the problem please check your configuration manually.""" % {
                            "number_db" : number_db,
                            "number_file" : number_file}

    elif len(external_collections_file) < len(external_collections_db):
        external_collections_diff = list(set(external_collections_db) - set(external_collections_file))
        external_collections_file.extend(external_collections_diff)
        external_collections_file.sort()
        if external_collections_file == external_collections_db:
            output += """<br /><span class="warning">There is an inconsistency:</span><br /><br />
                        &nbsp;&nbsp;&nbsp;- database table \"externalcollection\" has %(number_db)s collections
                        &nbsp;(<span class="warning">extra: %(diff)s</span>)<br />
                        &nbsp;&nbsp;&nbsp;- configuration file \"websearch_external_collections_config.py\" has %(number_file)s collections
                        <br /><br /><a href="%(site_url)s/admin/websearch/websearchadmin.py/checkexternalcollections?colID=%(colID)s&amp;icl=%(diff)s&amp;update=del&amp;ln=%(ln)s">
                        Click here</a> to force remove the extra collections from your database (warning: use with caution!). If the problem persists please check your configuration manually.""" % {
                            "number_db" : number_db,
                            "number_file" : number_file,
                            "diff" : external_collections_diff,
                            "site_url" : CFG_SITE_URL,
                            "colID" : colID,
                            "ln" : ln}
        else:
            output += """<br /><span class="warning">There is an inconsistency:</span><br /><br />
                        &nbsp;&nbsp;&nbsp;- database table \"externalcollection\" has %(number_db)s collections<br />
                        &nbsp;&nbsp;&nbsp;- configuration file \"websearch_external_collections_config.py\" has %(number_file)s collections
                        <br /><br /><span class="warning">The external collections do not match.</span>
                        <br />To fix the problem please check your configuration manually.""" % {
                            "number_db" : number_db,
                            "number_file" : number_file}

    else:
        output += """<br /><span class="warning">There is an inconsistency:</span><br /><br />
                    &nbsp;&nbsp;&nbsp;- database table \"externalcollection\" has %(number_db)s collections<br />
                    &nbsp;&nbsp;&nbsp;- configuration file \"websearch_external_collections_config.py\" has %(number_file)s collections
                    <br /><br /><span class="warning">The number of external collections is the same but the collections do not match.</span>
                    <br />To fix the problem please check your configuration manually.""" % {
                        "number_db" : number_db,
                        "number_file" : number_file}

    body = [output]

    return addadminbox(subtitle, body)

    if callback:
        return perform_index(colID, ln, "perform_checkexternalcollections", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_checksearchservices(colID, ln, icl=None, update="", confirm=0, callback='yes'):
    """Check the enabled search services, and possible errors"""
    from invenio.pluginutils import PluginContainer
    from invenio.websearch_services import CFG_SEARCH_SERVICES_PATH, \
         __required_plugin_API_version__, \
         SearchService

    subtitle = """<a name="10"></a>Check search services &nbsp;&nbsp;&nbsp;[<a href="%s/help/admin/websearch-admin-guide#10">?</a>]""" % CFG_SITE_URL
    output  = ""

    output += "<p>You can enable a search service by dropping the corresonpding plugin at <code>%s</code>.</p>" % \
              cgi.escape(CFG_SEARCH_SERVICES_PATH)

    search_service_plugins = PluginContainer(os.path.join(CFG_SEARCH_SERVICES_PATH, '*Service.py'),
                                             api_version=__required_plugin_API_version__,
                                             plugin_signature=SearchService)

    output += "<br /><b>Enabled search services:</b><br />"
    header = ['Service', 'Description', 'Status']
    actions = []
    for name, plugin in search_service_plugins.get_enabled_plugins().iteritems():
        description = plugin().get_description()
        actions.append((name, description, '<span style="color:#080">OK</a>'))

    if actions:
        output += tupletotable(header=header, tuple=actions)
    else:
        output += '<em style="color:#f80;font-size:small">No search service enabled</em>'

    output += "<br /><b>Search services with errors:</b><br />"
    header = ['Service', 'Error']
    actions = []
    for name, error in search_service_plugins.get_broken_plugins().iteritems():
        actions.append((name, '<pre style="color:#800">' + cgi.escape(repr(error[0]) + " " + repr(error[1]) + "\n" + "\n".join(traceback.format_tb(error[2]))) + '</pre>'))

    if actions:
        output += tupletotable(header=header, tuple=actions)
    else:
        output += '<em style="color:#080;font-size:small">No error found</em>'

    body = [output]

    if callback:
        return perform_index(colID, ln, "perform_checksearchservices", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def col_has_son(colID, rtype='r'):
    """Return True if the collection has at least one son."""
    return run_sql("SELECT id_son FROM collection_collection WHERE id_dad=%s and type=%s LIMIT 1", (colID, rtype)) != ()

def get_col_tree(colID, rtype=''):
    """Returns a presentation of the tree as a list. TODO: Add loop detection
    colID - startpoint for the tree
    rtype - get regular or virtual part of the tree"""

    try:
        colID = int(colID)
        stack = [colID]
        ssize = 0
        tree = [(colID, 0, 0, colID, 'r')]
        while len(stack) > 0:
            ccolID = stack.pop()
            if ccolID == colID and rtype:
                res = run_sql("SELECT id_son, score, type FROM collection_collection WHERE id_dad=%s AND type=%s ORDER BY score ASC,id_son", (ccolID, rtype))
            else:
                res = run_sql("SELECT id_son, score, type FROM collection_collection WHERE id_dad=%s ORDER BY score ASC,id_son", (ccolID, ))
            ssize += 1
            ntree = []
            for i in range(0, len(res)):
                id_son = res[i][0]
                score = res[i][1]
                rtype = res[i][2]
                stack.append(id_son)
                if i == (len(res) - 1):
                    up = 0
                else:
                    up = 1
                if i == 0:
                    down = 0
                else:
                    down = 1
                ntree.insert(0, (id_son, up, down, ccolID, rtype))
            tree = tree[0:ssize] + ntree + tree[ssize:len(tree)]
        return tree
    except StandardError, e:
        register_exception()
        return ()

def add_col_dad_son(add_dad, add_son, rtype):
    """Add a son to a collection (dad)
    add_dad - add to this collection id
    add_son - add this collection id
    rtype - either regular or virtual"""

    try:
        res = run_sql("SELECT score FROM collection_collection WHERE id_dad=%s ORDER BY score ASC", (add_dad, ))
        highscore = 0
        for score in res:
            if int(score[0]) > highscore:
                highscore = int(score[0])
        highscore += 1
        res = run_sql("INSERT INTO collection_collection(id_dad,id_son,score,type) values(%s,%s,%s,%s)", (add_dad, add_son, highscore, rtype))
        return (1, highscore)
    except StandardError, e:
        register_exception()
        return (0, e)

def compare_on_val(first, second):
    """Compare the two values"""

    return cmp(first[1], second[1])

def get_col_fld(colID=-1, type = '', id_field=''):
    """Returns either all portalboxes associated with a collection, or based on either colID or language or both.
    colID - collection id
    ln - language id"""

    sql = "SELECT id_field,id_fieldvalue,type,score,score_fieldvalue FROM collection_field_fieldvalue, field WHERE id_field=field.id"

    params = []
    if colID > -1:
        sql += " AND id_collection=%s"
        params.append(colID)
    if id_field:
        sql += " AND id_field=%s"
        params.append(id_field)
    if type:
        sql += " AND type=%s"
        params.append(type)
    sql += " ORDER BY type, score desc, score_fieldvalue desc"
    res = run_sql(sql, tuple(params))
    return res

def get_col_pbx(colID=-1, ln='', position = ''):
    """Returns either all portalboxes associated with a collection, or based on either colID or language or both.
    colID - collection id
    ln - language id"""

    sql = "SELECT id_portalbox, id_collection, ln, score, position, title, body FROM collection_portalbox, portalbox WHERE id_portalbox = portalbox.id"

    params = []
    if colID > -1:
        sql += " AND id_collection=%s"
        params.append(colID)
    if ln:
        sql += " AND ln=%s"
        params.append(ln)
    if position:
        sql += " AND position=%s"
        params.append(position)
    sql += " ORDER BY position, ln, score desc"
    res = run_sql(sql, tuple(params))
    return res

def get_col_fmt(colID=-1):
    """Returns all formats currently associated with a collection, or for one specific collection
    colID - the id of the collection"""

    if colID not in [-1, "-1"]:
        res = run_sql("SELECT id_format, id_collection, code, score FROM collection_format, format WHERE id_format = format.id AND id_collection=%s ORDER BY score desc", (colID, ))
    else:
        res = run_sql("SELECT id_format, id_collection, code, score FROM collection_format, format WHERE id_format = format.id ORDER BY score desc")
    return res

def get_col_rnk(colID, ln):
    """ Returns a list of the rank methods the given collection is attached to
    colID - id from collection"""

    try:
        res1 = dict(run_sql("SELECT id_rnkMETHOD, '' FROM collection_rnkMETHOD WHERE id_collection=%s", (colID, )))
        res2 = get_def_name('', "rnkMETHOD")
        result = filter(lambda x: res1.has_key(x[0]), res2)
        return result
    except StandardError, e:
        return ()

def get_pbx():
    """Returns all portalboxes"""

    res = run_sql("SELECT id, title, body FROM portalbox ORDER by title,body")
    return res

def get_fld_value(fldvID = ''):
    """Returns fieldvalue"""

    sql = "SELECT id, name, value FROM fieldvalue"
    params = []
    if fldvID:
        sql += " WHERE id=%s"
        params.append(fldvID)
    sql += " ORDER BY name"
    res = run_sql(sql, tuple(params))
    return res

def get_pbx_pos():
    """Returns a list of all the positions for a portalbox"""

    position = {}
    position["rt"] = "Right Top"
    position["lt"] = "Left Top"
    position["te"] = "Title Epilog"
    position["tp"] = "Title Prolog"
    position["ne"] = "Narrow by coll epilog"
    position["np"] = "Narrow by coll prolog"
    return position

def get_sort_nametypes():
    """Return a list of the various translationnames for the fields"""

    type = {}
    type['soo'] = 'Sort options'
    type['seo'] = 'Search options'
    type['sew'] = 'Search within'
    return type

def get_fmt_nametypes():
    """Return a list of the various translationnames for the output formats"""

    type = []
    type.append(('ln', 'Long name'))
    return type

def get_fld_nametypes():
    """Return a list of the various translationnames for the fields"""

    type = []
    type.append(('ln', 'Long name'))
    return type

def get_col_nametypes():
    """Return a list of the various translationnames for the collections"""

    type = []
    type.append(('ln', 'Collection name'))
    return type

def find_last(tree, start_son):
    """Find the previous collection in the tree with the same father as start_son"""

    id_dad = tree[start_son][3]
    while start_son > 0:
        start_son -= 1
        if tree[start_son][3] == id_dad:
            return start_son

def find_next(tree, start_son):
    """Find the next collection in the tree with the same father as start_son"""

    id_dad = tree[start_son][3]
    while start_son < len(tree):
        start_son += 1
        if tree[start_son][3] == id_dad:
            return start_son

def remove_col_subcol(id_son, id_dad, type):
    """Remove a collection as a son of another collection in the tree, if collection isn't used elsewhere in the tree, remove all registered sons of the id_son.
    id_son - collection id of son to remove
    id_dad - the id of the dad"""

    try:
        if id_son != id_dad:
            tree = get_col_tree(id_son)
            run_sql("DELETE FROM collection_collection WHERE id_son=%s and id_dad=%s", (id_son, id_dad))
        else:
            tree = get_col_tree(id_son, type)
            run_sql("DELETE FROM collection_collection WHERE id_son=%s and id_dad=%s and type=%s", (id_son, id_dad, type))
        if not run_sql("SELECT id_dad,id_son,type,score from collection_collection WHERE id_son=%s and type=%s", (id_son, type)):
            for (id, up, down, dad, rtype) in tree:
                run_sql("DELETE FROM collection_collection WHERE id_son=%s and id_dad=%s", (id, dad))
        return (1, "")
    except StandardError, e:
        return (0, e)

def check_col(add_dad, add_son):
    """Check if the collection can be placed as a son of the dad without causing loops.
    add_dad - collection id
    add_son - collection id"""

    try:
        stack = [add_dad]
        res = run_sql("SELECT id_dad FROM collection_collection WHERE id_dad=%s AND id_son=%s", (add_dad, add_son))
        if res:
            raise StandardError
        while len(stack) > 0:
            colID = stack.pop()
            res = run_sql("SELECT id_dad FROM collection_collection WHERE id_son=%s", (colID, ))
            for id in res:
                if int(id[0]) == int(add_son):
                    # raise StandardError # this was the original but it didnt work
                    return(0)
                else:
                    stack.append(id[0])
        return (1, "")
    except StandardError, e:
        return (0, e)

def attach_rnk_col(colID, rnkID):
    """attach rank method to collection
    rnkID - id from rnkMETHOD table
    colID - id of collection, as in collection table """

    try:
        res = run_sql("INSERT INTO collection_rnkMETHOD(id_collection, id_rnkMETHOD) values (%s,%s)", (colID, rnkID))
        return (1, "")
    except StandardError, e:
        register_exception()
        return (0, e)

def detach_rnk_col(colID, rnkID):
    """detach rank method from collection
    rnkID - id from rnkMETHOD table
    colID - id of collection, as in collection table """

    try:
        res = run_sql("DELETE FROM collection_rnkMETHOD WHERE id_collection=%s AND id_rnkMETHOD=%s", (colID, rnkID))
        return (1, "")
    except StandardError, e:
        register_exception()
        return (0, e)

def switch_col_treescore(col_1, col_2):
    try:
        res1 = run_sql("SELECT score FROM collection_collection WHERE id_dad=%s and id_son=%s", (col_1[3], col_1[0]))
        res2 = run_sql("SELECT score FROM collection_collection WHERE id_dad=%s and id_son=%s", (col_2[3], col_2[0]))
        res = run_sql("UPDATE collection_collection SET score=%s WHERE id_dad=%s and id_son=%s", (res2[0][0], col_1[3], col_1[0]))
        res = run_sql("UPDATE collection_collection SET score=%s WHERE id_dad=%s and id_son=%s", (res1[0][0], col_2[3], col_2[0]))
        return (1, "")
    except StandardError, e:
        register_exception()
        return (0, e)

def move_col_tree(col_from, col_to, move_to_rtype=''):
    """Move a collection from one point in the tree to another. becomes a son of the endpoint.
    col_from - move this collection from current point
    col_to - and set it as a son of this collection.
    move_to_rtype - either virtual or regular collection"""

    try:
        res = run_sql("SELECT score FROM collection_collection WHERE id_dad=%s ORDER BY score asc", (col_to[0], ))
        highscore = 0
        for score in res:
            if int(score[0]) > highscore:
                highscore = int(score[0])
        highscore += 1
        if not move_to_rtype:
            move_to_rtype = col_from[4]
        res = run_sql("DELETE FROM collection_collection WHERE id_son=%s and id_dad=%s", (col_from[0], col_from[3]))
        res = run_sql("INSERT INTO collection_collection(id_dad,id_son,score,type) values(%s,%s,%s,%s)", (col_to[0], col_from[0], highscore, move_to_rtype))
        return (1, "")
    except StandardError, e:
        register_exception()
        return (0, e)

def remove_pbx(colID, pbxID, ln):
    """Removes a portalbox from the collection given.
    colID - the collection the format is connected to
    pbxID - the portalbox which should be removed from the collection.
    ln - the language of the portalbox to be removed"""

    try:
        res = run_sql("DELETE FROM collection_portalbox WHERE id_collection=%s AND id_portalbox=%s AND ln=%s", (colID, pbxID, ln))
        return (1, "")
    except StandardError, e:
        register_exception()
        return (0, e)

def remove_fmt(colID, fmtID):
    """Removes a format from the collection given.
    colID - the collection the format is connected to
    fmtID - the format which should be removed from the collection."""

    try:
        res = run_sql("DELETE FROM collection_format WHERE id_collection=%s AND id_format=%s", (colID, fmtID))
        return (1, "")
    except StandardError, e:
        register_exception()
        return (0, e)

def remove_fld(colID, fldID, fldvID=''):
    """Removes a field from the collection given.
    colID - the collection the format is connected to
    fldID - the field which should be removed from the collection."""

    try:
        sql = "DELETE FROM collection_field_fieldvalue WHERE id_collection=%s AND id_field=%s"
        params = [colID, fldID]
        if fldvID:
            if fldvID != "None":
                sql += " AND id_fieldvalue=%s"
                params.append(fldvID)
            else:
                sql += " AND id_fieldvalue is NULL"
        res = run_sql(sql, tuple(params))
        return (1, "")
    except StandardError, e:
        register_exception()
        return (0, e)

def delete_fldv(fldvID):
    """Deletes all data for the given fieldvalue
    fldvID - delete all data in the tables associated with fieldvalue and this id"""

    try:
        res = run_sql("DELETE FROM collection_field_fieldvalue WHERE id_fieldvalue=%s", (fldvID, ))
        res = run_sql("DELETE FROM fieldvalue WHERE id=%s", (fldvID, ))
        return (1, "")
    except StandardError, e:
        register_exception()
        return (0, e)

def delete_pbx(pbxID):
    """Deletes all data for the given portalbox
    pbxID - delete all data in the tables associated with portalbox and this id """

    try:
        res = run_sql("DELETE FROM collection_portalbox WHERE id_portalbox=%s", (pbxID, ))
        res = run_sql("DELETE FROM portalbox WHERE id=%s", (pbxID, ))
        return (1, "")
    except StandardError, e:
        register_exception()
        return (0, e)

def delete_fmt(fmtID):
    """Deletes all data for the given format
    fmtID - delete all data in the tables associated with format and this id """

    try:
        res = run_sql("DELETE FROM format WHERE id=%s", (fmtID, ))
        res = run_sql("DELETE FROM collection_format WHERE id_format=%s", (fmtID, ))
        res = run_sql("DELETE FROM formatname WHERE id_format=%s", (fmtID, ))
        return (1, "")
    except StandardError, e:
        register_exception()
        return (0, e)

def delete_col(colID):
    """Deletes all data for the given collection
    colID - delete all data in the tables associated with collection and this id """

    try:
        res = run_sql("DELETE FROM collection WHERE id=%s", (colID, ))
        res = run_sql("DELETE FROM collectionname WHERE id_collection=%s", (colID, ))
        res = run_sql("DELETE FROM collection_rnkMETHOD WHERE id_collection=%s", (colID, ))
        res = run_sql("DELETE FROM collection_collection WHERE id_dad=%s", (colID, ))
        res = run_sql("DELETE FROM collection_collection WHERE id_son=%s", (colID, ))
        res = run_sql("DELETE FROM collection_portalbox WHERE id_collection=%s", (colID, ))
        res = run_sql("DELETE FROM collection_format WHERE id_collection=%s", (colID, ))
        res = run_sql("DELETE FROM collection_field_fieldvalue WHERE id_collection=%s", (colID, ))
        return (1, "")
    except StandardError, e:
        register_exception()
        return (0, e)

def add_fmt(code, name, rtype):
    """Add a new output format. Returns the id of the format.
    code - the code for the format, max 6 chars.
    name - the default name for the default language of the format.
    rtype - the default nametype"""

    try:
        res = run_sql("INSERT INTO format (code, name) values (%s,%s)", (code, name))
        fmtID = run_sql("SELECT id FROM format WHERE code=%s", (code,))
        res = run_sql("INSERT INTO formatname(id_format, type, ln, value) VALUES (%s,%s,%s,%s)",
                      (fmtID[0][0], rtype, CFG_SITE_LANG, name))
        return (1, fmtID)
    except StandardError, e:
        register_exception()
        return (0, e)

def update_fldv(fldvID, name, value):
    """Modify existing fieldvalue
    fldvID - id of fieldvalue to modify
    value - the value of the fieldvalue
    name - the name of the fieldvalue."""

    try:
        res = run_sql("UPDATE fieldvalue set name=%s where id=%s", (name, fldvID))
        res = run_sql("UPDATE fieldvalue set value=%s where id=%s", (value, fldvID))
        return (1, "")
    except StandardError, e:
        register_exception()
        return (0, e)

def add_fldv(name, value):
    """Add a new fieldvalue, returns id of fieldvalue
    value - the value of the fieldvalue
    name - the name of the fieldvalue."""

    try:
        res = run_sql("SELECT id FROM fieldvalue WHERE name=%s and value=%s", (name, value))
        if not res:
            res = run_sql("INSERT INTO fieldvalue (name, value) values (%s,%s)", (name, value))
            res = run_sql("SELECT id FROM fieldvalue WHERE name=%s and value=%s", (name, value))
        if res:
            return (1, res[0][0])
        else:
            raise StandardError
    except StandardError, e:
        register_exception()
        return (0, e)

def add_pbx(title, body):
    try:
        res = run_sql("INSERT INTO portalbox (title, body) values (%s,%s)", (title, body))
        res = run_sql("SELECT id FROM portalbox WHERE title=%s AND body=%s", (title, body))
        if res:
            return (1, res[0][0])
        else:
            raise StandardError
    except StandardError, e:
        register_exception()
        return (0, e)

def add_col(colNAME, dbquery=None):
    """Adds a new collection to collection table
    colNAME - the default name for the collection, saved to collection and collectionname
    dbquery - query related to the collection"""
    # BTW, sometimes '' are passed instead of None, so change them to None
    if not dbquery:
        dbquery = None
    try:
        rtype = get_col_nametypes()[0][0]
        colID = run_sql("SELECT id FROM collection WHERE id=1")
        if colID:
            res = run_sql("INSERT INTO collection (name,dbquery) VALUES (%s,%s)",
                          (colNAME,dbquery))
        else:
            res = run_sql("INSERT INTO collection (id,name,dbquery) VALUES (1,%s,%s)",
                          (colNAME,dbquery))
        colID = run_sql("SELECT id FROM collection WHERE name=%s", (colNAME,))
        res = run_sql("INSERT INTO collectionname(id_collection, type, ln, value) VALUES (%s,%s,%s,%s)",
                      (colID[0][0], rtype, CFG_SITE_LANG, colNAME))
        if colID:
            return (1, colID[0][0])
        else:
            raise StandardError
    except StandardError, e:
        register_exception()
        return (0, e)

def add_col_pbx(colID, pbxID, ln, position, score=''):
    """add a portalbox to the collection.
    colID - the id of the collection involved
    pbxID - the portalbox to add
    ln - which language the portalbox is for
    score - decides which portalbox is the most important
    position - position on page the portalbox should appear."""

    try:
        if score:
            res = run_sql("INSERT INTO collection_portalbox(id_portalbox, id_collection, ln, score, position) values (%s,%s,'%s',%s,%s)", (pbxID, colID, ln, score, position))
        else:
            res = run_sql("SELECT score FROM collection_portalbox WHERE id_collection=%s and ln=%s and position=%s ORDER BY score desc, ln, position", (colID, ln, position))
            if res:
                score = int(res[0][0])
            else:
                score = 0
            res = run_sql("INSERT INTO collection_portalbox(id_portalbox, id_collection, ln, score, position) values (%s,%s,%s,%s,%s)", (pbxID, colID, ln, (score + 1), position))
        return (1, "")
    except StandardError, e:
        register_exception()
        return (0, e)

def add_col_fmt(colID, fmtID, score=''):
    """Add a output format to the collection.
    colID - the id of the collection involved
    fmtID - the id of the format.
    score - the score of the format, decides sorting, if not given, place the format on top"""

    try:
        if score:
            res = run_sql("INSERT INTO collection_format(id_format, id_collection, score) values (%s,%s,%s)", (fmtID, colID, score))
        else:
            res = run_sql("SELECT score FROM collection_format WHERE id_collection=%s ORDER BY score desc", (colID, ))
            if res:
                score = int(res[0][0])
            else:
                score = 0
            res = run_sql("INSERT INTO collection_format(id_format, id_collection, score) values (%s,%s,%s)", (fmtID, colID, (score + 1)))
        return (1, "")
    except StandardError, e:
        register_exception()
        return (0, e)

def add_col_fld(colID, fldID, type, fldvID=''):
    """Add a sort/search/field to the collection.
    colID - the id of the collection involved
    fldID - the id of the field.
    fldvID - the id of the fieldvalue.
    type - which type, seo, sew...
    score - the score of the format, decides sorting, if not given, place the format on top"""

    try:
        if fldvID and fldvID not in [-1, "-1"]:
            run_sql("DELETE FROM collection_field_fieldvalue WHERE id_collection=%s AND id_field=%s and type=%s and id_fieldvalue is NULL", (colID, fldID, type))
            res = run_sql("SELECT score FROM collection_field_fieldvalue WHERE id_collection=%s AND id_field=%s and type=%s ORDER BY score desc", (colID, fldID, type))
            if res:
                score = int(res[0][0])
                res = run_sql("SELECT score_fieldvalue FROM collection_field_fieldvalue WHERE id_collection=%s AND id_field=%s and type=%s ORDER BY score_fieldvalue desc", (colID, fldID, type))
            else:
                res = run_sql("SELECT score FROM collection_field_fieldvalue WHERE id_collection=%s and type=%s ORDER BY score desc", (colID, type))
                if res:
                    score = int(res[0][0]) + 1
                else:
                    score = 1

            res = run_sql("SELECT id_collection,id_field,id_fieldvalue,type,score,score_fieldvalue FROM collection_field_fieldvalue where id_field=%s and id_collection=%s and type=%s and id_fieldvalue=%s", (fldID, colID, type, fldvID))
            if not res:
                run_sql("UPDATE collection_field_fieldvalue SET score_fieldvalue=score_fieldvalue+1 WHERE id_field=%s AND id_collection=%s and type=%s", (fldID, colID, type))
                res = run_sql("INSERT INTO collection_field_fieldvalue(id_field, id_fieldvalue, id_collection, type, score, score_fieldvalue) values (%s,%s,%s,%s,%s,%s)", (fldID, fldvID, colID, type, score, 1))
            else:
                return (0, (1, "Already exists"))
        else:
            res = run_sql("SELECT id_collection,id_field,id_fieldvalue,type,score,score_fieldvalue FROM collection_field_fieldvalue WHERE id_collection=%s AND type=%s and id_field=%s and id_fieldvalue is NULL", (colID, type, fldID))
            if res:
                return (0, (1, "Already exists"))
            else:
                run_sql("UPDATE collection_field_fieldvalue SET score=score+1")
                res = run_sql("INSERT INTO collection_field_fieldvalue(id_field, id_collection, type, score,score_fieldvalue) values (%s,%s,%s,%s, 0)", (fldID, colID, type, 1))
        return (1, "")
    except StandardError, e:
        register_exception()
        return (0, e)

def modify_dbquery(colID, dbquery=None):
    """Modify the dbquery of an collection.
    colID - the id of the collection involved
    dbquery - the new dbquery"""
    # BTW, sometimes '' is passed instead of None, so change it to None
    if not dbquery:
        dbquery = None
    try:
        res = run_sql("UPDATE collection SET dbquery=%s WHERE id=%s", (dbquery, colID))
        return (1, "")
    except StandardError, e:
        register_exception()
        return (0, e)

def modify_pbx(colID, pbxID, sel_ln, score='', position='', title='', body=''):
    """Modify a portalbox
    colID - the id of the collection involved
    pbxID - the id of the portalbox that should be modified
    sel_ln - the language of the portalbox that should be modified
    title - the title
    body - the content
    score - if several portalboxes in one position, who should appear on top.
    position - position on page"""

    try:
        if title:
            res = run_sql("UPDATE portalbox SET title=%s WHERE id=%s", (title, pbxID))
        if body:
            res = run_sql("UPDATE portalbox SET body=%s WHERE id=%s", (body, pbxID))
        if score:
            res = run_sql("UPDATE collection_portalbox SET score=%s WHERE id_collection=%s and id_portalbox=%s and ln=%s", (score, colID, pbxID, sel_ln))
        if position:
            res = run_sql("UPDATE collection_portalbox SET position=%s WHERE id_collection=%s and id_portalbox=%s and ln=%s", (position, colID, pbxID, sel_ln))
        return (1, "")
    except Exception, e:
        register_exception()
        return (0, e)

def switch_fld_score(colID, id_1, id_2):
    """Switch the scores of id_1 and id_2 in collection_field_fieldvalue
    colID - collection the id_1 or id_2 is connected to
    id_1/id_2 - id field from tables like format..portalbox...
    table - name of the table"""

    try:
        res1 = run_sql("SELECT score FROM collection_field_fieldvalue WHERE id_collection=%s and id_field=%s", (colID, id_1))
        res2 = run_sql("SELECT score FROM collection_field_fieldvalue WHERE id_collection=%s and id_field=%s", (colID, id_2))
        if res1[0][0] == res2[0][0]:
            return (0, (1, "Cannot rearrange the selected fields, either rearrange by name or use the mySQL client to fix the problem."))
        else:
            res = run_sql("UPDATE collection_field_fieldvalue SET score=%s WHERE id_collection=%s and id_field=%s", (res2[0][0], colID, id_1))
            res = run_sql("UPDATE collection_field_fieldvalue SET score=%s WHERE id_collection=%s and id_field=%s", (res1[0][0], colID, id_2))
        return (1, "")
    except StandardError, e:
        register_exception()
        return (0, e)

def switch_fld_value_score(colID, id_1, fldvID_1, fldvID_2):
    """Switch the scores of two field_value
    colID - collection the id_1 or id_2 is connected to
    id_1/id_2 - id field from tables like format..portalbox...
    table - name of the table"""

    try:
        res1 = run_sql("SELECT score_fieldvalue FROM collection_field_fieldvalue WHERE id_collection=%s and id_field=%s and id_fieldvalue=%s", (colID, id_1, fldvID_1))
        res2 = run_sql("SELECT score_fieldvalue FROM collection_field_fieldvalue WHERE id_collection=%s and id_field=%s and id_fieldvalue=%s", (colID, id_1, fldvID_2))
        if res1[0][0] == res2[0][0]:
            return (0, (1, "Cannot rearrange the selected fields, either rearrange by name or use the mySQL client to fix the problem."))
        else:
            res = run_sql("UPDATE collection_field_fieldvalue SET score_fieldvalue=%s WHERE id_collection=%s and id_field=%s and id_fieldvalue=%s", (res2[0][0], colID, id_1, fldvID_1))
            res = run_sql("UPDATE collection_field_fieldvalue SET score_fieldvalue=%s WHERE id_collection=%s and id_field=%s and id_fieldvalue=%s", (res1[0][0], colID, id_1, fldvID_2))
        return (1, "")
    except Exception, e:
        register_exception()
        return (0, e)

def switch_pbx_score(colID, id_1, id_2, sel_ln):
    """Switch the scores of id_1 and id_2 in the table given by the argument.
    colID - collection the id_1 or id_2 is connected to
    id_1/id_2 - id field from tables like format..portalbox...
    table - name of the table"""

    try:
        res1 = run_sql("SELECT score FROM collection_portalbox WHERE id_collection=%s and id_portalbox=%s and ln=%s", (colID, id_1, sel_ln))
        res2 = run_sql("SELECT score FROM collection_portalbox WHERE id_collection=%s and id_portalbox=%s and ln=%s", (colID, id_2, sel_ln))
        if res1[0][0] == res2[0][0]:
            return (0, (1, "Cannot rearrange the selected fields, either rearrange by name or use the mySQL client to fix the problem."))
        res = run_sql("UPDATE collection_portalbox SET score=%s WHERE id_collection=%s and id_portalbox=%s and ln=%s", (res2[0][0], colID, id_1, sel_ln))
        res = run_sql("UPDATE collection_portalbox SET score=%s WHERE id_collection=%s and id_portalbox=%s and ln=%s", (res1[0][0], colID, id_2, sel_ln))
        return (1, "")
    except Exception, e:
        register_exception()
        return (0, e)

def switch_score(colID, id_1, id_2, table):
    """Switch the scores of id_1 and id_2 in the table given by the argument.
    colID - collection the id_1 or id_2 is connected to
    id_1/id_2 - id field from tables like format..portalbox...
    table - name of the table"""

    try:
        res1 = run_sql("SELECT score FROM collection_%s WHERE id_collection=%%s and id_%s=%%s" % (table, table), (colID, id_1))
        res2 = run_sql("SELECT score FROM collection_%s WHERE id_collection=%%s and id_%s=%%s" % (table, table), (colID, id_2))
        if res1[0][0] == res2[0][0]:
            return (0, (1, "Cannot rearrange the selected fields, either rearrange by name or use the mySQL client to fix the problem."))
        res = run_sql("UPDATE collection_%s SET score=%%s WHERE id_collection=%%s and id_%s=%%s" % (table, table), (res2[0][0], colID, id_1))
        res = run_sql("UPDATE collection_%s SET score=%%s WHERE id_collection=%%s and id_%s=%%s" % (table, table), (res1[0][0], colID, id_2))
        return (1, "")
    except Exception, e:
        register_exception()
        return (0, e)

def get_detailed_page_tabs(colID=None, recID=None, ln=CFG_SITE_LANG):
    """
    Returns the complete list of tabs to be displayed in the
    detailed record pages.

    Returned structured is a dict with
      - key : last component of the url that leads to detailed record tab: http:www.../CFG_SITE_RECORD/74/key
      - values: a dictionary with the following keys:
                                         - label: *string* label to be printed as tab (Not localized here)
                                         - visible: *boolean* if False, tab should not be shown
                                         - enabled: *boolean* if True, tab should be disabled
                                         - order: *int* position of the tab in the list of tabs
      - ln: language of the tab labels

    returns dict
    """
    _ = gettext_set_language(ln)

    tabs = {'metadata'  : {'label': _('Information'),      'visible': False, 'enabled': True, 'order': 1},
            'references': {'label': _('References'),       'visible': False, 'enabled': True, 'order': 2},
            'citations' : {'label': _('Citations'),        'visible': False, 'enabled': True, 'order': 3},
            'keywords'  : {'label': _('Keywords'),         'visible': False, 'enabled': True, 'order': 4},
            'comments'  : {'label': _('Discussion'),       'visible': False, 'enabled': True, 'order': 5},
            'usage'     : {'label': _('Usage statistics'), 'visible': False, 'enabled': True, 'order': 6},
            'files'     : {'label': _('Files'),            'visible': False, 'enabled': True, 'order': 7},
            'plots'     : {'label': _('Plots'),            'visible': False, 'enabled': True, 'order': 8},
            'holdings'  : {'label': _('Holdings'),         'visible': False, 'enabled': True, 'order': 9},
            'linkbacks' : {'label': _('Linkbacks'),        'visible': False, 'enabled': True, 'order': 10},
            'data'      : {'label': _('Data'),             'visible': False, 'enabled': True, 'order': 11}
            }

    res = run_sql("SELECT tabs FROM collectiondetailedrecordpagetabs " + \
                  "WHERE id_collection=%s", (colID, ))

    if len(res) > 0:
        tabs_state = res[0][0].split(';')
        for tab_state in tabs_state:
            if tabs.has_key(tab_state):
                tabs[tab_state]['visible'] = True;

    else:
        # no preference set for this collection.
        # assume all tabs are displayed
        for key in tabs.keys():
            tabs[key]['visible'] = True


    if not CFG_WEBCOMMENT_ALLOW_COMMENTS and \
           not CFG_WEBCOMMENT_ALLOW_REVIEWS:
        tabs['comments']['visible'] = False
        tabs['comments']['enabled'] = False

    if recID is not None:

        # Disable references if no references found
        #bfo = BibFormatObject(recID)
        #if bfe_references.format_element(bfo, '', '') == '':
        #    tabs['references']['enabled'] = False

        ## FIXME: the above was commented out because bfe_references
        ## may be too slow.  And we do not really need this anyway
        ## because we can disable tabs in WebSearch Admin on a
        ## collection-by-collection basis.  If we need this, then we
        ## should probably call bfo.fields('999') here that should be
        ## much faster than calling bfe_references.

        # Disable citations if not citations found
        #if len(get_cited_by(recID)) == 0:
        #    tabs['citations']['enabled'] = False
        ## FIXME: the above was commented out because get_cited_by()
        ## may be too slow.  And we do not really need this anyway
        ## because we can disable tags in WebSearch Admin on a
        ## collection-by-collection basis.

        # Disable Files tab if no file found except for Plots:
        disable_files_tab_p = True
        for abibdoc in BibRecDocs(recID).list_bibdocs():
            abibdoc_type = abibdoc.get_type()
            if abibdoc_type == 'Plot':
                continue # ignore attached plots
            else:
                if CFG_INSPIRE_SITE and not \
                   abibdoc_type in ('', 'INSPIRE-PUBLIC', 'Supplementary Material'):
                    # ignore non-empty, non-INSPIRE-PUBLIC, non-suppl doctypes for INSPIRE
                    continue
                # okay, we found at least one non-Plot file:
                disable_files_tab_p = False
                break
        if disable_files_tab_p:
            tabs['files']['enabled'] = False

        #Disable holdings tab if collection != Books
        collection = run_sql("""select name from collection where id=%s""", (colID, ))
        if collection[0][0] != 'Books':
            tabs['holdings']['enabled'] = False

        # Disable Plots tab if no docfile of doctype Plot found
        brd =  BibRecDocs(recID)
        if len(brd.list_bibdocs('Plot')) == 0:
            tabs['plots']['enabled'] = False

        if CFG_CERN_SITE:
            from invenio.search_engine import get_collection_reclist
            if recID in get_collection_reclist("Books & Proceedings"):
                tabs['holdings']['visible'] = True
                tabs['holdings']['enabled'] = True
        # now treating the HEP data -> we have to check if there is Data
        # associated with the record and if so, make the tab visible and enabled

        has_data = record_has_data_attached(recID)
        tabs['data']['visible'] = has_data
        tabs['data']['enabled'] = has_data

    tabs[''] = tabs['metadata']
    del tabs['metadata']

    return tabs



def record_has_data_attached(recID):
    """returns True or False depending if there is Data attached or not"""
    from invenio.search_engine import search_pattern
    return len(search_pattern(p="786__w:%s" % (str(recID)))) > 0

def get_detailed_page_tabs_counts(recID):
    """
    Returns the number of citations, references and comments/reviews
    that have to be shown on the corresponding tabs in the
    detailed record pages
    @param recID: record id
    @return: dictionary with following keys
                'Citations': number of citations to be shown in the "Citations" tab
                'References': number of references to be shown in the "References" tab
                'Discussions': number of comments and reviews to be shown in the "Discussion" tab
    """

    num_comments = 0 #num of comments
    num_reviews = 0 #num of reviews
    tabs_counts = {'Citations'   : 0,
                   'References'  : -1,
                   'Discussions' : 0
                   }
    from invenio.search_engine import get_field_tags, get_record
    if CFG_BIBRANK_SHOW_CITATION_LINKS:
        tabs_counts['Citations'] = get_cited_by_count(recID)
    if not CFG_CERN_SITE:#FIXME:should be replaced by something like CFG_SHOW_REFERENCES
        reftag = ""
        reftags = get_field_tags("reference")
        if reftags:
            reftag = reftags[0]
        tmprec = get_record(recID)
        if reftag and len(reftag) > 4:
            tabs_counts['References'] = len(record_get_field_instances(tmprec, reftag[0:3], reftag[3], reftag[4]))
    # obtain number of comments/reviews
    from invenio.webcommentadminlib import get_nb_reviews, get_nb_comments
    if CFG_WEBCOMMENT_ALLOW_COMMENTS and CFG_WEBSEARCH_SHOW_COMMENT_COUNT:
        num_comments = get_nb_comments(recID, count_deleted=False)
    if CFG_WEBCOMMENT_ALLOW_REVIEWS and CFG_WEBSEARCH_SHOW_REVIEW_COUNT:
        num_reviews = get_nb_reviews(recID, count_deleted=False)
    if num_comments or num_reviews:
        tabs_counts['Discussions'] = num_comments + num_reviews

    return tabs_counts
