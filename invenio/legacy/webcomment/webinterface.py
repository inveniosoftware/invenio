# -*- coding: utf-8 -*-
# Comments and reviews for records.

# This file is part of Invenio.
# Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2012, 2013, 2015 CERN.
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

""" Comments and reviews for records: web interface """

__lastupdated__ = """$Date$"""

__revision__ = """$Id$"""

import cgi

from six import iteritems

from invenio.modules.comments.api import check_recID_is_in_range, \
    perform_request_display_comments_or_remarks, \
    perform_request_add_comment_or_remark, \
    perform_request_vote, \
    perform_request_report, \
    subscribe_user_to_discussion, \
    unsubscribe_user_from_discussion, \
    get_user_subscription_to_discussion, \
    check_user_can_attach_file_to_comments, \
    check_user_can_view_comments, \
    check_user_can_send_comments, \
    check_user_can_view_comment, \
    query_get_comment, \
    toggle_comment_visibility, \
    check_comment_belongs_to_record, \
    is_comment_deleted, \
    perform_display_your_comments

from invenio.config import \
     CFG_TMPSHAREDDIR, \
     CFG_SITE_LANG, \
     CFG_SITE_URL, \
     CFG_SITE_SECURE_URL, \
     CFG_SITE_NAME, \
     CFG_SITE_NAME_INTL, \
     CFG_WEBCOMMENT_ALLOW_COMMENTS,\
     CFG_WEBCOMMENT_ALLOW_REVIEWS, \
     CFG_WEBCOMMENT_USE_MATHJAX_IN_COMMENTS, \
     CFG_SITE_RECORD, \
     CFG_WEBCOMMENT_MAX_ATTACHMENT_SIZE, \
     CFG_WEBCOMMENT_MAX_ATTACHED_FILES, \
     CFG_ACCESS_CONTROL_LEVEL_SITE, \
     CFG_COMMENTSDIR
from invenio.legacy.webuser import getUid, page_not_authorized, isGuestUser, collect_user_info
from invenio.legacy.webpage import page, pageheaderonly, pagefooteronly
from invenio.legacy.search_engine import create_navtrail_links, \
    guess_primary_collection_of_a_record
from invenio.utils.url import redirect_to_url, \
    make_canonical_urlargd
from invenio.utils.html import get_mathjax_header
from invenio.ext.logging import register_exception
from invenio.base.i18n import gettext_set_language
from invenio.ext.legacy.handler import wash_urlargd, WebInterfaceDirectory
from invenio.legacy.websearch.adminlib import get_detailed_page_tabs, \
    get_detailed_page_tabs_counts
from invenio.modules.access.local_config import VIEWRESTRCOLL
from invenio.modules.access.mailcookie import \
    mail_cookie_create_authorize_action, \
    mail_cookie_create_common, \
    mail_cookie_check_common
from invenio.modules.access.errors import \
    InvenioWebAccessMailCookieDeletedError, \
    InvenioWebAccessMailCookieError
from invenio.modules.comments.config import \
    InvenioWebCommentWarning
import invenio.legacy.template
webstyle_templates = invenio.legacy.template.load('webstyle')
websearch_templates = invenio.legacy.template.load('websearch')
import os
from invenio.utils import apache
from invenio.legacy.bibdocfile.api import \
    stream_file, \
    decompose_file, \
    propose_next_docname
from invenio.modules.collections.models import Collection


class WebInterfaceCommentsPages(WebInterfaceDirectory):

    """Defines the set of /comments pages."""

    _exports = ['', 'display', 'add', 'vote', 'report', 'index', 'attachments',
                'subscribe', 'unsubscribe', 'toggle']

    def __init__(self, recid=-1, reviews=0):
        self.recid = recid
        self.discussion = reviews # 0:comments, 1:reviews
        self.attachments = WebInterfaceCommentsFiles(recid, reviews)

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
        @param reported: int, active if user reported a certain comment/review, see report function
        @param reviews: boolean, enabled for reviews, disabled for comments
        @param subscribed: int, 1 if user just subscribed to discussion, -1 if unsubscribed
        @return the full html page.
        """
        argd = wash_urlargd(form, {'do': (str, "od"),
                                   'ds': (str, "all"),
                                   'nb': (int, 100),
                                   'p': (int, 1),
                                   'voted': (int, -1),
                                   'reported': (int, -1),
                                   'subscribed': (int, 0),
                                   'cmtgrp': (list, ["latest"]) # 'latest' is now a reserved group/round name
                                   })

        _ = gettext_set_language(argd['ln'])
        uid = getUid(req)

        user_info = collect_user_info(req)
        (auth_code, auth_msg) = check_user_can_view_comments(user_info, self.recid)
        if auth_code and user_info['email'] == 'guest':
            cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : guess_primary_collection_of_a_record(self.recid)})
            target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : \
                CFG_SITE_SECURE_URL + user_info['uri']}, {})
            return redirect_to_url(req, target, norobot=True)
        elif auth_code:
            return page_not_authorized(req, "../", \
                text = auth_msg)

        can_send_comments = False
        (auth_code, auth_msg) = check_user_can_send_comments(user_info, self.recid)
        if not auth_code:
            can_send_comments = True

        can_attach_files = False
        (auth_code, auth_msg) = check_user_can_attach_file_to_comments(user_info, self.recid)
        if not auth_code and (user_info['email'] != 'guest'):
            can_attach_files = True

        subscription = get_user_subscription_to_discussion(self.recid, uid)
        if subscription == 1:
            user_is_subscribed_to_discussion = True
            user_can_unsubscribe_from_discussion = True
        elif subscription == 2:
            user_is_subscribed_to_discussion = True
            user_can_unsubscribe_from_discussion = False
        else:
            user_is_subscribed_to_discussion = False
            user_can_unsubscribe_from_discussion = False

        col_id = Collection.query.filter_by(
            name=guess_primary_collection_of_a_record(self.recid)).value('id')
        unordered_tabs = get_detailed_page_tabs(col_id, self.recid,
                                                ln=argd['ln'])
        ordered_tabs_id = [(tab_id, values['order']) for (tab_id, values) in iteritems(unordered_tabs)]
        ordered_tabs_id.sort(lambda x, y: cmp(x[1], y[1]))
        link_ln = ''
        if argd['ln'] != CFG_SITE_LANG:
            link_ln = '?ln=%s' % argd['ln']

        tabs = [(unordered_tabs[tab_id]['label'], \
                 '%s/record/%s/%s%s' % (CFG_SITE_URL, self.recid, tab_id, link_ln), \
                 tab_id in ['comments', 'reviews'],
                 unordered_tabs[tab_id]['enabled']) \
                for (tab_id, order) in ordered_tabs_id
                if unordered_tabs[tab_id]['visible'] == True]

        tabs_counts = get_detailed_page_tabs_counts(self.recid)
        citedbynum = tabs_counts['Citations']
        references = tabs_counts['References']
        discussions = tabs_counts['Discussions']

        top = webstyle_templates.detailed_record_container_top(self.recid,
                                                               tabs,
                                                               argd['ln'],
                                                               citationnum=citedbynum,
                                                               referencenum=references,
                                                               discussionnum=discussions)
        bottom = webstyle_templates.detailed_record_container_bottom(self.recid,
                                                                     tabs,
                                                                     argd['ln'])

        #display_comment_rounds = [cmtgrp for cmtgrp in argd['cmtgrp'] if cmtgrp.isdigit() or cmtgrp == "all" or cmtgrp == "-1"]
        display_comment_rounds = argd['cmtgrp']

        check_warnings = []

        (ok, problem) = check_recID_is_in_range(self.recid, check_warnings, argd['ln'])
        if ok:
            body = perform_request_display_comments_or_remarks(req=req, recID=self.recid,
                display_order=argd['do'],
                display_since=argd['ds'],
                nb_per_page=argd['nb'],
                page=argd['p'],
                ln=argd['ln'],
                voted=argd['voted'],
                reported=argd['reported'],
                subscribed=argd['subscribed'],
                reviews=self.discussion,
                uid=uid,
                can_send_comments=can_send_comments,
                can_attach_files=can_attach_files,
                user_is_subscribed_to_discussion=user_is_subscribed_to_discussion,
                user_can_unsubscribe_from_discussion=user_can_unsubscribe_from_discussion,
                display_comment_rounds=display_comment_rounds
                )

            title, description, keywords = websearch_templates.tmpl_record_page_header_content(req, self.recid, argd['ln'])
            navtrail = create_navtrail_links(cc=guess_primary_collection_of_a_record(self.recid), ln=argd['ln'])
            if navtrail:
                navtrail += ' &gt; '
            navtrail += '<a class="navtrail" href="%s/%s/%s?ln=%s">'% (CFG_SITE_URL, CFG_SITE_RECORD, self.recid, argd['ln'])
            navtrail += cgi.escape(title)
            navtrail += '</a>'
            navtrail += ' &gt; <a class="navtrail">%s</a>' % (self.discussion==1 and _("Reviews") or _("Comments"))

            mathjaxheader = ''
            if CFG_WEBCOMMENT_USE_MATHJAX_IN_COMMENTS:
                mathjaxheader = get_mathjax_header(req.is_https())
            jqueryheader = '''
            <script src="%(CFG_SITE_URL)s/vendors/jquery-multifile/jquery.MultiFile.pack.js" type="text/javascript"></script>
            ''' % {'CFG_SITE_URL': CFG_SITE_URL}


            return pageheaderonly(title=title,
                        navtrail=navtrail,
                        uid=uid,
                        verbose=1,
                        metaheaderadd = mathjaxheader + jqueryheader,
                        req=req,
                        language=argd['ln'],
                        navmenuid='search',
                        navtrail_append_title_p=0) + \
                    websearch_templates.tmpl_search_pagestart(argd['ln']) + \
                    top + body + bottom + \
                    websearch_templates.tmpl_search_pageend(argd['ln']) + \
                    pagefooteronly(lastupdated=__lastupdated__, language=argd['ln'], req=req)
        else:
            return page(title=_("Record Not Found"),
                        body=problem,
                        uid=uid,
                        verbose=1,
                        req=req,
                        language=argd['ln'],
                        navmenuid='search')

    # Return the same page wether we ask for /CFG_SITE_RECORD/123 or /CFG_SITE_RECORD/123/
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
        @param editor_type: the type of editor used for submitting the
                            comment: 'textarea', 'ckeditor'.
        @param subscribe: if set, subscribe user to receive email
                          notifications when new comment are added to
                          this discussion
        @return the full html page.
        """
        argd = wash_urlargd(form, {'action': (str, "DISPLAY"),
                                   'msg': (str, ""),
                                   'note': (str, ''),
                                   'score': (int, 0),
                                   'comid': (int, 0),
                                   'editor_type': (str, ""),
                                   'subscribe': (str, ""),
                                   'cookie': (str, "")
                                   })
        _ = gettext_set_language(argd['ln'])

        actions = ['DISPLAY', 'REPLY', 'SUBMIT']
        uid = getUid(req)

        # Is site ready to accept comments?
        if uid == -1 or (not CFG_WEBCOMMENT_ALLOW_COMMENTS and not CFG_WEBCOMMENT_ALLOW_REVIEWS):
            return page_not_authorized(req, "../comments/add",
                                       navmenuid='search')

        # Is user allowed to post comment?
        user_info = collect_user_info(req)
        (auth_code_1, auth_msg_1) = check_user_can_view_comments(user_info, self.recid)
        (auth_code_2, auth_msg_2) = check_user_can_send_comments(user_info, self.recid)
        if isGuestUser(uid):
            cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : guess_primary_collection_of_a_record(self.recid)})
            # Save user's value in cookie, so that these "POST"
            # parameters are not lost during login process
            msg_cookie = mail_cookie_create_common('comment_msg',
                                                    {'msg': argd['msg'],
                                                     'note': argd['note'],
                                                     'score': argd['score'],
                                                     'editor_type': argd['editor_type'],
                                                     'subscribe': argd['subscribe']},
                                                    onetime=True)
            target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : \
                CFG_SITE_SECURE_URL + user_info['uri'] + '&cookie=' + msg_cookie}, {})
            return redirect_to_url(req, target, norobot=True)
        elif (auth_code_1 or auth_code_2):
            return page_not_authorized(req, "../", \
                text = auth_msg_1 + auth_msg_2)

        if argd['comid']:
            # If replying to a comment, are we on a record that
            # matches the original comment user is replying to?
            if not check_comment_belongs_to_record(argd['comid'], self.recid):
                return page_not_authorized(req, "../", \
                                           text = _("Specified comment does not belong to this record"))


            # Is user trying to reply to a restricted comment? Make
            # sure user has access to it.  We will then inherit its
            # restriction for the new comment
            (auth_code, auth_msg) = check_user_can_view_comment(user_info, argd['comid'])
            if auth_code:
                return page_not_authorized(req, "../", \
                                           text = _("You do not have access to the specified comment"))

            # Is user trying to reply to a deleted comment? If so, we
            # let submitted comment go (to not lose possibly submitted
            # content, if comment is submitted while original is
            # deleted), but we "reset" comid to make sure that for
            # action 'REPLY' the original comment is not included in
            # the reply
            if is_comment_deleted(argd['comid']):
                argd['comid'] = 0

        user_info = collect_user_info(req)
        can_attach_files = False
        (auth_code, auth_msg) = check_user_can_attach_file_to_comments(user_info, self.recid)
        if not auth_code and (user_info['email'] != 'guest'):
            can_attach_files = True

        warning_msgs = [] # list of warning tuples (warning_text, warning_color)
        added_files = {}
        if can_attach_files:
            # User is allowed to attach files. Process the files
            file_too_big = False
            formfields = form.get('commentattachment[]', [])
            if not hasattr(formfields, "__getitem__"): # A single file was uploaded
                formfields = [formfields]
            for formfield in formfields[:CFG_WEBCOMMENT_MAX_ATTACHED_FILES]:
                if hasattr(formfield, "filename") and formfield.filename:
                    filename = formfield.filename
                    dir_to_open = os.path.join(CFG_TMPSHAREDDIR, 'webcomment', str(uid))
                    try:
                        assert(dir_to_open.startswith(CFG_TMPSHAREDDIR))
                    except AssertionError:
                        register_exception(req=req,
                                           prefix='User #%s tried to upload file to forbidden location: %s' \
                                           % (uid, dir_to_open))

                    if not os.path.exists(dir_to_open):
                        try:
                            os.makedirs(dir_to_open)
                        except:
                            register_exception(req=req, alert_admin=True)

                    ## Before saving the file to disc, wash the filename
                    ## (in particular washing away UNIX and Windows
                    ## (e.g. DFS) paths):
                    filename = os.path.basename(filename.split('\\')[-1])
                    filename = filename.strip()
                    if filename != "":
                        # Check that file does not already exist
                        while os.path.exists(os.path.join(dir_to_open,
                                                          filename)):
                            basedir, name, extension = decompose_file(filename)
                            new_name = propose_next_docname(name)
                            filename = new_name + extension

                        fp = open(os.path.join(dir_to_open, filename), "w")
                        # FIXME: temporary, waiting for wsgi handler to be
                        # fixed. Once done, read chunk by chunk
#                         while formfield.file:
#                             fp.write(formfield.file.read(10240))
                        fp.write(formfield.file.read())
                        fp.close()
                        # Isn't this file too big?
                        file_size = os.path.getsize(os.path.join(dir_to_open,
                                                                 filename))
                        if CFG_WEBCOMMENT_MAX_ATTACHMENT_SIZE > 0 and \
                               file_size > CFG_WEBCOMMENT_MAX_ATTACHMENT_SIZE:
                            os.remove(os.path.join(dir_to_open, filename))
                            # One file is too big: record that,
                            # dismiss all uploaded files and re-ask to
                            # upload again
                            file_too_big = True
                            try:
                                raise InvenioWebCommentWarning(_('The size of file \\"%(x_file)s\\" (%(x_size)s) is larger than maximum allowed file size (%(x_max)s). Select files again.',
                                        x_file=cgi.escape(filename), x_size=str(file_size/1024) + 'KB', x_max=str(CFG_WEBCOMMENT_MAX_ATTACHMENT_SIZE/1024) + 'KB'))
                            except InvenioWebCommentWarning as exc:
                                register_exception(stream='warning')
                                warning_msgs.append((exc.message, ''))
                            #warning_msgs.append(('WRN_WEBCOMMENT_MAX_FILE_SIZE_REACHED', cgi.escape(filename), str(file_size/1024) + 'KB', str(CFG_WEBCOMMENT_MAX_ATTACHMENT_SIZE/1024) + 'KB'))
                        else:
                            added_files[filename] = os.path.join(dir_to_open, filename)

            if file_too_big:
                # One file was too big. Removed all uploaded filed
                for filepath in added_files.items():
                    try:
                        os.remove(filepath)
                    except:
                        # File was already removed or does not exist?
                        pass

        client_ip_address = req.remote_ip
        check_warnings = []
        (ok, problem) = check_recID_is_in_range(self.recid, check_warnings, argd['ln'])
        if ok:
            title, description, keywords = websearch_templates.tmpl_record_page_header_content(req,
                                                                                               self.recid,
                                                                                               argd['ln'])
            navtrail = create_navtrail_links(cc=guess_primary_collection_of_a_record(self.recid))
            if navtrail:
                navtrail += ' &gt; '
            navtrail += '<a class="navtrail" href="%s/%s/%s?ln=%s">'% (CFG_SITE_URL, CFG_SITE_RECORD, self.recid, argd['ln'])
            navtrail += cgi.escape(title)
            navtrail += '</a>'
            navtrail += '&gt; <a class="navtrail" href="%s/%s/%s/%s/?ln=%s">%s</a>' % (CFG_SITE_URL,
                                                                                           CFG_SITE_RECORD,
                                                                                           self.recid,
                                                                                           self.discussion==1 and 'reviews' or 'comments',
                                                                                           argd['ln'],
                                                                                           self.discussion==1 and _('Reviews') or _('Comments'))

            if argd['action'] not in actions:
                argd['action'] = 'DISPLAY'

            if not argd['msg']:
                # User had to login in-between, so retrieve msg
                # from cookie
                try:
                    (kind, cookie_argd) = mail_cookie_check_common(argd['cookie'],
                                                                    delete=True)

                    argd.update(cookie_argd)
                except InvenioWebAccessMailCookieDeletedError:
                    return redirect_to_url(req, CFG_SITE_SECURE_URL + '/'+ CFG_SITE_RECORD +'/' + \
                                           str(self.recid) + (self.discussion==1 and \
                                                              '/reviews' or '/comments'))
                except InvenioWebAccessMailCookieError:
                    # Invalid or empty cookie: continue
                    pass

            subscribe = False
            if argd['subscribe'] and \
               get_user_subscription_to_discussion(self.recid, uid) == 0:
                # User is not already subscribed, and asked to subscribe
                subscribe = True

            body = perform_request_add_comment_or_remark(recID=self.recid,
                                                         ln=argd['ln'],
                                                         uid=uid,
                                                         action=argd['action'],
                                                         msg=argd['msg'],
                                                         note=argd['note'],
                                                         score=argd['score'],
                                                         reviews=self.discussion,
                                                         comID=argd['comid'],
                                                         client_ip_address=client_ip_address,
                                                         editor_type=argd['editor_type'],
                                                         can_attach_files=can_attach_files,
                                                         subscribe=subscribe,
                                                         req=req,
                                                         attached_files=added_files,
                                                         warnings=warning_msgs)

            if self.discussion:
                title = _("Add Review")
            else:
                title = _("Add Comment")

            jqueryheader = '''
            <script src="%(CFG_SITE_URL)s/vendors/jquery-multifile/jquery.MultiFile.pack.js" type="text/javascript"></script>
            ''' % {'CFG_SITE_URL': CFG_SITE_URL}

            return page(title=title,
                        body=body,
                        navtrail=navtrail,
                        uid=uid,
                        language=CFG_SITE_LANG,
                        verbose=1,
                        req=req,
                        navmenuid='search',
                        metaheaderadd=jqueryheader)
        # id not in range
        else:
            return page(title=_("Record Not Found"),
                        body=problem,
                        uid=uid,
                        verbose=1,
                        req=req,
                        navmenuid='search')

    def vote(self, req, form):
        """Vote positively or negatively for a comment/review.

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
        _ = gettext_set_language(argd['ln'])
        client_ip_address = req.remote_ip
        uid = getUid(req)

        user_info = collect_user_info(req)
        (auth_code, auth_msg) = check_user_can_view_comments(user_info, self.recid)
        if auth_code and user_info['email'] == 'guest':
            cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : guess_primary_collection_of_a_record(self.recid)})
            target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : \
                CFG_SITE_SECURE_URL + user_info['uri']}, {})
            return redirect_to_url(req, target, norobot=True)
        elif auth_code:
            return page_not_authorized(req, "../", \
                text = auth_msg)

        # Check that comment belongs to this recid
        if not check_comment_belongs_to_record(argd['comid'], self.recid):
            return page_not_authorized(req, "../", \
                                       text = _("Specified comment does not belong to this record"))

        # Check that user can access the record
        (auth_code, auth_msg) = check_user_can_view_comment(user_info, argd['comid'])
        if auth_code:
            return page_not_authorized(req, "../", \
                                       text = _("You do not have access to the specified comment"))

        # Check that comment is not currently deleted
        if is_comment_deleted(argd['comid']):
            return page_not_authorized(req, "../", \
                                       text = _("You cannot vote for a deleted comment"),
                                       ln=argd['ln'])

        success = perform_request_vote(argd['comid'], client_ip_address, argd['com_value'], uid)
        if argd['referer']:
            argd['referer'] += "?ln=%s&do=%s&ds=%s&nb=%s&p=%s&voted=%s&" % (
                argd['ln'], argd['do'], argd['ds'], argd['nb'], argd['p'], success)
            redirect_to_url(req, argd['referer'])
        else:
            #Note: sent to comments display
            referer = "%s/%s/%s/%s?&ln=%s&voted=1"
            referer %= (CFG_SITE_SECURE_URL, CFG_SITE_RECORD, self.recid, self.discussion == 1 and 'reviews' or 'comments', argd['ln'])
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
        _ = gettext_set_language(argd['ln'])

        client_ip_address = req.remote_ip
        uid = getUid(req)

        user_info = collect_user_info(req)
        (auth_code, auth_msg) = check_user_can_view_comments(user_info, self.recid)
        if isGuestUser(uid):
            cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : guess_primary_collection_of_a_record(self.recid)})
            target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : \
                CFG_SITE_SECURE_URL + user_info['uri']}, {})
            return redirect_to_url(req, target, norobot=True)
        elif auth_code:
            return page_not_authorized(req, "../", \
                text = auth_msg)

        # Check that comment belongs to this recid
        if not check_comment_belongs_to_record(argd['comid'], self.recid):
            return page_not_authorized(req, "../", \
                                       text = _("Specified comment does not belong to this record"))

        # Check that user can access the record
        (auth_code, auth_msg) = check_user_can_view_comment(user_info, argd['comid'])
        if auth_code:
            return page_not_authorized(req, "../", \
                                       text = _("You do not have access to the specified comment"))

        # Check that comment is not currently deleted
        if is_comment_deleted(argd['comid']):
            return page_not_authorized(req, "../", \
                                       text = _("You cannot report a deleted comment"),
                                       ln=argd['ln'])

        success = perform_request_report(argd['comid'], client_ip_address, uid)
        if argd['referer']:
            argd['referer'] += "?ln=%s&do=%s&ds=%s&nb=%s&p=%s&reported=%s&" % (argd['ln'], argd['do'], argd['ds'], argd['nb'], argd['p'], str(success))

            redirect_to_url(req, argd['referer'])
        else:
            #Note: sent to comments display
            referer = "%s/%s/%s/%s/display?ln=%s&voted=1"
            referer %= (CFG_SITE_SECURE_URL, CFG_SITE_RECORD, self.recid, self.discussion==1 and 'reviews' or 'comments', argd['ln'])
            redirect_to_url(req, referer)

    def subscribe(self, req, form):
        """
        Subscribe current user to receive email notification when new
        comments are added to current discussion.
        """
        argd = wash_urlargd(form, {'referer': (str, None)})

        uid = getUid(req)

        user_info = collect_user_info(req)
        (auth_code, auth_msg) = check_user_can_view_comments(user_info, self.recid)
        if isGuestUser(uid):
            cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : guess_primary_collection_of_a_record(self.recid)})
            target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : \
                CFG_SITE_SECURE_URL + user_info['uri']}, {})
            return redirect_to_url(req, target, norobot=True)
        elif auth_code:
            return page_not_authorized(req, "../", \
                text = auth_msg)

        success = subscribe_user_to_discussion(self.recid, uid)
        display_url = "%s/%s/%s/comments/display?subscribed=%s&ln=%s" % \
                      (CFG_SITE_SECURE_URL, CFG_SITE_RECORD, self.recid, str(success), argd['ln'])
        redirect_to_url(req, display_url)

    def unsubscribe(self, req, form):
        """
        Unsubscribe current user from current discussion.
        """
        argd = wash_urlargd(form, {'referer': (str, None)})

        user_info = collect_user_info(req)
        uid = getUid(req)

        if isGuestUser(uid):
            cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : guess_primary_collection_of_a_record(self.recid)})
            target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : \
                CFG_SITE_SECURE_URL + user_info['uri']}, {})
            return redirect_to_url(req, target, norobot=True)

        success = unsubscribe_user_from_discussion(self.recid, uid)
        display_url = "%s/%s/%s/comments/display?subscribed=%s&ln=%s" % \
                      (CFG_SITE_SECURE_URL, CFG_SITE_RECORD, self.recid, str(-success), argd['ln'])
        redirect_to_url(req, display_url)

    def toggle(self, req, form):
        """
        Store the visibility of a comment for current user
        """
        argd = wash_urlargd(form, {'comid': (int, -1),
                                   'referer': (str, None),
                                   'collapse': (int, 1)})

        uid = getUid(req)

        if isGuestUser(uid):
            # We do not store information for guests
            return ''

        toggle_comment_visibility(uid, argd['comid'], argd['collapse'], self.recid)
        if argd['referer']:
            return redirect_to_url(req, CFG_SITE_SECURE_URL + \
                                   (not argd['referer'].startswith('/') and '/' or '') + \
                                   argd['referer'] + '#' + str(argd['comid']))

class WebInterfaceCommentsFiles(WebInterfaceDirectory):
    """Handle <strike>upload and </strike> access to files for comments.

       <strike>The upload is currently only available through the Ckeditor.</strike>
    """

    #_exports = ['put'] # 'get' is handled by _lookup(..)

    def __init__(self, recid=-1, reviews=0):
        self.recid = recid
        self.discussion = reviews # 0:comments, 1:reviews

    def _lookup(self, component, path):
        """ This handler is invoked for the dynamic URLs (for getting
        <strike>and putting attachments</strike>) Eg:
        CFG_SITE_URL/CFG_SITE_RECORD/5953/comments/attachments/get/652/myfile.pdf
        """
        if component == 'get' and len(path) > 1:

            comid = path[0] # comment ID

            file_name = '/'.join(path[1:]) # the filename

            def answer_get(req, form):
                """Accessing files attached to comments."""
                form['file'] = file_name
                form['comid'] = comid
                return self._get(req, form)

            return answer_get, []

        # All other cases: file not found
        return None, []

    def _get(self, req, form):
        """
        Returns a file attached to a comment.

        Example:
        CFG_SITE_URL/CFG_SITE_RECORD/5953/comments/attachments/get/652/myfile.pdf
        where 652 is the comment ID
        """
        argd = wash_urlargd(form, {'file': (str, None),
                                   'comid': (int, 0)})
        _ = gettext_set_language(argd['ln'])

        # Can user view this record, i.e. can user access its
        # attachments?
        uid = getUid(req)
        user_info = collect_user_info(req)
        # Check that user can view record, and its comments (protected
        # with action "viewcomment")
        (auth_code, auth_msg) = check_user_can_view_comments(user_info, self.recid)
        if auth_code and user_info['email'] == 'guest':
            cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : guess_primary_collection_of_a_record(self.recid)})
            target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : \
                CFG_SITE_SECURE_URL + user_info['uri']}, {})
            return redirect_to_url(req, target, norobot=True)
        elif auth_code:
            return page_not_authorized(req, "../", \
                                       text = auth_msg)

        # Does comment exist?
        if not query_get_comment(argd['comid']):
            req.status = apache.HTTP_NOT_FOUND
            return page(title=_("Page Not Found"),
                        body=_('The requested comment could not be found'),
                        req=req)

        # Check that user can view this particular comment, protected
        # using its own restriction
        (auth_code, auth_msg) = check_user_can_view_comment(user_info, argd['comid'])
        if auth_code and user_info['email'] == 'guest':
            cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : guess_primary_collection_of_a_record(self.recid)})
            target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : \
                CFG_SITE_SECURE_URL + user_info['uri']}, {})
            return redirect_to_url(req, target)
        elif auth_code:
            return page_not_authorized(req, "../", \
                                       text = auth_msg,
                                       ln=argd['ln'])

        # Check that comment is not currently deleted
        if is_comment_deleted(argd['comid']):
            return page_not_authorized(req, "../", \
                                       text = _("You cannot access files of a deleted comment"),
                                       ln=argd['ln'])

        if not argd['file'] is None:
            # Prepare path to file on disk. Normalize the path so that
            # ../ and other dangerous components are removed.
            path = os.path.abspath(os.path.join(CFG_COMMENTSDIR,
                                                str(self.recid),
                                                str(argd['comid']),
                                                argd['file']))

            # Check that we are really accessing attachements
            # directory, for the declared record.
            if path.startswith(os.path.join(CFG_COMMENTSDIR,
                                            str(self.recid))) and \
                    os.path.exists(path):
                return stream_file(req, path)

        # Send error 404 in all other cases
        req.status = apache.HTTP_NOT_FOUND
        return page(title=_("Page Not Found"),
                    body=_('The requested file could not be found'),
                    req=req,
                    language=argd['ln'])

class WebInterfaceYourCommentsPages(WebInterfaceDirectory):
    """Defines the set of /yourcomments pages."""

    _exports = ['', ]

    def index(self, req, form):
        """Index page."""

        argd = wash_urlargd(form, {'page': (int, 1),
                                   'format': (str, "rc"),
                                   'order_by': (str, "lcf"),
                                   'per_page': (str, "all"),
                                   })
        # TODO: support also "reviews", by adding  new option to show/hide them if needed
        uid = getUid(req)

        # load the right language
        _ = gettext_set_language(argd['ln'])

        # Is site ready to accept comments?
        if not CFG_WEBCOMMENT_ALLOW_COMMENTS or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "%s/yourcomments" % \
                                             (CFG_SITE_SECURE_URL,),
                                       text="Comments are currently disabled on this site",
                                       navmenuid="yourcomments")
        elif uid == -1 or isGuestUser(uid):
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({
                    'referer' : "%s/yourcomments%s" % (
                        CFG_SITE_SECURE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        user_info = collect_user_info(req)
        if not user_info['precached_sendcomments']:
            # Maybe we should still authorize if user submitted
            # comments in the past?
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use comments."))

        return page(title=_("Your Comments"),
                    body=perform_display_your_comments(user_info,
                                                       page_number=argd['page'],
                                                       selected_order_by_option=argd['order_by'],
                                                       selected_display_number_option=argd['per_page'],
                                                       selected_display_format_option=argd['format'],
                                                       ln=argd['ln']),
                    navtrail= """<a class="navtrail" href="%(sitesecureurl)s/youraccount/display?ln=%(ln)s">%(account)s</a>""" % {
                                 'sitesecureurl' : CFG_SITE_SECURE_URL,
                                 'ln': argd['ln'],
                                 'account' : _("Your Account"),
                              },
                    description=_("%(x_name)s View your previously submitted comments", x_name=CFG_SITE_NAME_INTL.get(argd['ln'], CFG_SITE_NAME)),
                    keywords=_("%(x_name)s, personalize", x_name=CFG_SITE_NAME_INTL.get(argd['ln'], CFG_SITE_NAME)),
                    uid=uid,
                    language=argd['ln'],
                    req=req,
                    lastupdated=__lastupdated__,
                    navmenuid='youralerts',
                    secure_page_p=1)

    # Return the same page wether we ask for /CFG_SITE_RECORD/123 or /CFG_SITE_RECORD/123/
    __call__ = index
