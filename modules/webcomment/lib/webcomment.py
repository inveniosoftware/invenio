# -*- coding: utf-8 -*-

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

""" Comments and reviews for records """

__revision__ = "$Id$"

# non CDS Invenio imports:
import time
import math
from datetime import datetime, timedelta

# CDS Invenio imports:

from invenio.dbquery import run_sql
from invenio.config import CFG_SITE_LANG, \
                           CFG_WEBALERT_ALERT_ENGINE_EMAIL,\
                           CFG_SITE_ADMIN_EMAIL,\
                           CFG_SITE_SUPPORT_EMAIL,\
                           CFG_WEBCOMMENT_ALERT_ENGINE_EMAIL,\
                           CFG_SITE_URL,\
                           CFG_SITE_NAME,\
                           CFG_WEBCOMMENT_ALLOW_REVIEWS,\
                           CFG_WEBCOMMENT_ALLOW_SHORT_REVIEWS,\
                           CFG_WEBCOMMENT_ALLOW_COMMENTS,\
                           CFG_WEBCOMMENT_ADMIN_NOTIFICATION_LEVEL,\
                           CFG_WEBCOMMENT_NB_REPORTS_BEFORE_SEND_EMAIL_TO_ADMIN,\
                           CFG_WEBCOMMENT_TIMELIMIT_PROCESSING_COMMENTS_IN_SECONDS,\
                           CFG_WEBCOMMENT_TIMELIMIT_PROCESSING_REVIEWS_IN_SECONDS,\
                           CFG_WEBCOMMENT_DEFAULT_MODERATOR
from invenio.webmessage_mailutils import \
     email_quote_txt, \
     email_quoted_txt2html
from invenio.webuser import get_user_info, get_email, collect_user_info
from invenio.dateutils import convert_datetext_to_dategui, \
                              datetext_default, \
                              convert_datestruct_to_datetext
from invenio.mailutils import send_email
from invenio.messages import wash_language, gettext_set_language
from invenio.urlutils import wash_url_argument
from invenio.dateutils import convert_datestruct_to_datetext
from invenio.webcomment_config import CFG_WEBCOMMENT_ACTION_CODE, \
     CFG_WEBCOMMENT_EMAIL_REPLIES_TO
from invenio.access_control_engine import acc_authorize_action
from invenio.access_control_admin import acc_is_role
from invenio.access_control_config import CFG_WEBACCESS_WARNING_MSGS
from invenio.search_engine import \
     guess_primary_collection_of_a_record, \
     check_user_can_view_record, \
     get_all_collections_of_a_record, \
     get_fieldvalues
from invenio.webcomment_washer import EmailWasher
try:
    import invenio.template
    webcomment_templates = invenio.template.load('webcomment')
except:
    pass


def perform_request_display_comments_or_remarks(req, recID, display_order='od', display_since='all', nb_per_page=100, page=1, ln=CFG_SITE_LANG, voted=-1, reported=-1, subscribed=0, reviews=0, uid=-1, can_send_comments=False, can_attach_files=False, user_is_subscribed_to_discussion=False, user_can_unsubscribe_from_discussion=False):
    """
    Returns all the comments (reviews) of a specific internal record or external basket record.
    @param recID:  record id where (internal record IDs > 0) or (external basket record IDs < -100)
    @param display_order:       hh = highest helpful score, review only
                                lh = lowest helpful score, review only
                                hs = highest star score, review only
                                ls = lowest star score, review only
                                od = oldest date
                                nd = newest date
    @param display_since:       all= no filtering by date
                                nd = n days ago
                                nw = n weeks ago
                                nm = n months ago
                                ny = n years ago
                                where n is a single digit integer between 0 and 9
    @param nb_per_page: number of results per page
    @param page: results page
    @param voted: boolean, active if user voted for a review, see perform_request_vote function
    @param reported: boolean, active if user reported a certain comment/review, perform_request_report function
    @param subscribed: int, 1 if user just subscribed to discussion, -1 if unsubscribed
    @param reviews: boolean, enabled if reviews, disabled for comments
    @param uid: the id of the user who is reading comments
    @param can_send_comments: if user can send comment or not
    @param can_attach_files: if user can attach file to comment or not
    @param user_is_subscribed_to_discussion: True if user already receives new comments by email
    @param user_can_unsubscribe_from_discussion: True is user is allowed to unsubscribe from discussion
    @return html body.
    """
    errors = []
    warnings = []
    nb_reviews = 0
    nb_comments = 0

    # wash arguments
    recID = wash_url_argument(recID, 'int')
    ln = wash_language(ln)
    display_order = wash_url_argument(display_order, 'str')
    display_since = wash_url_argument(display_since, 'str')
    nb_per_page = wash_url_argument(nb_per_page, 'int')
    page = wash_url_argument(page, 'int')
    voted = wash_url_argument(voted, 'int')
    reported = wash_url_argument(reported, 'int')
    reviews = wash_url_argument(reviews, 'int')

    # vital argument check
    (valid, error_body) = check_recID_is_in_range(recID, warnings, ln)
    if not(valid):
        return (error_body, errors, warnings)
    # Query the database and filter results
    res = query_retrieve_comments_or_remarks(recID, display_order, display_since, reviews)
    res2 = query_retrieve_comments_or_remarks(recID, display_order, display_since, not reviews)

    nb_res = len(res)
    if reviews:
        nb_reviews = nb_res
        nb_comments = len(res2)
    else:
        nb_reviews = len(res2)
        nb_comments = nb_res

    # checking non vital arguemnts - will be set to default if wrong
    #if page <= 0 or page.lower() != 'all':
    if page < 0:
        page = 1
        warnings.append(('WRN_WEBCOMMENT_INVALID_PAGE_NB',))
    if nb_per_page < 0:
        nb_per_page = 100
        warnings.append(('WRN_WEBCOMMENT_INVALID_NB_RESULTS_PER_PAGE',))
    if CFG_WEBCOMMENT_ALLOW_REVIEWS and reviews:
        if display_order not in ['od', 'nd', 'hh', 'lh', 'hs', 'ls']:
            display_order = 'hh'
            warnings.append(('WRN_WEBCOMMENT_INVALID_REVIEW_DISPLAY_ORDER',))
    else:
        if display_order not in ['od', 'nd']:
            display_order = 'od'
            warnings.append(('WRN_WEBCOMMENT_INVALID_DISPLAY_ORDER',))

    # filter results according to page and number of reults per page
    if nb_per_page > 0:
        if nb_res > 0:
            last_page = int(math.ceil(nb_res / float(nb_per_page)))
        else:
            last_page = 1
        if page > last_page:
            page = 1
            warnings.append(("WRN_WEBCOMMENT_INVALID_PAGE_NB",))
        if nb_res > nb_per_page: # if more than one page of results
            if  page < last_page:
                res = res[(page-1)*(nb_per_page) : (page*nb_per_page)]
            else:
                res = res[(page-1)*(nb_per_page) : ]
        else: # one page of results
            pass
    else:
        last_page = 1

    # Send to template
    avg_score = 0.0
    if not CFG_WEBCOMMENT_ALLOW_COMMENTS and not CFG_WEBCOMMENT_ALLOW_REVIEWS: # comments not allowed by admin
        errors.append(('ERR_WEBCOMMENT_COMMENTS_NOT_ALLOWED',))
    if reported > 0:
        warnings.append(('WRN_WEBCOMMENT_FEEDBACK_RECORDED',))
    elif reported == 0:
        warnings.append(('WRN_WEBCOMMENT_ALREADY_REPORTED',))
    elif reported == -2:
        warnings.append(('WRN_WEBCOMMENT_INVALID_REPORT',))
    if CFG_WEBCOMMENT_ALLOW_REVIEWS and reviews:
        avg_score = calculate_avg_score(res)
        if voted > 0:
            warnings.append(('WRN_WEBCOMMENT_FEEDBACK_RECORDED',))
        elif voted == 0:
            warnings.append(('WRN_WEBCOMMENT_ALREADY_VOTED',))
    if subscribed == 1:
        warnings.append(('WRN_WEBCOMMENT_SUBSCRIBED',))
    elif subscribed == -1:
        warnings.append(('WRN_WEBCOMMENT_UNSUBSCRIBED',))

    body = webcomment_templates.tmpl_get_comments(req,
                                                  recID,
                                                  ln,
                                                  nb_per_page, page, last_page,
                                                  display_order, display_since,
                                                  CFG_WEBCOMMENT_ALLOW_REVIEWS,
                                                  res, nb_comments, avg_score,
                                                  warnings,
                                                  border=0,
                                                  reviews=reviews,
                                                  total_nb_reviews=nb_reviews,
                                                  uid=uid,
                                                  can_send_comments=can_send_comments,
                                                  can_attach_files=can_attach_files,
                                                  user_is_subscribed_to_discussion=\
                                                  user_is_subscribed_to_discussion,
                                                  user_can_unsubscribe_from_discussion=\
                                                  user_can_unsubscribe_from_discussion)
    return (body, errors, warnings)

def perform_request_vote(cmt_id, client_ip_address, value, uid=-1):
    """
    Vote positively or negatively for a comment/review
    @param cmt_id: review id
    @param value: +1 for voting positively
                  -1 for voting negatively
    @return: integer 1 if successful, integer 0 if not
    """
    cmt_id = wash_url_argument(cmt_id, 'int')
    client_ip_address = wash_url_argument(client_ip_address, 'str')
    value = wash_url_argument(value, 'int')
    uid = wash_url_argument(uid, 'int')
    if cmt_id > 0 and value in [-1, 1] and check_user_can_vote(cmt_id, client_ip_address, uid):
        action_date = convert_datestruct_to_datetext(time.localtime())
        action_code = CFG_WEBCOMMENT_ACTION_CODE['VOTE']
        query = """INSERT INTO cmtACTIONHISTORY (id_cmtRECORDCOMMENT,
                    id_bibrec, id_user, client_host, action_time,
                    action_code)
                   VALUES (%s, NULL ,%s, inet_aton(%s), %s, %s)"""
        params = (cmt_id, uid, client_ip_address, action_date, action_code)
        run_sql(query, params)
        return query_record_useful_review(cmt_id, value)
    else:
        return 0

def check_user_can_comment(recID, client_ip_address, uid=-1):
    """ Check if a user hasn't already commented within the last seconds
    time limit: CFG_WEBCOMMENT_TIMELIMIT_PROCESSING_COMMENTS_IN_SECONDS
    @param recID: record id
    @param client_ip_address: IP => use: str(req.remote_ip)
    @param uid: user id, as given by invenio.webuser.getUid(req)
    """
    recID = wash_url_argument(recID, 'int')
    client_ip_address = wash_url_argument(client_ip_address, 'str')
    uid = wash_url_argument(uid, 'int')
    max_action_time = time.time() - CFG_WEBCOMMENT_TIMELIMIT_PROCESSING_COMMENTS_IN_SECONDS
    max_action_time = convert_datestruct_to_datetext(time.localtime(max_action_time))
    action_code = CFG_WEBCOMMENT_ACTION_CODE['ADD_COMMENT']
    query = """SELECT id_bibrec
               FROM cmtACTIONHISTORY
               WHERE id_bibrec=%s AND
                     action_code=%s AND
                     action_time>%s
            """
    params = (recID, action_code, max_action_time)
    if uid < 0:
        query += " AND client_host=inet_aton(%s)"
        params += (client_ip_address,)
    else:
        query += " AND id_user=%s"
        params += (uid,)
    res = run_sql(query, params)
    return len(res) == 0

def check_user_can_review(recID, client_ip_address, uid=-1):
    """ Check if a user hasn't already reviewed within the last seconds
    time limit: CFG_WEBCOMMENT_TIMELIMIT_PROCESSING_REVIEWS_IN_SECONDS
    @param recID: record ID
    @param client_ip_address: IP => use: str(req.remote_ip)
    @param uid: user id, as given by invenio.webuser.getUid(req)
    """
    action_code = CFG_WEBCOMMENT_ACTION_CODE['ADD_REVIEW']
    query = """SELECT id_bibrec
               FROM cmtACTIONHISTORY
               WHERE id_bibrec=%s AND
                     action_code=%s
            """
    params = (recID, action_code)
    if uid < 0:
        query += " AND client_host=inet_aton(%s)"
        params += (client_ip_address,)
    else:
        query += " AND id_user=%s"
        params += (uid,)
    res = run_sql(query, params)
    return len(res) == 0

def check_user_can_vote(cmt_id, client_ip_address, uid=-1):
    """ Checks if a user hasn't already voted
    @param cmt_id: comment id
    @param client_ip_address: IP => use: str(req.remote_ip)
    @param uid: user id, as given by invenio.webuser.getUid(req)
    """
    cmt_id = wash_url_argument(cmt_id, 'int')
    client_ip_address = wash_url_argument(client_ip_address, 'str')
    uid = wash_url_argument(uid, 'int')
    query = """SELECT id_cmtRECORDCOMMENT
               FROM cmtACTIONHISTORY
               WHERE id_cmtRECORDCOMMENT=%s"""
    params = (cmt_id,)
    if uid < 0:
        query += " AND client_host=inet_aton(%s)"
        params += (client_ip_address,)
    else:
        query += " AND id_user=%s"
        params += (uid, )
    res = run_sql(query, params)
    return (len(res) == 0)

def get_comment_collection(cmt_id):
    """
    Extract the collection where the comment is written
    """
    query = "SELECT id_bibrec FROM cmtRECORDCOMMENT WHERE id=%s"
    recid = run_sql(query, (cmt_id,))
    record_primary_collection = guess_primary_collection_of_a_record(recid[0][0])
    return record_primary_collection

def get_collection_moderators(collection):
    """
    Return the list of comment moderators for the given collection.
    """
    from invenio.access_control_engine import acc_get_authorized_emails

    res =  list(acc_get_authorized_emails('moderatecomments', collection=collection))
    if not res:
        return [CFG_WEBCOMMENT_DEFAULT_MODERATOR,]
    return res

def perform_request_report(cmt_id, client_ip_address, uid=-1):
    """
    Report a comment/review for inappropriate content.
    Will send an email to the administrator if number of reports is a multiple of CFG_WEBCOMMENT_NB_REPORTS_BEFORE_SEND_EMAIL_TO_ADMIN
    @param cmt_id: comment id
    @return: integer 1 if successful, integer 0 if not. -2 if comment does not exist
    """
    cmt_id = wash_url_argument(cmt_id, 'int')
    if cmt_id <= 0:
        return 0
    (query_res, nb_abuse_reports) = query_record_report_this(cmt_id)
    if query_res == 0:
        return 0
    elif query_res == -2:
        return -2
    if not(check_user_can_report(cmt_id, client_ip_address, uid)):
        return 0
    action_date = convert_datestruct_to_datetext(time.localtime())
    action_code = CFG_WEBCOMMENT_ACTION_CODE['REPORT_ABUSE']
    query = """INSERT INTO cmtACTIONHISTORY (id_cmtRECORDCOMMENT, id_bibrec,
                  id_user, client_host, action_time, action_code)
               VALUES (%s, NULL, %s, inet_aton(%s), %s, %s)"""
    params = (cmt_id, uid, client_ip_address, action_date, action_code)
    run_sql(query, params)
    if nb_abuse_reports % CFG_WEBCOMMENT_NB_REPORTS_BEFORE_SEND_EMAIL_TO_ADMIN == 0:
        (cmt_id2,
         id_bibrec,
         id_user,
         cmt_body,
         cmt_date,
         cmt_star,
         cmt_vote, cmt_nb_votes_total,
         cmt_title,
         cmt_reported) = query_get_comment(cmt_id)
        (user_nb_abuse_reports,
         user_votes,
         user_nb_votes_total) = query_get_user_reports_and_votes(int(id_user))
        (nickname, user_email, last_login) = query_get_user_contact_info(id_user)
        from_addr = '%s Alert Engine <%s>' % (CFG_SITE_NAME, CFG_WEBALERT_ALERT_ENGINE_EMAIL)
        comment_collection = get_comment_collection(cmt_id)
        to_addrs = get_collection_moderators(comment_collection)
        subject = "A comment has been reported as inappropriate by a user"
        body = '''
The following comment has been reported a total of %(cmt_reported)s times.

Author:     nickname    = %(nickname)s
            email       = %(user_email)s
            user_id     = %(uid)s
            This user has:
                total number of reports         = %(user_nb_abuse_reports)s
                %(votes)s
Comment:    comment_id      = %(cmt_id)s
            record_id       = %(id_bibrec)s
            date written    = %(cmt_date)s
            nb reports      = %(cmt_reported)s
            %(review_stuff)s
            body            =
---start body---
%(cmt_body)s
---end body---

Please go to the record page %(comment_admin_link)s to delete this message if necessary. A warning will be sent to the user in question.''' % \
                {   'cfg-report_max'        : CFG_WEBCOMMENT_NB_REPORTS_BEFORE_SEND_EMAIL_TO_ADMIN,
                    'nickname'              : nickname,
                    'user_email'            : user_email,
                    'uid'                   : id_user,
                    'user_nb_abuse_reports' : user_nb_abuse_reports,
                    'user_votes'            : user_votes,
                    'votes'                 : CFG_WEBCOMMENT_ALLOW_REVIEWS and \
                                              "total number of positive votes\t= %s\n\t\ttotal number of negative votes\t= %s" % \
                                              (user_votes, (user_nb_votes_total - user_votes)) or "\n",
                    'cmt_id'                : cmt_id,
                    'id_bibrec'             : id_bibrec,
                    'cmt_date'              : cmt_date,
                    'cmt_reported'          : cmt_reported,
                    'review_stuff'          : CFG_WEBCOMMENT_ALLOW_REVIEWS and \
                                              "star score\t= %s\n\treview title\t= %s" % (cmt_star, cmt_title) or "",
                    'cmt_body'              : cmt_body,
                    'comment_admin_link'    : CFG_SITE_URL + "/record/" + str(id_bibrec) + '/comments#' + str(cmt_id),
                    'user_admin_link'       : "user_admin_link" #! FIXME
                }

        #FIXME to be added to email when websession module is over:
        #If you wish to ban the user, you can do so via the User Admin Panel %(user_admin_link)s.

        send_email(from_addr, to_addrs, subject, body)
    return 1

def check_user_can_report(cmt_id, client_ip_address, uid=-1):
    """ Checks if a user hasn't already reported a comment
    @param cmt_id: comment id
    @param client_ip_address: IP => use: str(req.remote_ip)
    @param uid: user id, as given by invenio.webuser.getUid(req)
    """
    cmt_id = wash_url_argument(cmt_id, 'int')
    client_ip_address = wash_url_argument(client_ip_address, 'str')
    uid = wash_url_argument(uid, 'int')
    query = """SELECT id_cmtRECORDCOMMENT
               FROM cmtACTIONHISTORY
               WHERE id_cmtRECORDCOMMENT=%s"""
    params = (uid,)
    if uid < 0:
        query += " AND client_host=inet_aton(%s)"
        params += (client_ip_address,)
    else:
        query += " AND id_user=%s"
        params += (uid,)
    res = run_sql(query, params)
    return (len(res) == 0)

def query_get_user_contact_info(uid):
    """
    Get the user contact information
    @return: tuple (nickname, email, last_login), if none found return ()
    Note: for the moment, if no nickname, will return email address up to the '@'
    """
    query1 = """SELECT nickname, email,
                     DATE_FORMAT(last_login, '%%Y-%%m-%%d %%H:%%i:%%s')
                     FROM user WHERE id=%s"""
    params1 = (uid,)
    res1 = run_sql(query1, params1)
    if res1:
        return res1[0]
    else:
        return ()


def query_get_user_reports_and_votes(uid):
    """
    Retrieve total number of reports and votes of a particular user
    @param uid: user id
    @return: tuple (total_nb_reports, total_nb_votes_yes, total_nb_votes_total)
            if none found return ()
    """
    query1 = """SELECT nb_votes_yes,
                       nb_votes_total,
                       nb_abuse_reports
                FROM cmtRECORDCOMMENT
                WHERE id_user=%s"""
    params1 = (uid,)
    res1 = run_sql(query1, params1)
    if len(res1) == 0:
        return ()
    nb_votes_yes = nb_votes_total = nb_abuse_reports = 0
    for cmt_tuple in res1:
        nb_votes_yes += int(cmt_tuple[0])
        nb_votes_total += int(cmt_tuple[1])
        nb_abuse_reports += int(cmt_tuple[2])
    return (nb_abuse_reports, nb_votes_yes, nb_votes_total)

def query_get_comment(comID):
    """
    Get all fields of a comment
    @param comID: comment id
    @return: tuple (comID, id_bibrec, id_user, body, date_creation, star_score, nb_votes_yes, nb_votes_total, title, nb_abuse_reports)
            if none found return ()
    """
    query1 = """SELECT id,
                       id_bibrec,
                       id_user,
                       body,
                       DATE_FORMAT(date_creation, '%%Y-%%m-%%d %%H:%%i:%%s'),
                       star_score,
                       nb_votes_yes,
                       nb_votes_total,
                       title,
                       nb_abuse_reports
                FROM cmtRECORDCOMMENT
                WHERE id=%s"""
    params1 = (comID,)
    res1 = run_sql(query1, params1)
    if len(res1)>0:
        return res1[0]
    else:
        return ()

def query_record_report_this(comID):
    """
    Increment the number of reports for a comment
    @param comID: comment id
    @return: tuple (success, new_total_nb_reports_for_this_comment) where
    success is integer 1 if success, integer 0 if not, -2 if comment does not exist
    """
    #retrieve nb_abuse_reports
    query1 = "SELECT nb_abuse_reports FROM cmtRECORDCOMMENT WHERE id=%s"
    params1 = (comID,)
    res1 = run_sql(query1, params1)
    if len(res1) == 0:
        return (-2, 0)

    #increment and update
    nb_abuse_reports = int(res1[0][0]) + 1
    query2 = "UPDATE cmtRECORDCOMMENT SET nb_abuse_reports=%s WHERE id=%s"
    params2 = (nb_abuse_reports, comID)
    res2 = run_sql(query2, params2)
    return (int(res2), nb_abuse_reports)

def query_record_useful_review(comID, value):
    """
    private funciton
    Adjust the number of useful votes and number of total votes for a comment.
    @param comID: comment id
    @param value: +1 or -1
    @return: integer 1 if successful, integer 0 if not
    """
    # retrieve nb_useful votes
    query1 = "SELECT nb_votes_total, nb_votes_yes FROM cmtRECORDCOMMENT WHERE id=%s"
    params1 = (comID,)
    res1 = run_sql(query1, params1)
    if len(res1)==0:
        return 0

    # modify and insert new nb_useful votes
    nb_votes_yes = int(res1[0][1])
    if value >= 1:
        nb_votes_yes = int(res1[0][1]) + 1
    nb_votes_total = int(res1[0][0]) + 1
    query2 = "UPDATE cmtRECORDCOMMENT SET nb_votes_total=%s, nb_votes_yes=%s WHERE id=%s"
    params2 = (nb_votes_total, nb_votes_yes, comID)
    res2 = run_sql(query2, params2)
    return int(res2)

def query_retrieve_comments_or_remarks (recID, display_order='od', display_since='0000-00-00 00:00:00',
                                        ranking=0):
    """
    Private function
    Retrieve tuple of comments or remarks from the database
    @param recID: record id
    @param display_order:   hh = highest helpful score
                            lh = lowest helpful score
                            hs = highest star score
                            ls = lowest star score
                            od = oldest date
                            nd = newest date
    @param display_since: datetime, e.g. 0000-00-00 00:00:00
    @param ranking: boolean, enabled if reviews, disabled for comments
    @return: tuple of comment where comment is
            tuple (nickname, uid, date_creation, body, status, id) if ranking disabled or
            tuple (nickname, uid, date_creation, body, status, nb_votes_yes, nb_votes_total, star_score, title, id)
    Note: for the moment, if no nickname, will return email address up to '@'
    """
    display_since = calculate_start_date(display_since)

    order_dict =    {   'hh'   : "cmt.nb_votes_yes/(cmt.nb_votes_total+1) DESC, cmt.date_creation DESC ",
                        'lh'   : "cmt.nb_votes_yes/(cmt.nb_votes_total+1) ASC, cmt.date_creation ASC ",
                        'ls'   : "cmt.star_score ASC, cmt.date_creation DESC ",
                        'hs'   : "cmt.star_score DESC, cmt.date_creation DESC ",
                        'od'   : "cmt.date_creation ASC ",
                        'nd'   : "cmt.date_creation DESC "
                    }

    # Ranking only done for comments and when allowed
    if ranking and recID > 0:
        try:
            display_order = order_dict[display_order]
        except:
            display_order = order_dict['od']
    else:
        # in case of recID > 0 => external record => no ranking!
        ranking = 0
    try:
        if display_order[-1] == 'd':
            display_order = order_dict[display_order]
        else:
            display_order = order_dict['od']
    except:
        display_order = order_dict['od']

    #display_order = order_dict['nd']
    query = """SELECT user.nickname,
                      cmt.id_user,
                      DATE_FORMAT(cmt.date_creation, '%%%%Y-%%%%m-%%%%d %%%%H:%%%%i:%%%%s'),
                      cmt.body,
                      cmt.status,
                      cmt.nb_abuse_reports,
                      %(ranking)s cmt.id
               FROM   %(table)s cmt LEFT JOIN user ON
                                              user.id=cmt.id_user
               WHERE %(id_bibrec)s=%%s
               %(ranking_only)s
               %(display_since)s
               ORDER BY %%s
               """ % {'ranking'       : ranking and ' cmt.nb_votes_yes, cmt.nb_votes_total, cmt.star_score, cmt.title, ' or '',
                      'ranking_only'  : ranking and ' AND cmt.star_score>0 ' or ' AND cmt.star_score=0 ',
                      'id_bibrec'     : recID > 0 and 'cmt.id_bibrec' or 'cmt.id_bibrec_or_bskEXTREC',
                      'table'         : recID > 0 and 'cmtRECORDCOMMENT' or 'bskRECORDCOMMENT',
                      'display_since' : display_since == '0000-00-00 00:00:00' and ' ' or 'AND cmt.date_creation>=\'%s\' ' % display_since}
    params = (recID, display_order)
    res = run_sql(query, params)

    if res:
        return res
    return ()

def query_add_comment_or_remark(reviews=0, recID=0, uid=-1, msg="",
                                note="", score=0, priority=0,
                                client_ip_address='', editor_type='textarea'):
    """
    Private function
    Insert a comment/review or remarkinto the database
    @param recID: record id
    @param uid: user id
    @param msg: comment body
    @param note: comment title
    @param score: review star score
    @param priority: remark priority #!FIXME
    @param editor_type: the kind of editor used to submit the comment: 'textarea', 'fckeditor'
    @return: integer >0 representing id if successful, integer 0 if not
    """
    current_date = calculate_start_date('0d')
    #change utf-8 message into general unicode
    msg = msg.decode('utf-8')
    note = note.decode('utf-8')
    #change general unicode back to utf-8
    msg = msg.encode('utf-8')
    note = note.encode('utf-8')

    if editor_type == 'fckeditor':
        # Here we remove the line feeds introduced by FCKeditor (they
        # have no meaning for the user) and replace the HTML line
        # breaks by linefeeds, so that we are close to an input that
        # would be done without the FCKeditor. That's much better if a
        # reply to a comment is made with a browser that does not
        # support FCKeditor.
        msg = msg.replace('\n', '').replace('\r', '').replace('<br />', '\n')
    query = """INSERT INTO cmtRECORDCOMMENT (id_bibrec,
                                           id_user,
                                           body,
                                           date_creation,
                                           star_score,
                                           nb_votes_total,
                                           title)
                VALUES (%s, %s, %s, %s, %s, %s, %s)"""
    params = (recID, uid, msg, current_date, score, 0, note)
    res = run_sql(query, params)
    if res:
        action_code = CFG_WEBCOMMENT_ACTION_CODE[reviews and 'ADD_REVIEW' or 'ADD_COMMENT']
        action_time = convert_datestruct_to_datetext(time.localtime())
        query2 = """INSERT INTO cmtACTIONHISTORY  (id_cmtRECORDCOMMENT,
                     id_bibrec, id_user, client_host, action_time, action_code)
                    VALUES ('', %s, %s, inet_aton(%s), %s, %s)"""
        params2 = (recID, uid, client_ip_address, action_time, action_code)
        run_sql(query2, params2)

        # Email this comment to 'subscribers'
        (subscribers_emails1, subscribers_emails2) = \
                              get_users_subscribed_to_discussion(recID)
        email_subscribers_about_new_comment(recID, reviews=reviews,
                                            emails1=subscribers_emails1,
                                            emails2=subscribers_emails2,
                                            comID=res, msg=msg,
                                            note=note, score=score,
                                            editor_type=editor_type, uid=uid)
        return int(res)

def subscribe_user_to_discussion(recID, uid):
    """
    Subscribe a user to a discussion, so the she receives by emails
    all new new comments for this record.

    @param recID: record ID corresponding to the discussion we want to
                  subscribe the user
    @param uid: user id
    """
    query = """INSERT INTO cmtSUBSCRIPTION (id_bibrec, id_user, creation_time)
                    VALUES (%s, %s, %s)"""
    params = (recID, uid, convert_datestruct_to_datetext(time.localtime()))
    try:
        run_sql(query, params)
    except:
        return 0
    return 1

def unsubscribe_user_from_discussion(recID, uid):
    """
    Unsubscribe users from a discussion.

    @param recID: record ID corresponding to the discussion we want to
                  unsubscribe the user
    @param uid: user id
    @return 1 if successful, 0 if not
    """
    query = """DELETE FROM cmtSUBSCRIPTION
                     WHERE id_bibrec=%s AND id_user=%s"""
    params = (recID, uid)
    try:
        res = run_sql(query, params)
    except:
        return 0
    if res > 0:
        return 1
    return 0

def get_user_subscription_to_discussion(recID, uid):
    """
    Returns the type of subscription for the given user to this
    discussion.
    @param recID: record ID
    @param uid: user id
    @return:
               - 0 if user is not subscribed to discussion
               - 1 if user is subscribed, and is allowed to unsubscribe
               - 2 if user is subscribed, but cannot unsubscribe
    """
    user_email = get_email(uid)
    (emails1, emails2) = get_users_subscribed_to_discussion(recID, check_authorizations=False)
    if user_email in emails1:
        return 1
    elif user_email in emails2:
        return 2
    else:
        return 0

def get_users_subscribed_to_discussion(recID, check_authorizations=True):
    """
    Returns the lists of users subscribed to a given discussion.

    Two lists are returned: the first one is the list of emails for
    users who can unsubscribe from the discussion, the second list
    contains the emails of users who cannot unsubscribe (for eg. author
    of the document, etc).

    Users appear in only one list. If a user has manually subscribed
    to a discussion AND is an automatic recipients for updates, it
    will only appear in the second list.

    @param recID: record ID for which we want to retrieve subscribed users
    @param check_authorizations: if True, check again if users are authorized to view comment
    @return tuple (emails1, emails2)
    """
    subscribers_emails = {}

    # Get users that have subscribed to this discussion
    query = """SELECT id_user FROM cmtSUBSCRIPTION WHERE id_bibrec=%s"""
    params = (recID,)
    res = run_sql(query, params)
    for row in res:
        uid = row[0]
        user_info = collect_user_info(uid)
        (auth_code, auth_msg) = check_user_can_view_comments(user_info, recID)
        if auth_code:
            # User is no longer authorized to view comments.
            # Delete subscription
            unsubscribe_user_from_discussion(recID, uid)
        else:
            email = get_email(uid)
            if '@' in email:
                subscribers_emails[email] = True

    # Get users automatically subscribed, based on the record metadata
    collections = get_all_collections_of_a_record(recID)
    primary_collection = guess_primary_collection_of_a_record(recID)
    if primary_collection not in collections:
        collections.append(primary_collection)
    for collection in collections:
        if CFG_WEBCOMMENT_EMAIL_REPLIES_TO.has_key(collection):
            fields = CFG_WEBCOMMENT_EMAIL_REPLIES_TO[collection]
            for field in fields:
                emails = get_fieldvalues(recID, field)
                for email in emails:
                    if not '@' in email:
                        # Is a group: add domain name
                        subscribers_emails[email + '@' + \
                                           CFG_SITE_SUPPORT_EMAIL.split('@')[1]] = False
                    else:
                        subscribers_emails[email] = False

    return ([email for email, can_unsubscribe_p \
             in subscribers_emails.iteritems() if can_unsubscribe_p],
            [email for email, can_unsubscribe_p \
             in subscribers_emails.iteritems() if not can_unsubscribe_p] )

def email_subscribers_about_new_comment(recID, reviews, emails1,
                                        emails2, comID, msg="",
                                        note="", score=0,
                                        editor_type='textarea',
                                        ln=CFG_SITE_LANG, uid=-1):
    """
    Notify subscribers that a new comment was posted.
    FIXME: consider recipient preference to send email in correct language.

    @param recID: record id
    @param emails1: list of emails for users who can unsubscribe from discussion
    @param emails2: list of emails for users who cannot unsubscribe from discussion
    @param comID: the comment id
    @param msg: comment body
    @param note: comment title
    @param score: review star score
    @param editor_type: the kind of editor used to submit the comment: 'textarea', 'fckeditor'
    @rtype: bool
    @return: True if email was sent okay, False if it was not.
    """
    _ = gettext_set_language(ln)

    if not emails1 and not emails2:
        return 0

    # Get title
    titles = get_fieldvalues(recID, "245__a")
    if not titles:
        # usual title not found, try conference title:
        titles = get_fieldvalues(recID, "111__a")

    title = ''
    if titles:
        title = titles[0]
    else:
        title = _("Record %i") % recID

    # Get report number
    report_numbers = get_fieldvalues(recID, "037__a")
    if not report_numbers:
        report_numbers = get_fieldvalues(recID, "088__a")
        if not report_numbers:
            report_numbers = get_fieldvalues(recID, "021__a")

    # Prepare email subject and body
    if reviews:
        email_subject = _('%(report_number)s"%(title)s" has been reviewed') % \
                        {'report_number': report_numbers and ('[' + report_numbers[0] + '] ') or '',
                         'title': title}
    else:
        email_subject = _('%(report_number)s"%(title)s" has been commented') % \
                        {'report_number': report_numbers and ('[' + report_numbers[0] + '] ') or '',
                         'title': title}

    washer = EmailWasher()
    msg = washer.wash(msg)
    email_content = msg
    if note:
        email_content = note + email_content

    # Send emails to people who can unsubscribe
    email_header = webcomment_templates.tmpl_email_new_comment_header(recID,
                                                                      title,
                                                                      reviews,
                                                                      comID,
                                                                      report_numbers,
                                                                      can_unsubscribe=True,
                                                                      ln=ln,
                                                                      uid=uid)

    email_footer = webcomment_templates.tmpl_email_new_comment_footer(recID,
                                                                      title,
                                                                      reviews,
                                                                      comID,
                                                                      report_numbers,
                                                                      can_unsubscribe=True,
                                                                      ln=ln)
    res1 = True
    if emails1:
        res1 = send_email(fromaddr=CFG_WEBCOMMENT_ALERT_ENGINE_EMAIL,
                          toaddr=emails1,
                          subject=email_subject,
                          content=email_content,
                          header=email_header,
                          footer=email_footer,
                          ln=ln)

    # Then send email to people who have been automatically
    # subscribed to the discussion (they cannot unsubscribe)
    email_header = webcomment_templates.tmpl_email_new_comment_header(recID,
                                                                      title,
                                                                      reviews,
                                                                      comID,
                                                                      report_numbers,
                                                                      can_unsubscribe=False,
                                                                      ln=ln,
                                                                      uid=uid)

    email_footer = webcomment_templates.tmpl_email_new_comment_footer(recID,
                                                                      title,
                                                                      reviews,
                                                                      comID,
                                                                      report_numbers,
                                                                      can_unsubscribe=False,
                                                                      ln=ln)
    res2 = True
    if emails2:
        res2 = send_email(fromaddr=CFG_WEBCOMMENT_ALERT_ENGINE_EMAIL,
                          toaddr=emails2,
                          subject=email_subject,
                          content=email_content,
                          header=email_header,
                          footer=email_footer,
                          ln=ln)

    return res1 and res2

def calculate_start_date(display_since):
    """
    Private function
    Returns the datetime of display_since argument in MYSQL datetime format
    calculated according to the local time.
    @param display_since: =  all= no filtering
                            nd = n days ago
                            nw = n weeks ago
                            nm = n months ago
                            ny = n years ago
                            where n is a single digit number
    @return: string of wanted datetime.
            If 'all' given as argument, will return datetext_default
            datetext_default is defined in miscutils/lib/dateutils and
            equals 0000-00-00 00:00:00 => MySQL format
            If bad arguement given, will return datetext_default
    """
    time_types = {'d':0, 'w':0, 'm':0, 'y':0}
    today = datetime.today()
    try:
        nb = int(display_since[:-1])
    except:
        return datetext_default
    if (display_since==(None or 'all')):
        return datetext_default
    if str(display_since[-1]) in time_types:
        time_type = str(display_since[-1])
    else:
        return datetext_default
    # year
    if time_type == 'y':
        if (int(display_since[:-1]) > today.year - 1) or (int(display_since[:-1]) < 1):
            #   1 < nb years < 2008
            return datetext_default
        else:
            final_nb_year = today.year - nb
            yesterday = today.replace(year=final_nb_year)
    # month
    elif time_type == 'm':
        # to convert nb of monthes in years
        nb_year = nb / 12                        # nb_year = number of year to substract
        nb = nb % 12
        if nb > today.month-1:                    # ex: july(07)-9 monthes = -1year -3monthes
            nb_year += 1
            nb_month = 12 - (today.month % nb)
        else:
            nb_month = today.month - nb
        final_nb_year = today.year - nb_year      # final_nb_year = number of year to print
        yesterday = today.replace(year=final_nb_year, month=nb_month)
    # week
    elif time_type == 'w':
        delta = timedelta(weeks=nb)
        yesterday = today - delta
    # day
    elif time_type == 'd':
        delta = timedelta(days=nb)
        yesterday = today - delta
    return yesterday.strftime("%Y-%m-%d %H:%M:%S")

def count_comments(recID):
    """
    Returns the number of comments made on a record.
    """
    recID = int(recID)
    query = """SELECT count(id) FROM cmtRECORDCOMMENT
                                WHERE id_bibrec=%s AND star_score=0"""
    return run_sql(query, (recID,))[0][0]

def count_reviews(recID):
    """
    Returns the number of reviews made on a record.
    """
    recID = int(recID)
    query = """SELECT count(id) FROM cmtRECORDCOMMENT
                                WHERE id_bibrec=%s AND star_score>0"""
    return run_sql(query, (recID,))[0][0]

def get_first_comments_or_remarks(recID=-1,
                                  ln=CFG_SITE_LANG,
                                  nb_comments='all',
                                  nb_reviews='all',
                                  voted=-1,
                                  reported=-1):
    """
    Gets nb number comments/reviews or remarks.
    In the case of comments, will get both comments and reviews
    Comments and remarks sorted by most recent date, reviews sorted by highest helpful score
    @param recID: record id
    @param ln: language
    @param nb_comments: number of comment or remarks to get
    @param nb_reviews: number of reviews or remarks to get
    @param voted: 1 if user has voted for a remark
    @param reported: 1 if user has reported a comment or review
    @return: if comment, tuple (comments, reviews) both being html of first nb comments/reviews
            if remark, tuple (remakrs, None)
    """
    warnings = []
    errors = []
    voted = wash_url_argument(voted, 'int')
    reported = wash_url_argument(reported, 'int')

    ## check recID argument
    if type(recID) is not int:
        return ()
    if recID >= 1: #comment or review. NB: suppressed reference to basket (handled in webbasket)
        if CFG_WEBCOMMENT_ALLOW_REVIEWS:
            res_reviews = query_retrieve_comments_or_remarks(recID=recID, display_order="hh", ranking=1)
            nb_res_reviews = len(res_reviews)
            ## check nb argument
            if type(nb_reviews) is int and nb_reviews < len(res_reviews):
                first_res_reviews = res_reviews[:nb_reviews]
            else:
                first_res_reviews = res_reviews
        if CFG_WEBCOMMENT_ALLOW_COMMENTS:
            res_comments = query_retrieve_comments_or_remarks(recID=recID, display_order="od", ranking=0)
            nb_res_comments = len(res_comments)
            ## check nb argument
            if type(nb_comments) is int and nb_comments < len(res_comments):
                first_res_comments = res_comments[:nb_comments]
            else:
                first_res_comments = res_comments
    else: #error
        errors.append(('ERR_WEBCOMMENT_RECID_INVALID', recID)) #!FIXME dont return error anywhere since search page

    # comment
    if recID >= 1:
        comments = reviews = ""
        if reported > 0:
            warnings.append(('WRN_WEBCOMMENT_FEEDBACK_RECORDED_GREEN_TEXT',))
        elif reported == 0:
            warnings.append(('WRN_WEBCOMMENT_FEEDBACK_NOT_RECORDED_RED_TEXT',))
        if CFG_WEBCOMMENT_ALLOW_COMMENTS: # normal comments
            comments = webcomment_templates.tmpl_get_first_comments_without_ranking(recID, ln, first_res_comments, nb_res_comments, warnings)
        if CFG_WEBCOMMENT_ALLOW_REVIEWS: # ranked comments
            #calculate average score
            avg_score = calculate_avg_score(res_reviews)
            if voted > 0:
                warnings.append(('WRN_WEBCOMMENT_FEEDBACK_RECORDED_GREEN_TEXT',))
            elif voted == 0:
                warnings.append(('WRN_WEBCOMMENT_FEEDBACK_NOT_RECORDED_RED_TEXT',))
            reviews = webcomment_templates.tmpl_get_first_comments_with_ranking(recID, ln, first_res_reviews, nb_res_reviews, avg_score, warnings)
        return (comments, reviews)
    # remark
    else:
        return(webcomment_templates.tmpl_get_first_remarks(first_res_comments, ln, nb_res_comments), None)

def calculate_avg_score(res):
    """
    private function
    Calculate the avg score of reviews present in res
    @param res: tuple of tuple returned from query_retrieve_comments_or_remarks
    @return: a float of the average score rounded to the closest 0.5
    """
    c_star_score = 6
    avg_score = 0.0
    nb_reviews = 0
    for comment in res:
        if comment[c_star_score] > 0:
            avg_score += comment[c_star_score]
            nb_reviews += 1
    if nb_reviews ==  0:
        return 0.0
    avg_score = avg_score / nb_reviews
    avg_score_unit = avg_score - math.floor(avg_score)
    if avg_score_unit < 0.25:
        avg_score = math.floor(avg_score)
    elif avg_score_unit > 0.75:
        avg_score = math.floor(avg_score) + 1
    else:
        avg_score = math.floor(avg_score) + 0.5
    if avg_score > 5:
        avg_score = 5.0
    return avg_score

def perform_request_add_comment_or_remark(recID=0,
                                          uid=-1,
                                          action='DISPLAY',
                                          ln=CFG_SITE_LANG,
                                          msg=None,
                                          score=None,
                                          note=None,
                                          priority=None,
                                          reviews=0,
                                          comID=-1,
                                          client_ip_address=None,
                                          editor_type='textarea',
                                          can_attach_files=False,
                                          subscribe=False):
    """
    Add a comment/review or remark
    @param recID: record id
    @param uid: user id
    @param action:  'DISPLAY' to display add form
                    'SUBMIT' to submit comment once form is filled
                    'REPLY' to reply to an existing comment
    @param ln: language
    @param msg: the body of the comment/review or remark
    @param score: star score of the review
    @param note: title of the review
    @param priority: priority of remark (int)
    @param reviews: boolean, if enabled will add a review, if disabled will add a comment
    @param comID: if replying, this is the comment id of the commetn are replying to
    @param editor_type: the kind of editor/input used for the comment: 'textarea', 'fckeditor'
    @param can_attach_files: if user can attach files to comments or not
    @param subscribe: if True, subscribe user to receive new comments by email
    @return:
             - html add form if action is display or reply
             - html successful added form if action is submit
    """
    warnings = []
    errors = []

    actions = ['DISPLAY', 'REPLY', 'SUBMIT']
    _ = gettext_set_language(ln)

    ## check arguments
    check_recID_is_in_range(recID, warnings, ln)
    if uid <= 0:
        errors.append(('ERR_WEBCOMMENT_UID_INVALID', uid))
        return ('', errors, warnings)

    user_contact_info = query_get_user_contact_info(uid)
    nickname = ''
    if user_contact_info:
        if user_contact_info[0]:
            nickname = user_contact_info[0]
    # show the form
    if action == 'DISPLAY':
        if reviews and CFG_WEBCOMMENT_ALLOW_REVIEWS:
            return (webcomment_templates.tmpl_add_comment_form_with_ranking(recID, uid, nickname, ln, msg, score, note, warnings, can_attach_files=can_attach_files), errors, warnings)
        elif not reviews and CFG_WEBCOMMENT_ALLOW_COMMENTS:
            return (webcomment_templates.tmpl_add_comment_form(recID, uid, nickname, ln, msg, warnings, can_attach_files=can_attach_files), errors, warnings)
        else:
            errors.append(('ERR_WEBCOMMENT_COMMENTS_NOT_ALLOWED',))

    elif action == 'REPLY':
        if reviews and CFG_WEBCOMMENT_ALLOW_REVIEWS:
            errors.append(('ERR_WEBCOMMENT_REPLY_REVIEW',))
            return (webcomment_templates.tmpl_add_comment_form_with_ranking(recID, uid, nickname, ln, msg, score, note, warnings, can_attach_files=can_attach_files), errors, warnings)
        elif not reviews and CFG_WEBCOMMENT_ALLOW_COMMENTS:
            textual_msg = msg
            if comID > 0:
                comment = query_get_comment(comID)
                if comment:
                    user_info = get_user_info(comment[2])
                    if user_info:
                        date_creation = convert_datetext_to_dategui(str(comment[4]))
                        # Build two msg: one mostly textual, the other one with HTML markup, for the FCKeditor.
                        msg = _("%(x_name)s wrote on %(x_date)s:")% {'x_name': user_info[2], 'x_date': date_creation}
                        textual_msg = msg
                        # 1 For FCKeditor input
                        msg += '<br /><br />'
                        msg += comment[3]
                        msg = email_quote_txt(text=msg)
                        msg = email_quoted_txt2html(text=msg)
                        msg = '<br/>' + msg + '<br/>'
                        # 2 For textarea input
                        textual_msg += "\n\n"
                        textual_msg += comment[3]
                        textual_msg = email_quote_txt(text=textual_msg)
            return (webcomment_templates.tmpl_add_comment_form(recID, uid, nickname, ln, msg, warnings, textual_msg, can_attach_files=can_attach_files), errors, warnings)
        else:
            errors.append(('ERR_WEBCOMMENT_COMMENTS_NOT_ALLOWED',))

    # check before submitting form
    elif action == 'SUBMIT':
        if reviews and CFG_WEBCOMMENT_ALLOW_REVIEWS:
            if note.strip() in ["", "None"] and not CFG_WEBCOMMENT_ALLOW_SHORT_REVIEWS:
                warnings.append(('WRN_WEBCOMMENT_ADD_NO_TITLE',))
            if score == 0 or score > 5:
                warnings.append(("WRN_WEBCOMMENT_ADD_NO_SCORE",))
        if msg.strip() in ["", "None"] and not CFG_WEBCOMMENT_ALLOW_SHORT_REVIEWS:
            warnings.append(('WRN_WEBCOMMENT_ADD_NO_BODY',))
        # if no warnings, submit
        if len(warnings) == 0:
            if reviews:
                if check_user_can_review(recID, client_ip_address, uid):
                    success = query_add_comment_or_remark(reviews, recID=recID, uid=uid, msg=msg,
                                                          note=note, score=score, priority=0,
                                                          client_ip_address=client_ip_address,
                                                          editor_type=editor_type)
                else:
                    warnings.append('WRN_WEBCOMMENT_CANNOT_REVIEW_TWICE')
                    success = 1
            else:
                if check_user_can_comment(recID, client_ip_address, uid):
                    success = query_add_comment_or_remark(reviews, recID=recID, uid=uid, msg=msg,
                                                          note=note, score=score, priority=0,
                                                          client_ip_address=client_ip_address,
                                                          editor_type=editor_type)
                    if success > 0 and subscribe:
                        subscribe_user_to_discussion(recID, uid)
                else:
                    warnings.append('WRN_WEBCOMMENT_TIMELIMIT')
                    success = 1
            if success > 0:
                if CFG_WEBCOMMENT_ADMIN_NOTIFICATION_LEVEL > 0:
                    notify_admin_of_new_comment(comID=success)
                return (webcomment_templates.tmpl_add_comment_successful(recID, ln, reviews, warnings, success), errors, warnings)
            else:
                errors.append(('ERR_WEBCOMMENT_DB_INSERT_ERROR'))
        # if are warnings or if inserting comment failed, show user where warnings are
        if reviews and CFG_WEBCOMMENT_ALLOW_REVIEWS:
            return (webcomment_templates.tmpl_add_comment_form_with_ranking(recID, uid, nickname, ln, msg, score, note, warnings, can_attach_files=can_attach_files), errors, warnings)
        else:
            return (webcomment_templates.tmpl_add_comment_form(recID, uid, nickname, ln, msg, warnings, can_attach_files=can_attach_files), errors, warnings)
    # unknown action send to display
    else:
        warnings.append(('WRN_WEBCOMMENT_ADD_UNKNOWN_ACTION',))
        if reviews and CFG_WEBCOMMENT_ALLOW_REVIEWS:
            return (webcomment_templates.tmpl_add_comment_form_with_ranking(recID, uid, ln, msg, score, note, warnings, can_attach_files=can_attach_files), errors, warnings)
        else:
            return (webcomment_templates.tmpl_add_comment_form(recID, uid, ln, msg, warnings, can_attach_files=can_attach_files), errors, warnings)

    return ('', errors, warnings)

def notify_admin_of_new_comment(comID):
    """
    Sends an email to the admin with details regarding comment with ID = comID
    """
    comment = query_get_comment(comID)
    if len(comment) > 0:
        (comID2,
         id_bibrec,
         id_user,
         body,
         date_creation,
         star_score, nb_votes_yes, nb_votes_total,
         title,
         nb_abuse_reports) = comment
    else:
        return
    user_info = query_get_user_contact_info(id_user)
    if len(user_info) > 0:
        (nickname, email, last_login) = user_info
        if not len(nickname) > 0:
            nickname = email.split('@')[0]
    else:
        nickname = email = last_login = "ERROR: Could not retrieve"

    review_stuff = '''
    Star score  = %s
    Title       = %s''' % (star_score, title)

    washer = EmailWasher()
    body = washer.wash(body)

    record_info = webcomment_templates.tmpl_email_new_comment_admin(id_bibrec)
    out = '''
The following %(comment_or_review)s has just been posted (%(date)s).

AUTHOR:
    Nickname    = %(nickname)s
    Email       = %(email)s
    User ID     = %(uid)s

RECORD CONCERNED:
    Record ID   = %(recID)s
%(record_details)s

%(comment_or_review_caps)s:
    %(comment_or_review)s ID    = %(comID)s %(review_stuff)s
    Body        =
<--------------->
%(body)s

<--------------->
ADMIN OPTIONS:
To moderate the %(comment_or_review)s go to %(siteurl)s/record/%(recID)s/%(comments_or_reviews)s/display?%(arguments)s
    ''' % \
        {   'comment_or_review'     : star_score >  0 and 'review' or 'comment',
            'comment_or_review_caps': star_score > 0 and 'REVIEW' or 'COMMENT',
            'comments_or_reviews'   : star_score >  0 and 'reviews' or 'comments',
            'date'                  : date_creation,
            'nickname'              : nickname,
            'email'                 : email,
            'uid'                   : id_user,
            'recID'                 : id_bibrec,
            'record_details'        : record_info,
            'comID'                 : comID2,
            'review_stuff'          : star_score > 0 and review_stuff or "",
            'body'                  : body.replace('<br />','\n'),
            'siteurl'               : CFG_SITE_URL,
            'arguments'             : 'ln=en&do=od#%s' % comID
        }

    from_addr = '%s WebComment <%s>' % (CFG_SITE_NAME, CFG_WEBALERT_ALERT_ENGINE_EMAIL)
    comment_collection = get_comment_collection(comID)
    to_addrs = get_collection_moderators(comment_collection)

    rec_collection = guess_primary_collection_of_a_record(id_bibrec)
    report_nums = get_fieldvalues(id_bibrec, "037__a")
    report_nums += get_fieldvalues(id_bibrec, "088__a")
    report_nums = ', '.join(report_nums)
    subject = "A new comment/review has just been posted [%s|%s]" % (rec_collection, report_nums)

    send_email(from_addr, to_addrs, subject, out)

def check_recID_is_in_range(recID, warnings=[], ln=CFG_SITE_LANG):
    """
    Check that recID is >= 0
    Append error messages to errors listi
    @param recID: record id
    @param warnings: the warnings list of the calling function
    @return: tuple (boolean, html) where boolean (1=true, 0=false)
                                  and html is the body of the page to display if there was a problem
    """
    # Make errors into a list if needed
    if type(warnings) is not list:
        errors = [warnings]
    try:
        recID = int(recID)
    except:
        pass

    if type(recID) is int:
        if recID > 0:
            from invenio.search_engine import record_exists
            success = record_exists(recID)
            if success == 1:
                return (1,"")
            else:
                warnings.append(('ERR_WEBCOMMENT_RECID_INEXISTANT', recID))
                return (0, webcomment_templates.tmpl_record_not_found(status='inexistant', recID=recID, ln=ln))
        elif recID == 0:
            warnings.append(('ERR_WEBCOMMENT_RECID_MISSING',))
            return (0, webcomment_templates.tmpl_record_not_found(status='missing', recID=recID, ln=ln))
        else:
            warnings.append(('ERR_WEBCOMMENT_RECID_INVALID', recID))
            return (0, webcomment_templates.tmpl_record_not_found(status='invalid', recID=recID, ln=ln))
    else:
        warnings.append(('ERR_WEBCOMMENT_RECID_NAN', recID))
        return (0, webcomment_templates.tmpl_record_not_found(status='nan', recID=recID, ln=ln))

def check_int_arg_is_in_range(value, name, errors, gte_value, lte_value=None):
    """
    Check that variable with name 'name' >= gte_value and optionally <= lte_value
    Append error messages to errors list
    @param value: variable value
    @param name: variable name
    @param errors: list of error tuples (error_id, value)
    @param gte_value: greater than or equal to value
    @param lte_value: less than or equal to value
    @return: boolean (1=true, 0=false)
    """
    # Make errors into a list if needed
    if type(errors) is not list:
        errors = [errors]

    if type(value) is not int or type(gte_value) is not int:
        errors.append(('ERR_WEBCOMMENT_PROGRAMNING_ERROR',))
        return 0

    if type(value) is not int:
        errors.append(('ERR_WEBCOMMENT_ARGUMENT_NAN', value))
        return 0

    if value < gte_value:
        errors.append(('ERR_WEBCOMMENT_ARGUMENT_INVALID', value))
        return 0
    if lte_value:
        if type(lte_value) is not int:
            errors.append(('ERR_WEBCOMMENT_PROGRAMNING_ERROR',))
            return 0
        if value > lte_value:
            errors.append(('ERR_WEBCOMMENT_ARGUMENT_INVALID', value))
            return 0
    return 1

def get_mini_reviews(recid, ln=CFG_SITE_LANG):
    """
    Returns the web controls to add reviews to a record from the
    detailed record pages mini-panel.

    @param recid: the id of the displayed record
    @param ln: the user's language
    """
    if CFG_WEBCOMMENT_ALLOW_SHORT_REVIEWS:
        action = 'SUBMIT'
    else:
        action = 'DISPLAY'

    reviews = query_retrieve_comments_or_remarks(recid, ranking=1)

    return webcomment_templates.tmpl_mini_review(recid, ln, action=action,
                                                 avg_score=calculate_avg_score(reviews),
                                                 nb_comments_total=len(reviews))

def check_user_can_view_comments(user_info, recid):
    """Check if the user is authorized to view comments for given
    recid.
    Returns the same type as acc_authorize_action
    """
    # Check user can view the record itself first
    (auth_code, auth_msg) = check_user_can_view_record(user_info, recid)
    if auth_code:
        return (auth_code, auth_msg)

    # Check if user can view the comments
    ## But first can we find an authorization for this case action,
    ## for this collection?
    record_primary_collection = guess_primary_collection_of_a_record(recid)
    return acc_authorize_action(user_info, 'viewcomment', authorized_if_no_roles=True, collection=record_primary_collection)

def check_user_can_send_comments(user_info, recid):
    """Check if the user is authorized to comment the given
    recid. This function does not check that user can view the record
    or view the comments

    Returns the same type as acc_authorize_action
    """
    ## First can we find an authorization for this case, action + collection
    record_primary_collection = guess_primary_collection_of_a_record(recid)
    return acc_authorize_action(user_info, 'sendcomment', authorized_if_no_roles=True, collection=record_primary_collection)

def check_user_can_attach_file_to_comments(user_info, recid):
    """Check if the user is authorized to attach a file to comments
    for given recid. This function does not check that user can view
    the comments or send comments.

    Returns the same type as acc_authorize_action
    """
    ## First can we find an authorization for this case action, for
    ## this collection?
    record_primary_collection = guess_primary_collection_of_a_record(recid)
    return acc_authorize_action(user_info, 'attachcommentfile', authorized_if_no_roles=True, collection=record_primary_collection)
