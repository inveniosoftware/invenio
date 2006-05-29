# -*- coding: utf-8 -*-
## $Id$
## Comments and reviews for records.

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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
""" Comments and reviews for records: web interface """

__lastupdated__ = """$Date$"""
__revision__ = """$Id$"""

from invenio.webcomment import check_recID_is_in_range, \
                               perform_request_display_comments_or_remarks,\
                               perform_request_add_comment_or_remark,\
                               perform_request_vote,\
                               perform_request_report
from invenio.config import cdslang, \
                           weburl,\
                           cfg_webcomment_allow_comments,\
                           cfg_webcomment_allow_reviews
from invenio.webuser import getUid, page_not_authorized, isGuestUser
from invenio.webaccount import create_login_page_box
from invenio.webpage import page
from invenio.search_engine import create_navtrail_links, guess_primary_collection_of_a_record
from invenio.urlutils import get_client_ip_address, \
                             redirect_to_url, \
                             wash_url_argument
from invenio.messages import wash_language, gettext_set_language

def index(req):
    """
    Redirects to display function
    """
    redirect_to_url(req,"%s/comments.py/display?%s" % (weburl, req.args))

def display(req, recid=-1, ln=cdslang, do='od', ds='all', nb=100, p=1, voted=-1, reported=-1, reviews=0):
    """
    Display comments (reviews if enabled) associated with record having id recid where recid>0.
    This function can also be used to display remarks associated with basket having id recid where recid<-99.
    @param ln: language
    @param recid: record id, integer
    @param do: display order    hh = highest helpful score, review only
                                lh = lowest helpful score, review only
                                hs = highest star score, review only
                                ls = lowest star score, review only 
                                od = oldest date 
                                nd = newest date 
    @param ds: display since    all= no filtering by date
                                nd = n days ago
                                nw = n weeks ago
                                nm = n months ago
                                ny = n years ago
                                where n is a single digit integer between 0 and 9
    @param nb: number of results per page
    @param p: results page
    @param voted: boolean, active if user voted for a review, see vote function
    @param reported: boolean, active if user reported a certain comment/review, see report function
    @param reviews: boolean, enabled for reviews, disabled for comments
    @return the full html page.
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)
    check_warnings = []
   
    (ok, problem) = check_recID_is_in_range(recid, check_warnings, ln) 
    if ok:
        (body, errors, warnings) = perform_request_display_comments_or_remarks(recID=recid, display_order=do, display_since=ds, nb_per_page=nb, page=p, ln=ln, voted=voted, reported=reported, reviews=reviews)

        navtrail = create_navtrail_links(cc=guess_primary_collection_of_a_record(recid))
        navtrail += '&gt; <a class="navtrail" href="%s/record/%s?ln=%s">'% (weburl, recid, ln)
        navtrail += _("Detailed record #%s") % recid
        navtrail += '</a>'
        navtrail += ' &gt; <a class="navtrail">%s</a>' % (reviews==1 and _("Reviews") or _("Comments"))

        return page(title="",
                    body=body,
                    navtrail=navtrail,
                    uid=uid,
                    verbose=1,
                    req=req,
                    language=ln,
                    errors=errors, warnings=warnings)
    else:
        return page(title=_("Record Not Found"),
                    body=problem,
                    uid=uid,
                    verbose=1,
                    req=req,
                    language=ln,
                    warnings=check_warnings, errors=[])

def add(req, ln=cdslang, recid=-1, action='DISPLAY', msg="", note="", score="", reviews=0, comid=-1):
    """
    Add a comment (review) to record with id recid where recid>0
    Also works for adding a remark to basket with id recid where recid<-99
    @param ln: languange
    @param recid: record id
    @param action:  'DISPLAY' to display add form 
                    'SUBMIT' to submit comment once form is filled
                    'REPLY' to reply to an already existing comment
    @param msg: the body of the comment/review or remark
    @param score: star score of the review
    @param note: title of the review
    @param comid: comment id, needed for replying
    @return the full html page.
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    reviews = wash_url_argument(reviews, 'int')
    action = wash_url_argument(action, 'str')
    comid = wash_url_argument(comid, 'int')
    
    actions = ['DISPLAY', 'REPLY', 'SUBMIT']
    uid = getUid(req)
    client_ip_address = get_client_ip_address(req)
    check_warnings = []

    (ok, problem) = check_recID_is_in_range(recid, check_warnings, ln) 
    if ok:
        navtrail = create_navtrail_links(cc=guess_primary_collection_of_a_record(recid))
        navtrail += ' &gt; <a class="navtrail" href="%s/record/%s?ln=%s">'% (weburl, recid, ln)
        navtrail += _("Detailed record #%s") % recid
        navtrail += '</a>'
        navtrail += '&gt; <a class="navtrail" href="%s/comments.py/display?recid=%s&ln=%s">%s</a>' % (weburl, recid, ln, reviews==1 and _('Reviews') or _('Comments')) 

        if action not in actions:
            action = 'DISPLAY'

        # is page allowed to be viewed
        if uid == -1 or (not cfg_webcomment_allow_comments and not cfg_webcomment_allow_reviews):
            return page_not_authorized(req, "../comments.py/add")

        # if guest, must log in first 
        if isGuestUser(uid):
            msg = _("Before you add your comment, you need to log in first")
            referer = "%s/comments.py/add?recid=%s&amp;ln=%s&amp;reviews=%s&amp;comid=%s&amp;action=%s" % (weburl, recid, ln, reviews, comid, action)
            login_box = create_login_page_box(referer=referer, ln=ln)
            return page(title=_("Login"),
                        body=msg+login_box,
                        navtrail=navtrail,
                        uid=uid,
                        language=cdslang,
                        verbose=1,
                        req=req)
        # user logged in
        else:
            (body, errors, warnings) = perform_request_add_comment_or_remark(recID=recid, uid=uid, action=action, msg=msg, note=note, score=score, reviews=reviews, comID=comid, client_ip_address=client_ip_address)
            if reviews:
                title = _("Add Review")
            else:
                title = _("Add Comment")
            return page(title=title,
                        body=body,
                        navtrail=navtrail,
                        uid=uid, 
                        language=cdslang,
                        verbose=1,
                        errors=errors,
                        warnings=warnings,
                        req=req)
    # id not in range
    else:
        return page(title=_("Record Not Found"),
                    body=problem,
                    uid=uid,
                    verbose=1,
                    req=req,
                    warnings=check_warnings, errors=[])

def vote(req, comid=-1, com_value=0, recid=-1, ln=cdslang, do='od', ds='all', nb=100, p=1, referer=None, reviews=0):
    """
    Vote positively or negatively for a comment/review.
    @param comid: comment/review id
    @param com_value:   +1 to vote positively
                        -1 to vote negatively
    @param recid: the id of the record the comment/review is associated with
    @param ln: language
    @param do: display order    hh = highest helpful score, review only
                                lh = lowest helpful score, review only
                                hs = highest star score, review only
                                ls = lowest star score, review only 
                                od = oldest date 
                                nd = newest date 
    @param ds: display since    all= no filtering by date
                                nd = n days ago
                                nw = n weeks ago
                                nm = n months ago
                                ny = n years ago
                                where n is a single digit integer between 0 and 9
    @param nb: number of results per page
    @param p: results page
    @param referer: http address of the calling function to redirect to (refresh)
    @param reviews: boolean, enabled for reviews, disabled for comments
    """
    client_ip_address = get_client_ip_address(req)
    uid = getUid(req)
    success = perform_request_vote(comid, client_ip_address, com_value, uid)
    if referer:
        referer += "?recid=%s&amp;ln=%s&amp;do=%s&amp;ds=%s&amp;nb=%s&amp;p=%s&amp;voted=%s&amp;reviews=%s" % (recid, ln, do, ds, nb, p, success, reviews)
        redirect_to_url(req, referer)
    else:
        #Note: sent to commetns display
        referer = "%s/comments.py/display?recid=%s&amp;ln=%s&amp;reviews=1&amp;voted=1"
        referer %= (weburl, recid, ln)
        redirect_to_url(req, referer)

def report(req, comid=-1, recid=-1, ln=cdslang, do='od', ds='all', nb=100, p=1, referer=None, reviews=0):
    """
    Report a comment/review for inappropriate content
    @param comid: comment/review id
    @param recid: the id of the record the comment/review is associated with
    @param ln: language
    @param do: display order    hh = highest helpful score, review only
                                lh = lowest helpful score, review only
                                hs = highest star score, review only
                                ls = lowest star score, review only 
                                od = oldest date 
                                nd = newest date 
    @param ds: display since    all= no filtering by date
                                nd = n days ago
                                nw = n weeks ago
                                nm = n months ago
                                ny = n years ago
                                where n is a single digit integer between 0 and 9
    @param nb: number of results per page
    @param p: results page
    @param referer: http address of the calling function to redirect to (refresh)
    @param reviews: boolean, enabled for reviews, disabled for comments
    """
    client_ip_address = get_client_ip_address(req)
    uid = getUid(req)
    success = perform_request_report(comid, client_ip_address, uid)
    if referer:
        referer += "?recid=%s&amp;ln=%s&amp;do=%s&amp;ds=%s&amp;nb=%s&amp;p=%s&amp;reported=%s&amp;reviews=%s" % (recid, ln, do, ds, nb, p, success, reviews)
        redirect_to_url(req, referer)
    else:
        #Note: sent to comments display 
        referer = "%s/comments.py/display?recid=%s&amp;ln=%s&amp;reviews=1&amp;voted=1"
        referer %= (weburl, recid, ln)
        redirect_to_url(referer)
