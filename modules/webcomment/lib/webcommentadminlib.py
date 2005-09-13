# -*- coding: utf-8 -*-
## $Id$
## Comments and reviews for records.
                                                                                                                                                                                                     
## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
                                                                                                                                                                                                     
__lastupdated__ = """FIXME: last updated"""


from bibrankadminlib import check_user
                            #write_outcome,modify_translations,get_def_name,get_i8n_name,get_name,get_rnk_nametypes,get_languages,check_user,is_adminuser,
                            #adderrorbox,addadminbox,tupletotable,tupletotable_onlyselected,addcheckboxes,createhiddenform,serialize_via_numeric_array_dumps,
                            #serialize_via_numeric_array_compr,serialize_via_numeric_array_escape,serialize_via_numeric_array,deserialize_via_numeric_array,
                            #serialize_via_marshal,deserialize_via_marshal
from config import *
from webcomment import wash_url_argument, query_get_comment, query_get_user_contact_info
from mod_python import apache
from dbquery import run_sql

import template
webcomment_templates = template.load('webcomment')

def getnavtrail(previous = ''):
    """Get the navtrail"""
    
    navtrail = """<a class=navtrail href="%s/admin/">Admin Area</a> &gt; <a class=navtrail href="%s/admin/webcomment/">WebComment Admin</a> """ % (weburl, weburl)
    navtrail = navtrail + previous
    return navtrail

def perform_request_index(ln=cdslang):
    """
    """ 
    return webcomment_templates.tmpl_admin_index(ln=ln)

def perform_request_delete(ln=cdslang, comID=-1):
    """
    """
    warnings = []

    ln = wash_url_argument(ln, 'str')
    comID = wash_url_argument(comID, 'int')

    if comID is not None:
        if comID <= 0:
            if comID != -1:
                warnings.append(("WRN_WEBCOMMENT_ADMIN_INVALID_COMID",))
            return (webcomment_templates.tmpl_admin_delete_form(ln, warnings),None, warnings)

        comment = query_get_comment(comID)
        if comment:
            c_star_score = 5
            if comment[c_star_score] > 0:
                reviews = 1
            else:
                reviews = 0
            return (perform_request_comments(ln=ln, comID=comID, reviews=reviews), None, warnings) 
        else:
            warnings.append(('WRN_WEBCOMMENT_ADMIN_COMID_INEXISTANT', comID))
            return (webcomment_templates.tmpl_admin_delete_form(ln, warnings), None, warnings)
    else:
        return (webcomment_templates.tmpl_admin_delete_form(ln, warnings), None, warnings)

def perform_request_users(ln=cdslang):
    """
    """
    ln = wash_url_argument(ln, 'str')

    users_data = query_get_users_reported()

    return webcomment_templates.tmpl_admin_users(ln=ln, users_data=users_data)

def query_get_users_reported():
    """
    Get the users who have been reported at least one.
    @return tuple of ct, i.e. (ct, ct, ...)
            where ct is a tuple (total_number_reported, total_comments_reported, total_reviews_reported, 
                                 total_vote_value_of_reported, total_nb_votes_of_reported, user_id, user_email, user_nickname)
            sorted by order of ct having highest total_number_reported
    """
    query1 = "SELECT c.nb_reported, c.vote_value, c.nb_votes, u.id, u.email, u.nickname, c.star_score " \
             "FROM user AS u, cmtRECORDCOMMENT AS c " \
             "WHERE c.id_user=u.id AND c.nb_reported > 0 " \
             "ORDER BY u.id "
    res1 = run_sql(query1)
    if type(res1) is None:
        return ()
    users = {}
    for cmt in res1:
        uid = int(cmt[3])
        if users.has_key(uid):
            users[uid] = (users[uid][0]+int(cmt[0]), int(cmt[6])>0 and users[uid][1] or users[uid][1]+1, int(cmt[6])>0 and users[uid][2]+1 or users[uid][2], 
                          users[uid][3]+int(cmt[1]), users[uid][4]+int(cmt[2]), int(cmt[3]), cmt[4], cmt[5])
        else:
            users[uid] = (int(cmt[0]), int(cmt[6])==0 and 1 or 0, int(cmt[6])>0 and 1 or 0, int(cmt[1]), int(cmt[2]), int(cmt[3]), cmt[4], cmt[5])
    users = users.values()
    users.sort()
    users.reverse()
    users = tuple(users)
    return users
            
def perform_request_comments(ln=cdslang, uid="", comID="", reviews=0):
    """
    """
    warning = []

    ln = wash_url_argument(ln, 'str')
    uid = wash_url_argument(uid, 'int')
    comID = wash_url_argument(comID, 'int')
    reviews = wash_url_argument(reviews, 'int')

    comments = query_get_comments(uid, comID, reviews)
    return webcomment_templates.tmpl_admin_comments(ln=ln, uid=uid, comID=comID, comment_data=comments, reviews=reviews)

def query_get_comments(uid, comID, reviews):
    """
    private funciton
    Get the reported comments of user uid or get the comment comID or get the comment comID which was written by user uid
    @return same type of tuple as that which is returned by webcomment.py/query_retrieve_comments_or_remarks i.e.
            tuple of comment where comment is
            tuple (nickname, date_creation, body, id) if ranking disabled or
            tuple (nickname, date_creation, body, vote_value, nb_votes, star_score, star_note, id)
    """
    query1 = "SELECT u.nickname, c.date_creation, c.body, %s c.id, c.id_bibrec, c.id_user, " \
             "c.nb_reported, u.id, u.email, u.nickname " \
             "FROM user AS u, cmtRECORDCOMMENT AS c " \
             "WHERE c.id_user=u.id %s %s %s " \
             "ORDER BY c.nb_reported DESC, c.vote_value DESC, c.date_creation "
    params1 = ( reviews>0 and " c.vote_value, c.nb_votes, c.star_score, c.star_note, " or "",
                reviews>0 and " AND c.star_score>0 " or " AND c.star_score=0 ",
                uid>0 and " AND c.id_user=%s " % uid or "",
                comID>0 and " AND c.id=%s " % comID or " AND c.nb_reported>0 " )
    res1 = run_sql(query1 % params1)
    res2 = []
    for qtuple1 in res1:
        # exceptional use of html here for giving admin extra information
        new_info = """          <br>user (nickname=%s, email=%s, id=%s)<br>
                                comment/review id = %s<br>
                                commented <a href="%s/search.py/index?recid=%s">this record (id=%s)</a><br>
                            </td>
                        </tr>
                        <tr>
                            <td><span class="important"><b>reported %s times</b></span></td>
                            <td>&nbsp;</td>
                            <td>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td>
                            <td align=right><input type=checkbox name="comid%s"></td>
                        </tr>
                        <tr>
                            <td>""" \
                        % (len(qtuple1[0])>0 and qtuple1[0] or qtuple1[-2].split('@')[0], 
                           qtuple1[-2], qtuple1[-5], qtuple1[-7], weburl, qtuple1[-6], qtuple1[-6], qtuple1[-4], qtuple1[-7])
        if reviews:
            qtuple2 = (len(qtuple1[0])>0 and qtuple1[0] or qtuple1[-2].split('@')[0], 
                       str(qtuple1[1])+new_info, qtuple1[2], qtuple1[3], qtuple1[4], qtuple1[5], qtuple1[6], qtuple1[7])
        else:
            qtuple2 = (len(qtuple1[0])>0 and qtuple1[0] or qtuple1[-2].split('@')[0],
                       str(qtuple1[1])+new_info, qtuple1[2], qtuple1[3])
                                                                                                                                                                                                     
        res2.append(qtuple2)
    return tuple(res2)

def perform_request_del_com(ln=cdslang, comIDs=[]):
    """
    private function
    Delete the comments and say whether successful or not
    @param ln: language
    @param comIDs: list of comment ids
    """
    ln = wash_url_argument(ln, 'str')
    comIDs = wash_url_argument(comIDs, 'list')
    # map ( fct, list, arguments of function)
    comIDs = map(wash_url_argument, comIDs, ('int '*len(comIDs)).split(' ')[:-1])

    if not comIDs:
        comIDs = map(coerce, comIDs, ('0 '*len(comIDs)).split(' ')[:-1])
        return webcomment_templates.tmpl_admin_del_com(del_res=comIDs)
 
    del_res=[]
    for id in comIDs:
        del_res.append((id, query_delete_comment(id)))
    return webcomment_templates.tmpl_admin_del_com(del_res=del_res)

def query_delete_comment(comID):
    """
    delete comment with id comID
    @return integer 1 if successful, integer 0 if not
    """
    query1 = "DELETE FROM cmtRECORDCOMMENT WHERE id=%s"
    params1 = (comID,)
    res1 = run_sql(query1, params1)
    return int(res1)

def getnavtrail(previous = ''):
    """
    Get the navtrail
    """
    
    navtrail = """<a class=navtrail href="%s/admin/">Admin Area</a> &gt; <a class=navtrail href="%s/admin/webcomment/">WebComment Admin</a> """ % (weburl, weburl)
    navtrail = navtrail + previous
    return navtrail


















