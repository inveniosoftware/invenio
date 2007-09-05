# -*- coding: utf-8 -*-
## $Id$
## Comments and reviews for records.

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

import urllib
from invenio.webcomment import check_recID_is_in_range, \
                               perform_request_display_comments_or_remarks,\
                               perform_request_add_comment_or_remark,\
                               perform_request_vote,\
                               perform_request_report
from invenio.config import cdslang, \
                           weburl, \
                           sweburl, \
                           CFG_WEBCOMMENT_ALLOW_COMMENTS,\
                           CFG_WEBCOMMENT_ALLOW_REVIEWS
from invenio.webuser import getUid, page_not_authorized, isGuestUser
from invenio.webpage import page, pageheaderonly, pagefooteronly
from invenio.search_engine import create_navtrail_links, \
     guess_primary_collection_of_a_record, \
     get_colID
from invenio.urlutils import get_client_ip_address, \
                             redirect_to_url, \
                             wash_url_argument
from invenio.messages import wash_language, gettext_set_language
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory
from invenio.websearchadminlib import get_detailed_page_tabs
import invenio.template
webstyle_templates = invenio.template.load('webstyle')
websearch_templates = invenio.template.load('websearch')

class WebInterfaceCommentsPages(WebInterfaceDirectory):
    """Defines the set of /comments pages."""

    _exports = ['', 'display', 'add', 'vote', 'report', 'index']

    def __init__(self, recid=-1, reviews=0):
        self.recid = recid
        self.discussion = reviews # 0:comments, 1:reviews

    def index(self, req, form):
        """
        Redirects to display function
        """
        return self.display(req, form)

    def display(self, req, form):
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

        argd = wash_urlargd(form, {'do': (str, "od"),
                                   'ds': (str, "all"),
                                   'nb': (int, 100),
                                   'p': (int, 1),
                                   'voted': (int, -1),
                                   'reported': (int, -1),
                                   })

        _ = gettext_set_language(argd['ln'])
        uid = getUid(req)
        check_warnings = []

        (ok, problem) = check_recID_is_in_range(self.recid, check_warnings, argd['ln'])
        if ok:
            (body, errors, warnings) = perform_request_display_comments_or_remarks(recID=self.recid,
                                                                                   display_order=argd['do'],
                                                                                   display_since=argd['ds'],
                                                                                   nb_per_page=argd['nb'],
                                                                                   page=argd['p'],
                                                                                   ln=argd['ln'],
                                                                                   voted=argd['voted'],
                                                                                   reported=argd['reported'],
                                                                                   reviews=self.discussion,
                                                                                   uid=uid)

            unordered_tabs = get_detailed_page_tabs(get_colID(guess_primary_collection_of_a_record(self.recid)),
                                                    self.recid)
            ordered_tabs_id = [(tab_id, values['order']) for (tab_id, values) in unordered_tabs.iteritems()]
            ordered_tabs_id.sort(lambda x,y: cmp(x[1],y[1]))
            tabs = [(unordered_tabs[tab_id]['label'], \
                     '%s/record/%s/%s' % (weburl, self.recid, tab_id), \
                     tab_id in ['comments', 'reviews'],
                     unordered_tabs[tab_id]['enabled']) \
                    for (tab_id, order) in ordered_tabs_id
                    if unordered_tabs[tab_id]['visible'] == True]
            body = webstyle_templates.detailed_record_container(body,
                                                                self.recid,
                                                                tabs,
                                                                argd['ln'])

            title, description, keywords = websearch_templates.tmpl_record_page_header_content(req, self.recid, argd['ln'])
            navtrail = create_navtrail_links(cc=guess_primary_collection_of_a_record(self.recid), ln=argd['ln'])
            navtrail += ' &gt; <a class="navtrail" href="%s/record/%s?ln=%s">'% (weburl, self.recid, argd['ln'])
            navtrail += title
            navtrail += '</a>'
            navtrail += ' &gt; <a class="navtrail">%s</a>' % (self.discussion==1 and _("Reviews") or _("Comments"))

            return pageheaderonly(title=title,
                        navtrail=navtrail,
                        uid=uid,
                        verbose=1,
                        req=req,
                        language=argd['ln'],
                        navmenuid='search',
                        navtrail_append_title_p=0) + \
                    websearch_templates.tmpl_search_pagestart(argd['ln']) + \
                    body + \
                    websearch_templates.tmpl_search_pageend(argd['ln']) + \
                    pagefooteronly(lastupdated=__lastupdated__, language=argd['ln'], req=req)
        else:
            return page(title=_("Record Not Found"),
                        body=problem,
                        uid=uid,
                        verbose=1,
                        req=req,
                        language=argd['ln'],
                        warnings=check_warnings, errors=[],
                        navmenuid='search')

    # Return the same page wether we ask for /record/123 or /record/123/
    __call__ = index

    def add(self, req, form):
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

        argd = wash_urlargd(form, {'action': (str, "DISPLAY"),
                                   'msg': (str, ""),
                                   'note': (str, ''),
                                   'score': (int, 0),
                                   'comid': (int, -1),
                                   })

        _ = gettext_set_language(argd['ln'])

        actions = ['DISPLAY', 'REPLY', 'SUBMIT']
        uid = getUid(req)
        client_ip_address = get_client_ip_address(req)
        check_warnings = []
        (ok, problem) = check_recID_is_in_range(self.recid, check_warnings, argd['ln'])
        if ok:
            title, description, keywords = websearch_templates.tmpl_record_page_header_content(req,
                                                                                               self.recid,
                                                                                               argd['ln'])
            navtrail = create_navtrail_links(cc=guess_primary_collection_of_a_record(self.recid))
            navtrail += ' &gt; <a class="navtrail" href="%s/record/%s?ln=%s">'% (weburl, self.recid, argd['ln'])
            navtrail += title
            navtrail += '</a>'
            navtrail += '&gt; <a class="navtrail" href="%s/record/%s/%s/?ln=%s">%s</a>' % (weburl,
                                                                                           self.recid,
                                                                                           self.discussion==1 and 'reviews' or 'comments',
                                                                                           argd['ln'],
                                                                                           self.discussion==1 and _('Reviews') or _('Comments'))

            if argd['action'] not in actions:
                argd['action'] = 'DISPLAY'

            # is page allowed to be viewed
            if uid == -1 or (not CFG_WEBCOMMENT_ALLOW_COMMENTS and not CFG_WEBCOMMENT_ALLOW_REVIEWS):
                return page_not_authorized(req, "../comments/add",
                                           navmenuid='search')

            # if guest, must log in first
            if isGuestUser(uid):
                referer = "%s/record/%s/%s/add?ln=%s&amp;comid=%s&amp;action=%s&amp;score=%s" % (weburl,
                                                                                    self.recid,
                                                                                    self.discussion == 1 and 'reviews' or 'comments',
                                                                                    argd['ln'],
                                                                                    argd['comid'],
                                                                                    argd['action'],
                                                                                    argd['score'])
                msg = _("Before you add your comment, you need to %(x_url_open)slogin%(x_url_close)s first.") % {
                          'x_url_open': '<a href="%s/youraccount/login?referer=%s">' % \
                                        (sweburl, urllib.quote(referer)),
                          'x_url_close': '</a>'}
                return page(title=_("Login"),
                            body=msg,
                            navtrail=navtrail,
                            uid=uid,
                            language=cdslang,
                            verbose=1,
                            req=req,
                            navmenuid='search')
            # user logged in
            else:
                (body, errors, warnings) = perform_request_add_comment_or_remark(recID=self.recid,
                                                                                 ln=argd['ln'],
                                                                                 uid=uid,
                                                                                 action=argd['action'],
                                                                                 msg=argd['msg'],
                                                                                 note=argd['note'],
                                                                                 score=argd['score'],
                                                                                 reviews=self.discussion,
                                                                                 comID=argd['comid'],
                                                                                 client_ip_address=client_ip_address)
                if self.discussion:
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
                            req=req,
                            navmenuid='search')
        # id not in range
        else:
            return page(title=_("Record Not Found"),
                        body=problem,
                        uid=uid,
                        verbose=1,
                        req=req,
                        warnings=check_warnings, errors=[],
                        navmenuid='search')

    def vote(self, req, form):
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

        argd = wash_urlargd(form, {'comid': (int, -1),
                                   'com_value': (int, 0),
                                   'recid': (int, -1),
                                   'do': (str, "od"),
                                   'ds': (str, "all"),
                                   'nb': (int, 100),
                                   'p': (int, 1),
                                   'referer': (str, None)
                                   })

        client_ip_address = get_client_ip_address(req)
        uid = getUid(req)
        success = perform_request_vote(argd['comid'], client_ip_address, argd['com_value'], uid)
        if argd['referer']:
            argd['referer'] += "?ln=%s&amp;do=%s&amp;ds=%s&amp;nb=%s&amp;p=%s&amp;voted=%s&amp;" % (argd['ln'],
                                                                                                    argd['do'],
                                                                                                    argd['ds'],
                                                                                                    argd['nb'],
                                                                                                    argd['p'],
                                                                                                    success)
            redirect_to_url(req, argd['referer'])
        else:
            #Note: sent to comments display
            referer = "%s/record/%s/%s?&amp;ln=%s&amp;voted=1"
            referer %= (weburl, self.recid, self.discussion == 1 and 'reviews' or 'comments', argd['ln'])
            redirect_to_url(req, referer)

    def report(self, req, form):
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

        argd = wash_urlargd(form, {'comid': (int, -1),
                                   'recid': (int, -1),
                                   'do': (str, "od"),
                                   'ds': (str, "all"),
                                   'nb': (int, 100),
                                   'p': (int, 1),
                                   'referer': (str, None)
                                   })

        client_ip_address = get_client_ip_address(req)
        uid = getUid(req)
        success = perform_request_report(argd['comid'], client_ip_address, uid)
        if argd['referer']:
            argd['referer'] += "?ln=%s&amp;do=%s&amp;ds=%s&amp;nb=%s&amp;p=%s&amp;reported=%s&amp;" % (argd['ln'],
                                                                                                       argd['do'],
                                                                                                       argd['ds'],
                                                                                                       argd['nb'],
                                                                                                       argd['p'],
                                                                                                       str(success))

            redirect_to_url(req, argd['referer'])
        else:
            #Note: sent to comments display
            referer = "%s/record/%s/%s/display?ln=%s&amp;voted=1"
            referer %= (weburl, self.recid, self.discussion==1 and 'reviews' or 'comments', argd['ln'])
            redirect_to_url(req, referer)
