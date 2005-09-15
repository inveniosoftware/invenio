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

# non CDSware imports:
from email.Utils import quote
import time
import math
import string
from cgi import escape 

# import CDSware stuff:
from webcomment_config import *
from dbquery import run_sql
from config import cdslang
from elmsubmit_html2txt import html2txt

import template
webcomment_templates = template.load('webcomment')

def perform_request_display_comments_or_remarks(recID, ln=cdslang, display_order='od', display_since='all', nb_per_page=100, page=1, voted=-1, reported=-1, reviews=0):
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
    @param reviews: boolean, enabled if reviews, disabled for comments
    @return html body. 
    """

    errors = []
    warnings = []

    # wash arguments
    recID= wash_url_argument(recID, 'int')
    ln = wash_url_argument(ln, 'str')
    display_order = wash_url_argument(display_order, 'str')
    display_since = wash_url_argument(display_since, 'str')
    nb_per_page = wash_url_argument(nb_per_page, 'int')
    page = wash_url_argument(page, 'int')
    voted = wash_url_argument(voted, 'int')
    reported = wash_url_argument(reported, 'int')
    reviews = wash_url_argument(reviews, 'int')

    # vital argument check
    check_recID_is_in_range(recID, warnings, ln)

    # Query the database and filter results
    res = query_retrieve_comments_or_remarks(recID, display_order, display_since, reviews)
    nb_res = len(res)

    # chekcing non vital arguemnts - will be set to default if wrong
    #if page <= 0 or page.lower() != 'all':
    if page < 0:
        page = 1
        warnings.append(('WRN_WEBCOMMENT_INVALID_PAGE_NB',))
    if nb_per_page < 0:
        nb_per_page = 100
        warnings.append(('WRN_WEBCOMMENT_INVALID_NB_RESULTS_PER_PAGE',))
    if cfg_webcomment_allow_reviews and reviews:
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
    # record is an internal record
    if recID >  0: 
        avg_score = 0.0
        if not cfg_webcomment_allow_comments and not cfg_webcomment_allow_reviews: # comments not allowed by admin
            errors.append(('ERR_WEBCOMMENT_COMMENTS_NOT_ALLOWED',))
        if reported > 0:
            warnings.append(('WRN_WEBCOMMENT_FEEDBACK_RECORDED_GREEN_TEXT',))
        elif reported == 0:
            warnings.append(('WRN_WEBCOMMENT_FEEDBACK_NOT_RECORDED_RED_TEXT',))
        if cfg_webcomment_allow_reviews and reviews:
            avg_score = calculate_avg_score(res)
            if voted>0:
                warnings.append(('WRN_WEBCOMMENT_FEEDBACK_RECORDED_GREEN_TEXT',))
            elif voted == 0:
                warnings.append(('WRN_WEBCOMMENT_FEEDBACK_NOT_RECORDED_RED_TEXT',))
        body = webcomment_templates.tmpl_get_comments(recID, ln, nb_per_page, page, last_page, display_order, display_since, cfg_webcomment_allow_reviews, res, 
                                                      nb_res, avg_score, warnings, border=0, reviews=reviews)
        return (body, errors, warnings)
    # record is an external record    
    else: 
        return ("TODO", errors, warnings) #!FIXME

def perform_request_vote(comID, value):
    """
    Vote positively or negatively for a comment/review
    @param comID: review id
    @param value: +1 for voting positively
                  -1 for voting negatively
    @return integer 1 if successful, integer 0 if not
    """
    #FIXME should record IP address and not allow voters to vote more than once
    comID = wash_url_argument(comID, 'int')
    value = wash_url_argument(value, 'int')
    if comID > 0 and value in [-1, 1]:
        return query_record_useful_review(comID, value)
    else:
        return 0

def perform_request_report(comID):
    """
    Report a comment/review for inappropriate content.
    Will send an email to the administrator if number of reports is a multiple of config.py/cfg_comment_nb_reports_before_send_email_to_admin
    @param comID: comment id
    @return integer 1 if successful, integer 0 if not
    """
    #FIXME should record IP address and not allow reporters to report more than once
    comID = wash_url_argument(comID, 'int')
    if comID <= 0:
        return 0
    (query_res, nb_abuse_reports) = query_record_report_this(comID)
    if query_res == 0:
        return 0
    if nb_abuse_reports % cfg_webcomment_nb_reports_before_send_email_to_admin == 0:
        (comID2, id_bibrec, id_user, com_body, com_date, com_star, com_vote, com_nb_votes_total, com_title, com_reported) = query_get_comment(comID)
        (user_nb_abuse_reports, user_votes, user_nb_votes_total) = query_get_user_reports_and_votes(int(id_user))
        (nickname, user_email, last_login) = query_get_user_contact_info(id_user)
        from_addr = 'CDS Alert Engine <%s>' % alertengineemail
        to_addr = adminemail
        subject = "An error report has been sent from a user"
        body = '''
The following comment has been reported a total of %(com_reported)s times.

Author:     nickname    = %(nickname)s
            email       = %(user_email)s 
            user_id     = %(uid)s
            This user has:
                total number of reports         = %(user_nb_abuse_reports)s 
                %(votes)s
Comment:    comment_id      = %(comID)s
            record_id       = %(id_bibrec)s
            date written    = %(com_date)s 
            nb reports      = %(com_reported)s 
            %(review_stuff)s
            body            =
---start body---
%(com_body)s
---end body---

Please go to the Comments Admin Panel %(comment_admin_link)s to delete this message if necessary. A warning will be sent to the user in question.''' % \
                {   'cfg-report_max'        : cfg_webcomment_nb_reports_before_send_email_to_admin,
                    'nickname'              : nickname,
                    'user_email'            : user_email,
                    'uid'                   : id_user,
                    'user_nb_abuse_reports'      : user_nb_abuse_reports,
                    'user_votes'            : user_votes,
                    'votes'                 : cfg_webcomment_allow_reviews and \
                                              "total number of positive votes\t= %s\n\t\t\t\ttotal number of negative votes\t= %s" % \
                                              (user_votes, (user_nb_votes_total - user_votes)) or "\n",
                    'comID'                 : comID, 
                    'id_bibrec'             : id_bibrec,
                    'com_date'              : com_date,
                    'com_reported'          : com_reported,
                    'review_stuff'          : cfg_webcomment_allow_reviews and \
                                              "star score\t\t= %s\n\t\t\treview title\t\t= %s" % (com_star, com_title) or "",
                    'com_body'              : com_body,
                    'comment_admin_link'    : "http://%s/admin/webcomment/" % weburl, 
                    'user_admin_link'       : "user_admin_link" #! FIXME
                }

        #FIXME to be added to email
        #If you wish to ban the user, you can do so via the User Admin Panel %(user_admin_link)s.
        
        from alert_engine import send_email, forge_email
        body = forge_email(from_addr, to_addr, subject, body)
        send_email(from_addr, to_addr, body)
    return 1

def query_get_user_contact_info(uid):
    """
    Get the user contact information
    @return tuple (nickname, email, last_login), if none found return ()
    Note: for the moment, if no nickname, will return email address up to the '@'
    """
    query1 = "SELECT email, nickname, last_login FROM user WHERE id=%s"
    params1 = (uid,)
    res1 = run_sql(query1, params1)
    if len(res1)==0:
        return ()
    #!FIXME - extra code because still possible to have no nickname
    res2 = list(res1[0])
    if not res2[1]:
        res2[1] = res2[0].split('@')[0]
    return (res2[1], res2[0], res2[2])
#    return (res1[0][1], res1[0][0], res1[0][2])

def query_get_user_reports_and_votes(uid):
    """
    Retrieve total number of reports and votes of a particular user
    @param uid: user id
    @return tuple (total_nb_reports, total_nb_votes_yes, total_nb_votes_total)
            if none found return ()
    """
    query1 = "SELECT nb_votes_yes, nb_votes_total, nb_abuse_reports FROM cmtRECORDCOMMENT WHERE id_user=%s"
    params1 = (uid,)
    res1 = run_sql(query1, params1)
    if len(res1)==0:
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
    @return tuple (comID, id_bibrec, id_user, body, date_creation, star_score, nb_votes_yes, nb_votes_total, title, nb_abuse_reports)
            if none found return ()
    """
    query1 = "SELECT id, id_bibrec, id_user, body, date_creation, star_score, nb_votes_yes, nb_votes_total, title, nb_abuse_reports FROM cmtRECORDCOMMENT WHERE id=%s"
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
    @return tuple (success, new_total_nb_reports_for_this_comment) where success is integer 1 if success, integer 0 if not
            if none found, return ()
    """
    #retrieve nb_abuse_reports
    query1 = "SELECT nb_abuse_reports FROM cmtRECORDCOMMENT WHERE id=%s"
    params1 = (comID,)
    res1 = run_sql(query1, params1)
    if len(res1)==0:
        return ()

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
    @return integer 1 if successful, integer 0 if not
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

def query_retrieve_comments_or_remarks (recID, display_order='od', display_since='0000-00-00 00:00:00', ranking=0):
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
    @return tuple of comment where comment is 
            tuple (nickname, date_creation, body, id) if ranking disabled or 
            tuple (nickname, date_creation, body, nb_votes_yes, nb_votes_total, star_score, title, id)
    Note: for the moment, if no nickname, will return email address up to '@'
    """
    display_since = calculate_start_date(display_since)

    order_dict =    {   'hh'   : "c.nb_votes_yes/(c.nb_votes_total+1) DESC, c.date_creation DESC ", 
                        'lh'   : "c.nb_votes_yes/(c.nb_votes_total+1) ASC, c.date_creation ASC ",
                        'ls'   : "c.star_score ASC, c.date_creation DESC ",
                        'hs'   : "c.star_score DESC, c.date_creation DESC ",
                        'od'   : "c.date_creation ASC ",
                        'nd'   : "c.date_creation DESC "
                    } 

    #FIXME: temporary fix due to new basket tables not existing yet.
    if recID < 1:
        return ()

    # Ranking only done for comments and when allowed
    if ranking:
        try:
            display_order = order_dict[display_order] 
        except:
            display_order = order_dict['od'] 
    else:
        try:
            if display_order[-1] == 'd':
                display_order = order_dict[display_order]
            else:
                display_order = order_dict['od']
        except:
            display_order = order_dict['od']

    query = "SELECT u.nickname, c.date_creation, c.body, %(ranking)s c.id " \
            "FROM %(table)s AS c, user AS u " \
            "WHERE %(id_bibrec)s=\'%(recID)s\' " \
            "AND c.id_user=u.id "\
            "%(ranking_only)s " \
            "%(display_since)s " \
            "ORDER BY %(display_order)s " 

    params = {  'ranking'       : ranking and ' c.nb_votes_yes, c.nb_votes_total, c.star_score, c.title, ' or '',
                'ranking_only'  : ranking and ' AND c.star_score>0 ' or ' AND c.star_score=0 ',
                'id_bibrec'     : recID>0 and 'c.id_bibrec' or 'c.id_bskBASKET_bibrec_bskEXTREC',
                'table'         : recID>0 and 'cmtRECORDCOMMENT' or 'bskREMARK',
                'recID'         : recID,
                'display_since' : display_since=='0000-00-00 00:00:00' and ' ' or 'AND c.date_creation>=\'%s\' ' % display_since, 
                'display_order' : display_order      
            }
    # return run_sql(query % params)
    #FIXME - Extra horrible code cause nickname can still be blank
    res = run_sql(query % params) #!FIXME
    res2= []
    for comment in res:
        if not comment[0]:
            comment2 = list(comment)
            user_id = query_get_comment(comment[-1])[2]
            comment2[0] = query_get_user_contact_info(user_id)[1].split('@')[0]
            res2.append(comment2)
        else:
            res2.append(comment)
    return tuple(res2)

def query_add_comment_or_remark(recID=-1, uid=-1, msg="", note="", score=0, priority=0):
    """ 
    Private function
    Insert a comment/review or remarkinto the database
    @param recID: record id
    @param uid: user id
    @param msg: comment body
    @param note: comment title
    @param score: review star score
    @param priority: remark priority #!FIXME
    @return integer >0 representing id if successful, integer 0 if not
    """
    current_date = calculate_start_date('0d')
    if recID > 0:
        #change utf-8 message into general unicode
        msg = msg.decode('utf-8')
        note = note.decode('utf-8')
        # get rid of html tags in msg but keep newlines
        msg = msg.replace ('\n', "#br#")
        msg= html2txt(msg)
        msg = msg.replace('#br#', '<br>')
        note= html2txt(note)
        #change general unicode back to utf-8
        msg = msg.encode('utf-8')
        note = note.encode('utf-8')
        query = "INSERT INTO cmtRECORDCOMMENT (id_bibrec, id_user, body, date_creation, star_score, nb_votes_total, title) " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)" 
        params = (recID, uid, msg, current_date, score, 0, note)
    else:
        #change utf-8 message into general unicode
        msg = msg.decode('utf-8')
        # get rid of html tags in msg but keep newlines
        msg = msg.replace ('\n', "#br#")
        msg= html2txt(msg)
        msg = msg.replace('#br#', '<br>')
        #change general unicode back to utf-8
        msg = msg.encode('utf-8')
        query = "INSERT INTO bskREMARK (id_bskBASKET_bibrec_bibEXTREC, id_user, body, date_creation, priority) " \
                "VALUES (%s, %s, %s, %s, %s)"
        params = (recID, uid, msg, current_date, priority) 

    return int(run_sql(query, params))

def calculate_start_date(display_since):
    """ 
    Private function
    Returns the datetime of display_since argument in MYSQL datetime format
    calculated according to the local time.
    @param display_since =  all= no filtering
                            nd = n days ago
                            nw = n weeks ago
                            nm = n months ago
                            ny = n years ago
                            where n is a single digit number
    @return string of wanted datetime.
            If 'all' given as argument, will return "0000-00-00 00:00:00"
            If bad arguement given, will return "0000-00-00 00:00:00"
    """
    # time type and seconds coefficients 
    time_types = {'d':0,'w':0,'m':0,'y':0}

    ## verify argument
    # argument wrong size
    if (display_since==(None or 'all')) or (len(display_since) > 2):
        return ("0000-00-00 00:00:00")
    try:
        nb = int(display_since[0])
    except:
        return ("0000-00-00 00:00:00")
    if str(display_since[1]) in time_types:
        time_type = str(display_since[1])
    else:
        return ("0000-00-00 00:00:00")

    ## calculate date
    # initialize the coef
    if time_type == 'w':
        time_types[time_type] = 7
    else:
        time_types[time_type] = 1

    start_time = time.localtime(time.time())
    start_time = time.mktime((   start_time[0] - nb*time_types['y'],
                        start_time[1] - nb*time_types['m'],
                        start_time[2] - nb*time_types['d'] - nb*time_types['w'],
                        start_time[3],
                        start_time[4],
                        start_time[5],
                        start_time[6],
                        start_time[7],
                        start_time[8]))
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time))

def get_first_comments_or_remarks(recID=-1, ln=cdslang, nb_comments='all', nb_reviews='all', voted=-1, reported=-1):
    """
    Gets nb number comments/reviews or remarks.
    In the case of comments, will get both comments and reviews
    Comments and remarks sorted by most recent date, reviews sorted by highest helpful score
    @param recID: record id
    @param ln: language
    @param nb: number of comment/reviews or remarks to get
    @param voted: 1 if user has voted for a remark 
    @param reported: 1 if user has reported a comment or review 
    @return if comment, tuple (comments, reviews) both being html of first nb comments/reviews
            if remark, tuple (remakrs, None)
    """
    warnings = []
    errors = []
    voted = wash_url_argument(voted, 'int')
    reported = wash_url_argument(reported, 'int')

    ## check recID argument 
    if type(recID) is not int:
        return ()
    if recID >= 1 or recID <= -100: #comment or remark
        if cfg_webcomment_allow_reviews:
            res_reviews = query_retrieve_comments_or_remarks(recID=recID, display_order="hh", ranking=1) 
            nb_res_reviews = len(res_reviews)
            ## check nb argument
            if type(nb_reviews) is int and nb_reviews < len(res_reviews):
                first_res_reviews = res_reviews[:nb_reviews]
            else:
                if nb_res_reviews  > cfg_webcomment_nb_reviews_in_detailed_view:
                    first_res_reviews = res_reviews[:cfg_comment_nb_reports_before_send_email_to_admin]
                else:
                    first_res_reviews = res_reviews
        if cfg_webcomment_allow_comments:
            res_comments = query_retrieve_comments_or_remarks(recID=recID, display_order="od", ranking=0)
            nb_res_comments = len(res_comments)
            ## check nb argument
            if type(nb_comments) is int and nb_comments < len(res_comments):
                first_res_comments = res_comments[:nb_comments]
            else:
                if nb_res_comments  > cfg_webcomment_nb_comments_in_detailed_view:
                    first_res_comments = res_comments[:cfg_webcomment_nb_comments_in_detailed_view]
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
        if cfg_webcomment_allow_comments: # normal comments
            comments = webcomment_templates.tmpl_get_first_comments_without_ranking(recID, ln, first_res_comments, nb_res_comments, warnings)
        if cfg_webcomment_allow_reviews: # ranked comments
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
    @return a float of the average score rounded to the closest 0.5
    """

    c_nickname = 0
    c_date_creation = 1
    c_body = 2
    c_nb_votes_yes = 3
    c_nb_votes_total = 4
    c_star_score = 5
    c_title = 6
    c_id = 7

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

def perform_request_add_comment_or_remark(recID=-1, uid=-1, action='DISPLAY', ln=cdslang, msg=None, score=None, note=None, priority=None, reviews=0, comID=-1):
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
    @param priority: priority of remark
    @param reviews: boolean, if enabled will add a review, if disabled will add a comment
    @param comID: if replying, this is the comment id of the commetn are replying to
    @return html add form if action is display or reply 
            html successful added form if action is submit
    """

    warnings = []
    errors = []

    actions = ['DISPLAY', 'REPLY', 'SUBMIT']
    ## wash arguments
    recID = wash_url_argument(recID, 'int')
    uid   = wash_url_argument(uid, 'int')
    msg   = wash_url_argument(msg, 'str')
    score = wash_url_argument(score, 'int')     
    note  = wash_url_argument(note, 'str')
    priority = wash_url_argument(priority, 'int')
    reviews = wash_url_argument(reviews, 'int')
    comID = wash_url_argument(comID, 'int')

    ## check arguments
    check_recID_is_in_range(recID, warnings, ln)
    if uid <= 0:
        errors.append(('ERR_WEBCOMMENT_UID_INVALID', uid))
    else:
        nickname = query_get_user_contact_info(uid)[0]

    # show the form 
    if action == 'DISPLAY':
        if reviews and cfg_webcomment_allow_reviews:
            return (webcomment_templates.tmpl_add_comment_form_with_ranking(recID, uid, nickname, ln, msg, score, note, warnings), errors, warnings)
        elif not reviews and cfg_webcomment_allow_comments:
            return (webcomment_templates.tmpl_add_comment_form(recID, uid, nickname, ln, msg, warnings), errors, warnings)
        else:
            errors.append(('ERR_WEBCOMMENT_COMMENTS_NOT_ALLOWED',))
    
    elif action == 'REPLY':
        if reviews and cfg_webcomment_allow_reviews:
            errors.append(('ERR_WEBCOMMENT_REPLY_REVIEW',))
            return (webcomment_templates.tmpl_add_comment_form_with_ranking(recID, uid, nickname, ln, msg, score, note, warnings), errors, warnings)
        elif not reviews and cfg_webcomment_allow_comments:
            if comID>0:
                comment = query_get_comment(comID)
                if comment: 
                    user_info = query_get_user_contact_info(comment[2])
                    if user_info:
                        msg = comment[3].replace('\n', ' ')
                        msg = msg.replace('<br>', '\n')
                        msg = "Quoting %s:\n%s\n" % (user_info[0], msg)
            return (webcomment_templates.tmpl_add_comment_form(recID, uid, nickname, ln, msg, warnings), errors, warnings)
        else:
            errors.append(('ERR_WEBCOMMENT_COMMENTS_NOT_ALLOWED',))

    # check before submitting form
    elif action == 'SUBMIT':
        if reviews and cfg_webcomment_allow_reviews:
            if note.strip() in ["", "None"]:
                warnings.append(('WRN_WEBCOMMENT_ADD_NO_TITLE',))
            if score == 0 or score > 5:
                warnings.append(("WRN_WEBCOMMENT_ADD_NO_SCORE",))
        if msg.strip() in ["", "None"]:
            warnings.append(('WRN_WEBCOMMENT_ADD_NO_BODY',))
        # if no warnings, submit
        if len(warnings) == 0:
            success = query_add_comment_or_remark(recID=recID, uid=uid, msg=msg, note=note, score=score, priority=0)
            if success > 0:
                if cfg_webcomment_admin_notification_level > 0:
                    notify_admin_of_new_comment(comID=success)
                return (webcomment_templates.tmpl_add_comment_successful(recID, ln, reviews), errors, warnings)
            else:
                errors.append(('ERR_WEBCOMMENT_DB_INSERT_ERROR',))
        # if are warnings or if inserting comment failed, show user where warnings are
        if reviews and cfg_webcomment_allow_reviews:
            return (webcomment_templates.tmpl_add_comment_form_with_ranking(recID, uid, nickname, ln, msg, score, note, warnings), errors, warnings)
        else:
            return (webcomment_templates.tmpl_add_comment_form(recID, uid, nickname, ln, msg, warnings), errors, warnings)
    # unknown action send to display
    else:
        warnings.append(('WRN_WEBCOMMENT_ADD_UNKNOWN_ACTION',))
        if reviews and cfg_webcomment_allow_reviews:
            return (webcomment_templates.tmpl_add_comment_form_with_ranking(recID, uid, ln, msg, score, note, warnings), errors, warnings)
        else:
            return (webcomment_templates.tmpl_add_comment_form(recID, uid, ln, msg, warnings), errors, warnings)

def notify_admin_of_new_comment(comID):
    """
    Sends an email to the admin with details regarding comment with ID = comID
    """
    comment = query_get_comment(comID)
    if len(comment) > 0:
        (comID2, id_bibrec, id_user, body, date_creation, star_score, nb_votes_yes, nb_votes_total, title, nb_abuse_reports) = comment
    else:
        return
    user_info = query_get_user_contact_info(id_user) 
    if len(user_info) > 0:
        (nickname, email, last_login) = user_info
        if not len(nickname) > 0:
            nickname = email.split('@')[0]
    else:
        nickname = email = last_login = "ERROR: Could not retrieve"

    from search_engine import print_record    
    record = print_record(recID=id_bibrec, format='hs')
 
    review_stuff = ''' 
    Star score  = %s
    Title       = %s''' % (star_score, title)

    out = '''
The following %(comment_or_review)s has just been posted (%(date)s).

AUTHOR:     
    Nickname    = %(nickname)s
    Email       = %(email)s
    User ID     = %(uid)s

RECORD CONCERNED:
    Record ID   = %(recID)s
    Record      = 
<!-- start record details -->
%(record_details)s
<!-- end record details -->

%(comment_or_review_caps)s:
    %(comment_or_review)s ID    = %(comID)s %(review_stuff)s
    Body        = 
<!-- start body -->
%(body)s
<!-- end body -->

ADMIN OPTIONS:
To delete comment go to %(weburl)s/admin/webcomment/webcommentadmin.py/delete?comid=%(comID)s
    ''' % \
        {   'comment_or_review'     : star_score>0 and 'review' or 'comment',
            'comment_or_review_caps': star_score>0 and 'REVIEW' or 'COMMENT',
            'date'                  : date_creation,
            'nickname'              : nickname,
            'email'                 : email,
            'uid'                   : id_user,
            'recID'                 : id_bibrec,
            'record_details'        : record,
            'comID'                 : comID2,
            'review_stuff'          : star_score>0 and review_stuff or "",
            'body'                  : body.replace('<br>','\n'),
            'weburl'                : weburl
        }

    from_addr = 'CDS Alert Engine <%s>' % alertengineemail
    to_addr = adminemail
    subject = "A new comment/review has just been posted"
 
    from alert_engine import send_email, forge_email
    out = forge_email(from_addr, to_addr, subject, out)
    send_email(from_addr, to_addr, out)

def check_recID_is_in_range(recID, warnings=[], ln=cdslang):
    """
    Check that recID is >= 0 or <= -100
    Append error messages to errors listi
    @param recID: record id
    @param warnings: the warnings list of the calling function
    @return tuple (boolean, html) where boolean (1=true, 0=false) 
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
        if recID >= 1 or recID <= -100:
            from search_engine import record_exists
            success = record_exists(recID)
            if success == 1: 
                return (1,"")
            else:
                warnings.append(('ERR_WEBCOMMENT_RECID_INEXISTANT', recID))
                return (0, webcomment_templates.tmpl_record_not_found(status='inexistant', recID=recID, ln=ln))
        elif recID == -1:
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
    @return boolean (1=true, 0=false)
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

def wash_url_argument(var, new_type):
    """
    Wash argument into 'new_type', that can be 'list', 'str', or 'int'.
    If needed, the check 'type(var) is not None' should be done before calling this function
    @param var: variable value
    @param new_type: variable type, 'list', 'str' or 'int'
    @return as much as possible, value var as type new_type
            If var is a list, will change first element into new_type.
            If int check unsuccessful, returns 0
    """
    out = []
    if new_type == 'list':  # return lst
        if type(var) is list:
            out = var
        else:
            out = [var]
    elif new_type == 'str':  # return str
        if type(var) is list:
            try:
                out = "%s" % var[0]
            except:
                out = ""
        elif type(var) is str:
            out = var
        else:
            out = "%s" % var
    elif new_type == 'int': # return int
        if type(var) is list:
            try:
                out = int(var[0])
            except:
                out = 0
        elif type(var) is int:
            out = var
        elif type(var) is str:
            try:
                out = int(var)
            except:
                out = 0
        else:
            out = 0
    elif new_type == 'tuple': # return tuple
        if type(var) is tuple:
            out = var
        else:
            out = (var,)
    elif new_type == 'dict': # return dictionary
        if type(var) is dict:
            out = var
        else:
            out = {0:var}
    return out

