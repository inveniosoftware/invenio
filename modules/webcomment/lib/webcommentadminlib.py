# -*- coding: utf-8 -*-
## $Id$
## Comments and reviews for records. 
## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

__lastupdated__ = """$Date$"""

from cdsware.config import cdslang, weburl
from cdsware.webcomment import query_get_comment
from cdsware.urlutils import wash_url_argument
from cdsware.dbquery import run_sql
from cdsware.messages import gettext_set_language, wash_language
from cdsware.webuser import get_user_info

import cdsware.template
webcomment_templates = cdsware.template.load('webcomment')

def getnavtrail(previous = '', ln=cdslang):
    """Get the navtrail"""
    previous = wash_url_argument(previous, 'str')
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail = """<a class=navtrail href="%s/admin/">%s</a> &gt; <a class=navtrail href="%s/admin/webcomment/">%s</a> """ % (weburl, _("Admin Area"), weburl, _("WebComment Admin"))
    navtrail = navtrail + previous
    return navtrail

def perform_request_index(ln=cdslang):
    """
    """ 
    return webcomment_templates.tmpl_admin_index(ln=ln)

def perform_request_delete(comID=-1, ln=cdslang):
    """
    """
    warnings = []

    ln = wash_language(ln)
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
    ln = wash_language(ln)

    users_data = query_get_users_reported()
    return webcomment_templates.tmpl_admin_users(ln=ln, users_data=users_data)

def query_get_users_reported():
    """
    Get the users who have been reported at least one.
    @return tuple of ct, i.e. (ct, ct, ...)
            where ct is a tuple (total_number_reported, total_comments_reported, total_reviews_reported, 
                                 total_nb_votes_yes_of_reported, total_nb_votes_total_of_reported, user_id, user_email, user_nickname)
            sorted by order of ct having highest total_number_reported
    """
    query1 = "SELECT c.nb_abuse_reports, c.nb_votes_yes, c.nb_votes_total, u.id, u.email, u.nickname, c.star_score " \
             "FROM user AS u, cmtRECORDCOMMENT AS c " \
             "WHERE c.id_user=u.id AND c.nb_abuse_reports > 0 " \
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
    ln = wash_language(ln)
    uid = wash_url_argument(uid, 'int')
    comID = wash_url_argument(comID, 'int')
    reviews = wash_url_argument(reviews, 'int')
    
    comments = query_get_comments(uid, comID, reviews, ln)
    return webcomment_templates.tmpl_admin_comments(ln=ln, uid=uid,
                                                    comID=comID,
                                                    comment_data=comments,
                                                    reviews=reviews)

def query_get_comments(uid, cmtID, reviews, ln):
    """
    private function
    tuple of comment where comment is
    tuple (nickname, uid, date_creation, body, id) if ranking disabled or
    tuple (nickname, uid, date_creation, body, nb_votes_yes, nb_votes_total, star_score, title, id)
    """
    qdict = {'id': 0, 'id_bibrec': 1, 'uid': 2, 'date_creation': 3, 'body': 4,
             'nb_abuse_reports': 5, 'nb_votes_yes': 6, 'nb_votes_total': 7,
             'star_score': 8, 'title': 9, 'email': -2, 'nickname': -1}
    query = """SELECT c.id, c.id_bibrec, c.id_user,
                      c.date_creation, c.body,
                      c.nb_abuse_reports,
                      %s
                      u.email, u.nickname
               FROM cmtRECORDCOMMENT c LEFT JOIN user u
                                       ON c.id_user = u.id
               %s
               ORDER BY c.nb_abuse_reports DESC, c.nb_votes_yes DESC, c.date_creation
    """
    select_fields = reviews and 'c.nb_votes_yes, c.nb_votes_total, c.star_score, c.title,' or ''
    where_clause = "WHERE " + (reviews and 'c.star_score>0' or 'c.star_score=0')
    if uid:
        where_clause += ' AND c.id_user=%i' % uid
    if cmtID:
        where_clause += ' AND c.id=%i' % cmtID
    else:
        where_clause += ' AND c.nb_abuse_reports>0'
    res = run_sql(query % (select_fields, where_clause))
    output = []
    for qtuple in res:
        nickname = qtuple[qdict['nickname']] or get_user_info(qtuple[qdict['uid']], ln)[2]
        if reviews:
            comment_tuple = (nickname,
                             qtuple[qdict['uid']],
                             qtuple[qdict['date_creation']],
                             qtuple[qdict['body']],
                             qtuple[qdict['nb_votes_yes']],
                             qtuple[qdict['nb_votes_total']],
                             qtuple[qdict['star_score']],
                             qtuple[qdict['title']],
                             qtuple[qdict['id']])
        else:
            comment_tuple = (nickname,
                             qtuple[qdict['uid']],
                             qtuple[qdict['date_creation']],
                             qtuple[qdict['body']],
                             qtuple[qdict['id']])
        general_infos_tuple = (nickname,
                               qtuple[qdict['uid']],
                               qtuple[qdict['email']],
                               qtuple[qdict['id']],
                               qtuple[qdict['id_bibrec']],
                               qtuple[qdict['nb_abuse_reports']])
        out_tuple = (comment_tuple, general_infos_tuple)
        output.append(out_tuple)
    return tuple(output)

def perform_request_del_com(ln=cdslang, comIDs=[]):
    """
    private function
    Delete the comments and say whether successful or not
    @param ln: language
    @param comIDs: list of comment ids
    """
    ln = wash_language(ln)
    comIDs = wash_url_argument(comIDs, 'list')
    # map ( fct, list, arguments of function)
    comIDs = map(wash_url_argument, comIDs, ('int '*len(comIDs)).split(' ')[:-1])

    if not comIDs:
        comIDs = map(coerce, comIDs, ('0 '*len(comIDs)).split(' ')[:-1])
        return webcomment_templates.tmpl_admin_del_com(del_res=comIDs, ln=ln)
 
    del_res=[]
    for id in comIDs:
        del_res.append((id, query_delete_comment(id)))
    return webcomment_templates.tmpl_admin_del_com(del_res=del_res, ln=ln)

def suppress_abuse_report(ln=cdslang, comIDs=[]):
    """
    private function
    suppress the abuse reports for the given comIDs.
    @param ln: language
    @param comIDs: list of ids to suppress attached reports.
    """
    ln = wash_language(ln)
    comIDs = wash_url_argument(comIDs, 'list')
    # map ( fct, list, arguments of function)
    comIDs = map(wash_url_argument, comIDs, ('int '*len(comIDs)).split(' ')[:-1])

    if not comIDs:
        comIDs = map(coerce, comIDs, ('0 '*len(comIDs)).split(' ')[:-1])
        return webcomment_templates.tmpl_admin_del_com(del_res=comIDs, ln=ln)
 
    del_res=[]
    for id in comIDs:
        del_res.append((id, query_suppress_abuse_report(id)))
    return webcomment_templates.tmpl_admin_suppress_abuse_report(del_res=del_res, ln=ln)

def query_suppress_abuse_report(comID):
    """ suppress abuse report for a given comment
    @return integer 1 if successful, integer 0 if not
    """
    query = "UPDATE cmtRECORDCOMMENT SET nb_abuse_reports=0 WHERE id=%i"
    params = comID
    res = run_sql(query%params)
    return int(res)
    
def query_delete_comment(comID):
    """
    delete comment with id comID
    @return integer 1 if successful, integer 0 if not
    """
    query1 = "DELETE FROM cmtRECORDCOMMENT WHERE id=%s"
    params1 = (comID,)
    res1 = run_sql(query1, params1)
    return int(res1)
