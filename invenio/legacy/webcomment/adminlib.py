# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2013, 2015 CERN.
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

from invenio.config import CFG_SITE_LANG, CFG_SITE_URL, \
     CFG_WEBCOMMENT_NB_REPORTS_BEFORE_SEND_EMAIL_TO_ADMIN
from invenio.modules.comments.config import InvenioWebCommentWarning
from invenio.modules.comments.api import query_get_comment, \
     get_reply_order_cache_data
from invenio.utils.url import wash_url_argument
from invenio.legacy.dbquery import run_sql
from invenio.base.i18n import gettext_set_language, wash_language
from invenio.ext.logging import register_exception
from invenio.legacy.webuser import get_user_info, collect_user_info, \
                            isUserAdmin
from invenio.modules.access.engine import acc_authorize_action, \
     acc_get_authorized_emails
from invenio.legacy.search_engine import perform_request_search

import invenio.legacy.template
webcomment_templates = invenio.legacy.template.load('webcomment')

def getnavtrail(previous = '', ln=CFG_SITE_LANG):
    """Get the navtrail"""
    previous = wash_url_argument(previous, 'str')
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail = """<a class="navtrail" href="%s/help/admin">%s</a> """ % (CFG_SITE_URL, _("Admin Area"))
    navtrail = navtrail + previous
    return navtrail

def get_nb_reviews(recID, count_deleted=True):
    """
    Return number of reviews for the record recID

    if count_deleted is True, deleted reviews are also counted
    """
    query = """SELECT count(*)
            FROM "cmtRECORDCOMMENT" c
            WHERE c.id_bibrec = %s and c.star_score > 0
            """

    if not count_deleted:
        query += "and c.status != 'dm' and c.status != 'da'"

    res = run_sql(query, (recID,))

    return res[0][0]

def get_nb_comments(recID, count_deleted=True):
    """
    Return number of comments for the record recID

    if count_deleted is True, deleted comments are also counted
    """
    query = """SELECT count(*)
            FROM "cmtRECORDCOMMENT" c
            WHERE c.id_bibrec = %s and c.star_score = 0
            """

    if not count_deleted:
        query += "and c.status != 'dm' and c.status != 'da'"

    res = run_sql(query, (recID,))

    return res[0][0]

def get_user_collections(req):
    """
    Return collections for which the user is moderator
    """
    user_info = collect_user_info(req)
    res = []
    collections = run_sql('SELECT name FROM collection')
    for collection in collections:
        collection_emails = acc_get_authorized_emails('moderatecomments', collection=collection[0])
        if user_info['email'] in collection_emails or isUserAdmin(user_info):
            res.append(collection[0])
    return res

def perform_request_index(ln=CFG_SITE_LANG):
    """
    """
    return webcomment_templates.tmpl_admin_index(ln=ln)

def perform_request_delete(comID=-1, recID=-1, uid=-1, reviews="", ln=CFG_SITE_LANG):
    """
    """
    _ = gettext_set_language(ln)

    from invenio.legacy.search_engine import record_exists

    warnings = []

    ln = wash_language(ln)
    comID = wash_url_argument(comID, 'int')
    recID = wash_url_argument(recID, 'int')
    uid = wash_url_argument(uid, 'int')
    # parameter reviews is deduced from comID when needed

    if comID is not None and recID is not None and uid is not None:
        if comID <= 0 and recID <= 0 and uid <= 0:
            if comID != -1:
                try:
                    raise InvenioWebCommentWarning(_('Invalid comment ID.'))
                except InvenioWebCommentWarning as exc:
                    register_exception(stream='warning')
                    warnings.append((exc.message, ''))
                #warnings.append(("WRN_WEBCOMMENT_ADMIN_INVALID_COMID",))
            return webcomment_templates.tmpl_admin_delete_form(ln, warnings)

        if comID > 0 and not recID > 0:
            comment = query_get_comment(comID)

            if comment:
                # Figure out if this is a review or a comment
                c_star_score = 5
                if comment[c_star_score] > 0:
                    reviews = 1
                else:
                    reviews = 0
                return (perform_request_comments(ln=ln, comID=comID, recID=recID, reviews=reviews), None, warnings)
            else:
                try:
                    raise InvenioWebCommentWarning(_('Comment ID %(x_name)s does not exist.', x_name=comID))
                except InvenioWebCommentWarning as exc:
                    register_exception(stream='warning')
                    warnings.append((exc.message, ''))
                #warnings.append(('WRN_WEBCOMMENT_ADMIN_COMID_INEXISTANT', comID))
                return webcomment_templates.tmpl_admin_delete_form(ln, warnings)

        elif recID > 0:
            if record_exists(recID):
                comID = ''
                reviews = wash_url_argument(reviews, 'int')
                return (perform_request_comments(ln=ln, comID=comID, recID=recID, reviews=reviews), None, warnings)
            else:
                try:
                    raise InvenioWebCommentWarning(_('Record ID %(x_rec)s does not exist.', x_rec=comID))
                except InvenioWebCommentWarning as exc:
                    register_exception(stream='warning')
                    warnings.append((exc.message, ''))
                #warnings.append(('WRN_WEBCOMMENT_ADMIN_RECID_INEXISTANT', comID))
                return webcomment_templates.tmpl_admin_delete_form(ln, warnings)
        else:
            return webcomment_templates.tmpl_admin_delete_form(ln, warnings)

    else:
        return webcomment_templates.tmpl_admin_delete_form(ln, warnings)

def perform_request_users(ln=CFG_SITE_LANG):
    """
    """
    ln = wash_language(ln)

    users_data = query_get_users_reported()
    return webcomment_templates.tmpl_admin_users(ln=ln, users_data=users_data)

def query_get_users_reported():
    """
    Get the users who have been reported at least once.
    @return: tuple of ct, i.e. (ct, ct, ...)
            where ct is a tuple (total_number_reported, total_comments_reported, total_reviews_reported,
                                 total_nb_votes_yes_of_reported, total_nb_votes_total_of_reported, user_id, user_email, user_nickname)
            sorted by order of ct having highest total_number_reported
    """
    query1 = "SELECT c.nb_abuse_reports, c.nb_votes_yes, c.nb_votes_total, u.id, u.email, u.nickname, c.star_score " \
             """FROM user AS u, "cmtRECORDCOMMENT" AS c """ \
             "WHERE c.id_user=u.id AND c.nb_abuse_reports > 0 " \
             "ORDER BY u.id "
    res1 = run_sql(query1)
    if type(res1) is None:
        return ()
    users = {}
    for cmt in res1:
        uid = int(cmt[3])
        if uid in users:
            users[uid] = (users[uid][0]+int(cmt[0]), int(cmt[6])>0 and users[uid][1] or users[uid][1]+1, int(cmt[6])>0 and users[uid][2]+1 or users[uid][2],
                          users[uid][3]+int(cmt[1]), users[uid][4]+int(cmt[2]), int(cmt[3]), cmt[4], cmt[5])
        else:
            users[uid] = (int(cmt[0]), int(cmt[6])==0 and 1 or 0, int(cmt[6])>0 and 1 or 0, int(cmt[1]), int(cmt[2]), int(cmt[3]), cmt[4], cmt[5])
    users = users.values()
    users.sort()
    users.reverse()
    users = tuple(users)
    return users

def perform_request_comments(req=None, ln=CFG_SITE_LANG, uid="", comID="", recID="", reviews=0, abuse=False, collection=""):
    """
    Display the list of comments/reviews along with information about the comment.

    Display the comment given by its ID, or the list of comments for
    the given record ID.
    If abuse == True, only list records reported as abuse.
    If comID and recID are not provided, list all comments, or all
    abused comments (check parameter 'abuse')
    """
    ln = wash_language(ln)
    uid = wash_url_argument(uid, 'int')
    comID = wash_url_argument(comID, 'int')
    recID = wash_url_argument(recID, 'int')
    reviews = wash_url_argument(reviews, 'int')
    collection = wash_url_argument(collection, 'str')

    user_info = collect_user_info(req)
    user_collections = ['Show all']
    user_collections.extend(get_user_collections(req))
    if collection and collection != 'Show all':
        (auth_code, auth_msg) = acc_authorize_action(req, 'moderatecomments', collection=collection)
        if auth_code:
            return webcomment_templates.tmpl_admin_comments(ln=ln, uid=uid,
                                                            comID=comID,
                                                            recID=recID,
                                                            comment_data=None,
                                                            reviews=reviews,
                                                            error=1,
                                                            user_collections=user_collections,
                                                            collection=collection)
    if collection:
        if recID or uid:
            comments = query_get_comments(uid, comID, recID, reviews, ln, abuse=abuse, user_collections=user_collections, collection=collection)
        else:
            comments = query_get_comments('', comID, '', reviews, ln, abuse=abuse, user_collections=user_collections, collection=collection)
    else:
        if recID or uid:
            comments = query_get_comments(uid, comID, recID, reviews, ln, abuse=abuse, user_collections=user_collections, collection=user_collections[0])
        else:
            comments = query_get_comments('', comID, '', reviews, ln, abuse=abuse, user_collections=user_collections, collection=user_collections[0])
    if comments:
        return webcomment_templates.tmpl_admin_comments(ln=ln, uid=uid,
                                                        comID=comID,
                                                        recID=recID,
                                                        comment_data=comments,
                                                        reviews=reviews,
                                                        error=0,
                                                        user_collections=user_collections,
                                                        collection=collection)
    else:
        return webcomment_templates.tmpl_admin_comments(ln=ln, uid=uid,
                                                        comID=comID,
                                                        recID=recID,
                                                        comment_data=comments,
                                                        reviews=reviews,
                                                        error=2,
                                                        user_collections=user_collections,
                                                        collection=collection)



def perform_request_hot(req=None, ln=CFG_SITE_LANG, comments=1, top=10, collection="Show all"):
    """
    Display the list of hottest comments/reviews along with information about the comment.

    @param req: request object for obtaining user information
    @param ln: language
    @param comments: boolean activated if using comments, deactivated for reviews
    @param top: specify number of results to be shown
    @param collection: filter by collection
    """
    ln = wash_language(ln)
    comments = wash_url_argument(comments, 'int')
    top = wash_url_argument(top, 'int')
    collection = wash_url_argument(collection, 'str')

    user_info = collect_user_info(req)
    user_collections = ['Show all']
    user_collections.extend(get_user_collections(req))
    if collection and collection != 'Show all':
        (auth_code, auth_msg) = acc_authorize_action(req, 'moderatecomments', collection=collection)
        if auth_code:
            return webcomment_templates.tmpl_admin_hot(ln=ln,
                                                       comment_data = None,
                                                       comments=comments, error=1, user_collections=user_collections, collection=collection)
    if collection:
        comments_retrieved = query_get_hot(comments, ln, top, user_collections, collection)
    else:
        comments_retrieved = query_get_hot(comments, ln, top, user_collections, user_collections[0])
    if comments_retrieved:
        return webcomment_templates.tmpl_admin_hot(ln=ln,
                                                   comment_data=comments_retrieved,
                                                   comments=comments, error=0, user_collections=user_collections, collection=collection)
    else:
        return webcomment_templates.tmpl_admin_hot(ln=ln,
                                                   comment_data=comments_retrieved,
                                                   comments=comments, error=2, user_collections=user_collections, collection=collection)


def perform_request_latest(req=None, ln=CFG_SITE_LANG, comments=1, top=10, collection=""):
    """
    Display the list of latest comments/reviews along with information about the comment.

    @param req: request object for obtaining user information
    @param ln: language
    @param comments: boolean activated if using comments, deactivated for reviews
    @param top: Specify number of results to be shown
    @param collection: filter by collection
    """
    ln = wash_language(ln)
    comments = wash_url_argument(comments, 'int')
    top = wash_url_argument(top, 'int')
    collection = wash_url_argument(collection, 'str')

    user_info = collect_user_info(req)
    user_collections = ['Show all']
    user_collections.extend(get_user_collections(req))
    if collection and collection != 'Show all':
        (auth_code, auth_msg) = acc_authorize_action(req, 'moderatecomments', collection=collection)
        if auth_code:
            return webcomment_templates.tmpl_admin_latest(ln=ln,
                                                          comment_data=None,
                                                          comments=comments, error=1, user_collections=user_collections, collection=collection)
    if collection:
        comments_retrieved = query_get_latest(comments, ln, top, user_collections, collection)
    else:
        comments_retrieved = query_get_latest(comments, ln, top, user_collections, user_collections[0])
    if comments_retrieved:
        return webcomment_templates.tmpl_admin_latest(ln=ln,
                                                      comment_data=comments_retrieved,
                                                      comments=comments, error=0, user_collections=user_collections, collection=collection)
    else:
        return webcomment_templates.tmpl_admin_latest(ln=ln,
                                                      comment_data=comments_retrieved,
                                                      comments=comments, error=2, user_collections=user_collections, collection=collection)


def perform_request_undel_single_com(ln=CFG_SITE_LANG, id=id):
    """
    Mark comment referenced by id as active
    """
    ln = wash_language(ln)
    id = wash_url_argument(id, 'int')

    return query_undel_single_comment(id)

def query_get_comments(uid, cmtID, recID, reviews, ln, abuse=False, user_collections='', collection=''):
    """
    private function
    @param user_collections: allowed collections for the user
    @param collection: collection to display
    @return tuple of comment where comment is
    tuple (nickname, uid, date_creation, body, id, status) if ranking disabled or
    tuple (nickname, uid, date_creation, body, nb_votes_yes, nb_votes_total, star_score, title, id, status)
    """
    qdict = {'id': 0, 'id_bibrec': 1, 'uid': 2, 'date_creation': 3, 'body': 4,
    'status': 5, 'nb_abuse_reports': 6, 'nb_votes_yes': 7, 'nb_votes_total': 8,
             'star_score': 9, 'title': 10, 'email': -2, 'nickname': -1}
    query = """SELECT c.id, c.id_bibrec, c.id_user,
                      DATE_FORMAT(c.date_creation, '%%Y-%%m-%%d %%H:%%i:%%S'), c.body,
                      c.status, c.nb_abuse_reports,
                      %s
                      u.email, u.nickname
               FROM "cmtRECORDCOMMENT" c LEFT JOIN user u
                                       ON c.id_user = u.id
               %s
               ORDER BY c.nb_abuse_reports DESC, c.nb_votes_yes DESC, c.date_creation
    """
    select_fields = reviews and 'c.nb_votes_yes, c.nb_votes_total, c.star_score, c.title,' or ''
    where_clause = "WHERE " + (reviews and 'c.star_score>0' or 'c.star_score=0')
    if uid:
        where_clause += ' AND c.id_user=%i' % uid
    if recID:
        where_clause += ' AND c.id_bibrec=%i' % recID
    if cmtID:
        where_clause += ' AND c.id=%i' % cmtID
    if abuse:
        where_clause += ' AND c.nb_abuse_reports>0'

    res = run_sql(query % (select_fields, where_clause))
    collection_records = []
    if collection == 'Show all':
        for collection_name in user_collections:
            collection_records.extend(perform_request_search(cc=collection_name))
    else:
        collection_records.extend(perform_request_search(cc=collection))
    output = []
    for qtuple in res:
        if qtuple[qdict['id_bibrec']] in collection_records:
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
                                 qtuple[qdict['id']],
                                 qtuple[qdict['status']])
            else:
                comment_tuple = (nickname,
                                 qtuple[qdict['uid']],
                                 qtuple[qdict['date_creation']],
                                 qtuple[qdict['body']],
                                 qtuple[qdict['id']],
                                 qtuple[qdict['status']])
            general_infos_tuple = (nickname,
                                   qtuple[qdict['uid']],
                                   qtuple[qdict['email']],
                                   qtuple[qdict['id']],
                                   qtuple[qdict['id_bibrec']],
                                   qtuple[qdict['nb_abuse_reports']])
            out_tuple = (comment_tuple, general_infos_tuple)
            output.append(out_tuple)
    return tuple(output)

def query_get_hot(comments, ln, top, user_collections, collection):
    """
    private function
    @param comments:  boolean indicating if we want to retrieve comments or reviews
    @param ln: language
    @param top: number of results to display
    @param user_collections: allowed collections for the user
    @param collection: collection to display
    @return: tuple (id_bibrec, date_last_comment, users, count)
    """
    qdict = {'id_bibrec': 0, 'date_last_comment': 1, 'users': 2, 'total_count': 3}
    query = """SELECT c.id_bibrec,
               DATE_FORMAT(max(c.date_creation), '%%Y-%%m-%%d %%H:%%i:%%S') as date_last_comment,
               count(distinct c.id_user) as users,
               count(*) as count
               FROM "cmtRECORDCOMMENT" c
               %s
               GROUP BY c.id_bibrec
               ORDER BY count(*) DESC
               LIMIT %s
    """
    where_clause = "WHERE " + (comments and 'c.star_score=0' or 'c.star_score>0') + """ AND c.status='ok' AND c.nb_abuse_reports < %s""" % CFG_WEBCOMMENT_NB_REPORTS_BEFORE_SEND_EMAIL_TO_ADMIN

    res = run_sql(query % (where_clause, top))

    collection_records = []
    if collection == 'Show all':
        for collection_name in user_collections:
            collection_records.extend(perform_request_search(cc=collection_name))
    else:
        collection_records.extend(perform_request_search(cc=collection))

    output = []
    for qtuple in res:
        if qtuple[qdict['id_bibrec']] in collection_records:
            general_infos_tuple = (qtuple[qdict['id_bibrec']],
                                   qtuple[qdict['date_last_comment']],
                                   qtuple[qdict['users']],
                                   qtuple[qdict['total_count']])
            output.append(general_infos_tuple)
    return tuple(output)

def query_get_latest(comments, ln, top, user_collections, collection):
    """
    private function
    @param comments:  boolean indicating if we want to retrieve comments or reviews
    @param ln: language
    @param top: number of results to display
    @param user_collections: allowed collections for the user
    @param collection: collection to display
    @return tuple of comment where comment is
    tuple (nickname, uid, date_creation, body, id) if latest comments or
    tuple (nickname, uid, date_creation, body, star_score, id) if latest reviews
    """
    qdict = {'id': 0, 'id_bibrec': 1, 'uid': 2, 'date_creation': 3, 'body': 4,
             'nb_abuse_reports': 5, 'star_score': 6, 'nickname': -1}
    query = """SELECT c.id, c.id_bibrec, c.id_user,
                      DATE_FORMAT(c.date_creation, '%%Y-%%m-%%d %%H:%%i:%%S'), c.body,
                      c.nb_abuse_reports,
                      %s
                      u.nickname
                      FROM "cmtRECORDCOMMENT" c LEFT JOIN user u
                      ON c.id_user = u.id
               %s
               ORDER BY c.date_creation DESC
               LIMIT %s
    """
    select_fields = not comments and 'c.star_score, ' or ''
    where_clause = "WHERE " + (comments and 'c.star_score=0' or 'c.star_score>0') + """ AND c.status='ok' AND c.nb_abuse_reports < %s""" % CFG_WEBCOMMENT_NB_REPORTS_BEFORE_SEND_EMAIL_TO_ADMIN

    res = run_sql(query % (select_fields, where_clause, top))

    collection_records = []
    if collection == 'Show all':
        for collection_name in user_collections:
            collection_records.extend(perform_request_search(cc=collection_name))
    else:
        collection_records.extend(perform_request_search(cc=collection))
    output = []
    for qtuple in res:
        if qtuple[qdict['id_bibrec']] in collection_records:
            nickname = qtuple[qdict['nickname']] or get_user_info(qtuple[qdict['uid']], ln)[2]
            if not comments:
                comment_tuple = (nickname,
                                 qtuple[qdict['uid']],
                                 qtuple[qdict['date_creation']],
                                 qtuple[qdict['body']],
                                 qtuple[qdict['star_score']],
                                 qtuple[qdict['id']])
            else:
                comment_tuple = (nickname,
                                 qtuple[qdict['uid']],
                                 qtuple[qdict['date_creation']],
                                 qtuple[qdict['body']],
                                 qtuple[qdict['id']])
            general_infos_tuple = (nickname,
                                   qtuple[qdict['uid']],
                                   qtuple[qdict['id']],
                                   qtuple[qdict['id_bibrec']],
                                   qtuple[qdict['nb_abuse_reports']])

            out_tuple = (comment_tuple, general_infos_tuple)
            output.append(out_tuple)
    return tuple(output)

def perform_request_del_com(ln=CFG_SITE_LANG, comIDs=[]):
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

    del_res = []
    for comID in comIDs:
        del_res.append((comID, query_delete_comment_mod(comID)))
    return webcomment_templates.tmpl_admin_del_com(del_res=del_res, ln=ln)

def perform_request_undel_com(ln=CFG_SITE_LANG, comIDs=[]):
    """
    private function
    Undelete the comments and say whether successful or not
    @param ln: language
    @param comIDs: list of comment ids
    """
    ln = wash_language(ln)
    comIDs = wash_url_argument(comIDs, 'list')
    # map ( fct, list, arguments of function)
    comIDs = map(wash_url_argument, comIDs, ('int '*len(comIDs)).split(' ')[:-1])

    if not comIDs:
        comIDs = map(coerce, comIDs, ('0 '*len(comIDs)).split(' ')[:-1])
        return webcomment_templates.tmpl_admin_undel_com(del_res=comIDs, ln=ln)

    del_res = []
    for comID in comIDs:
        del_res.append((comID, query_undel_single_comment(comID)))
    return webcomment_templates.tmpl_admin_undel_com(del_res=del_res, ln=ln)


def perform_request_del_single_com_mod(ln=CFG_SITE_LANG, id=id):
    """
    private function
    Delete a single comment requested by a moderator
    @param ln: language
    @param id: comment id to be deleted
    """
    ln = wash_language(ln)
    id = wash_url_argument(id, 'int')
    return query_delete_comment_mod(id)

def perform_request_del_single_com_auth(ln=CFG_SITE_LANG, id=id):
    """
    private function
    Delete a single comment requested by the author
    @param ln: language
    @param id: comment id to be deleted
    """
    ln = wash_language(ln)
    id = wash_url_argument(id, 'int')
    return query_delete_comment_auth(id)

def perform_request_unreport_single_com(ln=CFG_SITE_LANG, id=""):
    """
    private function
    Unreport a single comment
    @param ln: language
    @param id: comment id to be deleted
    """
    ln = wash_language(ln)
    id = wash_url_argument(id, 'int')
    return query_suppress_abuse_report(id)

def suppress_abuse_report(ln=CFG_SITE_LANG, comIDs=[]):
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

    del_res = []
    for comID in comIDs:
        del_res.append((comID, query_suppress_abuse_report(comID)))
    return webcomment_templates.tmpl_admin_suppress_abuse_report(del_res=del_res, ln=ln)

def query_suppress_abuse_report(comID):
    """ suppress abuse report for a given comment
    @return: integer 1 if successful, integer 0 if not
    """
    query = """UPDATE "cmtRECORDCOMMENT" SET nb_abuse_reports=0, status='ap' WHERE id=%s"""
    params = (comID,)
    res = run_sql(query, params)
    return int(res)

def query_delete_comment_mod(comID):
    """
    delete comment with id comID
    @return: integer 1 if successful, integer 0 if not
    """
    query1 = """UPDATE "cmtRECORDCOMMENT" SET status='dm' WHERE id=%s"""
    params1 = (comID,)
    res1 = run_sql(query1, params1)
    return int(res1)

def query_delete_comment_auth(comID):
    """
    delete comment with id comID
    @return: integer 1 if successful, integer 0 if not
    """
    query1 = """UPDATE "cmtRECORDCOMMENT" SET status='da' WHERE id=%s"""
    params1 = (comID,)
    res1 = run_sql(query1, params1)
    return int(res1)

def query_undel_single_comment(comID):
    """
    undelete comment with id comID
    @return: integer 1 if successful, integer 0 if not
    """
    query = """UPDATE "cmtRECORDCOMMENT" SET status='ok' WHERE id=%s"""
    params = (comID,)
    res = run_sql(query, params)
    return int(res)

def check_user_is_author(user_id, com_id):
    """ Check if the user is the author of the given comment """
    res = run_sql("""SELECT id, id_user FROM "cmtRECORDCOMMENT" WHERE id=%s and id_user=%s""", (str(com_id), str(user_id)))
    if res:
        return 1
    return 0

def migrate_comments_populate_threads_index():
    """
    Fill in the `reply_order_cached_data' columns in cmtRECORDCOMMENT and
    bskRECORDCOMMENT tables with adequate values so that thread
    are displayed correctly.
    """
    # Update WebComment comments
    res = run_sql("""SELECT id FROM "cmtRECORDCOMMENT" WHERE reply_order_cached_data is NULL""")
    for row in res:
        reply_order_cached_data = get_reply_order_cache_data(row[0])
        run_sql("""UPDATE "cmtRECORDCOMMENT" set reply_order_cached_data=%s WHERE id=%s""",
                (reply_order_cached_data, row[0]))

    # Update WebBasket comments
    res = run_sql("""SELECT id FROM "bskRECORDCOMMENT" WHERE reply_order_cached_data is NULL""")
    for row in res:
        reply_order_cached_data = get_reply_order_cache_data(row[0])
        run_sql("""UPDATE "cmtRECORDCOMMENT" set reply_order_cached_data=%s WHERE id=%s""",
                (reply_order_cached_data, row[0]))
