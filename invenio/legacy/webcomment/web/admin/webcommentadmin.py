# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2015 CERN.
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

"""Comments and reviews administrative interface."""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

from invenio.legacy.webcomment.adminlib import *
from invenio.legacy.bibrank.adminlib import check_user
from invenio.legacy.webpage import page, create_error_box
from invenio.config import CFG_SITE_SECURE_URL,CFG_SITE_LANG,CFG_SITE_NAME
from invenio.legacy.webuser import getUid, page_not_authorized, collect_user_info
from invenio.utils.url import wash_url_argument, redirect_to_url
from invenio.base.i18n import wash_language, gettext_set_language
from invenio.modules.access.engine import acc_authorize_action

from sqlalchemy.exc import SQLAlchemyError as Error


def index(req, ln=CFG_SITE_LANG):
    """
    Menu of admin options
    @param ln: language
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = getnavtrail()
    navtrail_previous_links +=' &gt; <a class="navtrail" href="%s/admin/webcomment/webcommentadmin.py/">' % CFG_SITE_URL
    navtrail_previous_links += _("WebComment Admin") + '</a>'

    try:
        uid = getUid(req)
    except Error:
        return page(title=_("Internal Error"),
                    body = create_error_box(req, verbose=0, ln=ln),
                    description="%s - Internal Error" % CFG_SITE_NAME,
                    keywords="%s, Internal Error" % CFG_SITE_NAME,
                    language=ln,
                    req=req)

    (auth_code, auth_msg) = check_user(req, 'cfgwebcomment')
    if (auth_code != 'false'):
        return page(title=_("WebComment Admin"),
                body=perform_request_index(ln=ln),
                uid=uid,
                language=ln,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__,
                req=req)
    else:
        return page_not_authorized(req=req, text=auth_msg, navtrail=navtrail_previous_links)

def delete(req, ln=CFG_SITE_LANG, comid="", recid="", uid="", reviews=""):
    """
    Delete a comment by giving its comment id
    @param req: request object to obtain user information
    @param ln: language
    @param comid: comment id
    @param recid: ID of the record containing the comment
    @param uid: id of the user
    @param reviews: boolean 1 if deleting a review, 0 if deleting a comment
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = getnavtrail()
    navtrail_previous_links += ' &gt; <a class="navtrail" href="%s/admin/webcomment/webcommentadmin.py/">' % CFG_SITE_URL
    navtrail_previous_links += _("WebComment Admin") + '</a>'

    try:
        uid = getUid(req)
    except Error:
        return page(title=_("Internal Error"),
                    body = create_error_box(req, verbose=0, ln=ln),
                    description="%s - Internal Error" % CFG_SITE_NAME,
                    keywords="%s, Internal Error" % CFG_SITE_NAME,
                    language=ln,
                    req=req)

    (auth_code, auth_msg) = check_user(req,'cfgwebcomment')
    if (auth_code != 'false'):
        body = perform_request_delete(ln=ln,
                                      comID=comid,
                                      recID=recid,
                                      uid=uid,
                                      reviews=reviews)
        return page(title=(reviews=='1' and _("Delete/Undelete Reviews") or _("Delete/Undelete Comments")) + _(" or Suppress abuse reports"),
                body=body,
                uid=uid,
                language=ln,
                navtrail = navtrail_previous_links,
                req = req,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth_msg, navtrail=navtrail_previous_links)

def comments(req, ln=CFG_SITE_LANG, uid="", comid="", reviews=0, collection=""):
    """
    View reported comments, filter by either user or a specific comment (only one given at a time)
    @param req: request object to obtain user information
    @param ln: language
    @param uid: user id
    @param comid: comment id
    @param reviews: boolean enabled for reviews, disabled for comments
    @param collection: filter results by collection
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = getnavtrail()
    navtrail_previous_links += ' &gt; <a class="navtrail" href="%s/admin/webcomment/webcommentadmin.py/">' % CFG_SITE_URL
    navtrail_previous_links += _("WebComment Admin") + '</a>'

    try:
        auid = getUid(req)
    except Error:
        return page(title=_("Internal Error"),
                    body = create_error_box(req, verbose=0, ln=ln),
                    description="%s - Internal Error" % CFG_SITE_NAME,
                    keywords="%s, Internal Error" % CFG_SITE_NAME,
                    language=ln,
                    req=req)

    (auth_code, auth_msg) = check_user(auid, 'cfgwebcomment')
    if (auth_code != 'false'):
        return page(title=(reviews=='0' and _("View all comments reported as abuse") or _("View all reviews reported as abuse")),
                    body=perform_request_comments(req, ln=ln, uid=uid, comID=comid, reviews=reviews, abuse=True, collection=collection),
                    uid=auid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)
    else:
        return page_not_authorized(req=req, text=auth_msg, navtrail=navtrail_previous_links)

def hot(req, ln=CFG_SITE_LANG, comments=1, top=10, collection=""):
    """
    View most active comments/reviews
    @param req: request object to obtain user information
    @param ln: language
    @param comments: boolean enabled for comments, disabled for reviews
    @param top: number of results to be shown
    @param collection: filter results by collection
    """
    ln = wash_language(ln)
    collection = wash_url_argument(collection, 'str')
    _ = gettext_set_language(ln)
    navtrail_previous_links = getnavtrail()
    navtrail_previous_links += ' &gt; <a class="navtrail" href="%s/admin/webcomment/webcommentadmin.py/">' % CFG_SITE_URL
    navtrail_previous_links += _("WebComment Admin") + '</a>'

    user_info = collect_user_info(req)
    (auth_code, auth_msg) = acc_authorize_action(user_info, 'cfgwebcomment')
    if auth_code:
        return page_not_authorized(req=req, text=auth_msg, navtrail=navtrail_previous_links)
    return page(title=(comments=='0' and _("View most reviewed records") or
                           _("View most commented records")),
                    body=perform_request_hot(req, ln=ln, comments=comments, top=top, collection=collection),
                    uid=user_info['uid'],
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)

def latest(req, ln=CFG_SITE_LANG, comments=1, top=10, collection=""):
    """
    View latest comments/reviews
    @param req: request object to obtain user information
    @param ln: language
    @param comments: boolean enabled for comments, disabled for reviews
    @param top: number of results to be shown
    @param collection: filter results by collection
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = getnavtrail()
    navtrail_previous_links += ' &gt; <a class="navtrail" href="%s/admin/webcomment/webcommentadmin.py/">' % CFG_SITE_URL
    navtrail_previous_links += _("WebComment Admin") + '</a>'

    try:
        auid = getUid(req)
    except Error:
        return page(title=_("Internal Error"),
                    body = create_error_box(req, verbose=0, ln=ln),
                    description="%s - Internal Error" % CFG_SITE_NAME,
                    keywords="%s, Internal Error" % CFG_SITE_NAME,
                    language=ln,
                    req=req)

    (auth_code, auth_msg) = check_user(auid, 'cfgwebcomment')
    if (auth_code != 'false'):
        return page(title=(comments=='0' and _("View latest reviewed records") or
                           _("View latest commented records")),
                    body=perform_request_latest(req=req, ln=ln, comments=comments, top=top, collection=collection),
                    uid=auid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)
    else:
        return page_not_authorized(req=req, text=auth_msg, navtrail=navtrail_previous_links)


def users(req, ln=CFG_SITE_LANG):
    """
    View a list of all the users that have been reported, sorted by most reported
    @param req: request object to obtain user information
    @param ln: language
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = getnavtrail()
    navtrail_previous_links += ' &gt; <a class="navtrail" href="%s/admin/webcomment/webcommentadmin.py/">' % CFG_SITE_URL
    navtrail_previous_links += _("WebComment Admin") + '</a>'

    try:
        uid = getUid(req)
    except Error:
        return page(title=_("Internal Error"),
                    body = create_error_box(req, verbose=0, ln=ln),
                    description="%s - Internal Error" % CFG_SITE_NAME,
                    keywords="%s, Internal Error" % CFG_SITE_NAME,
                    language=ln,
                    req=req)

    (auth_code, auth_msg) = check_user(req,'cfgwebcomment')
    if (auth_code != 'false'):
        return page(title=_("View all reported users"),
                    body=perform_request_users(ln=ln),
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)
    else:

        return page_not_authorized(req=req, text=auth_msg, navtrail=navtrail_previous_links)

def del_com(req, ln=CFG_SITE_LANG, action="delete", **hidden):
    """
    private function
    Delete a comment
    @param req: request object to obtain user information
    @param ln: language
    @param **hidden: ids of comments to delete sent as individual variables comidX=on, where X is id
    """
    ln = wash_language(ln)
    action = wash_url_argument(action, 'str')
    _ = gettext_set_language(ln)
    navtrail_previous_links = getnavtrail()
    navtrail_previous_links += ' &gt; <a class="navtrail" href="%s/admin/webcomment/webcommentadmin.py/">' % CFG_SITE_URL
    navtrail_previous_links += _("WebComment Admin") + '</a>'

    try:
        uid = getUid(req)
    except Error:
        return page(title=_("Internal Error"),
                    body = create_error_box(req, verbose=0, ln=ln),
                    description="%s - Internal Error" % CFG_SITE_NAME,
                    keywords="%s, Internal Error" % CFG_SITE_NAME,
                    language=ln,
                    req=req)

    (auth_code, auth_msg) = check_user(req,'cfgwebcomment')
    if (auth_code != 'false'):
        comIDs = []
        args = hidden.keys()
        for var in args:
            try:
                comIDs.append(int(var.split('comid')[1]))
            except:
                pass
        if action == 'delete':
            body = perform_request_del_com(ln=ln, comIDs=comIDs)
            title = _("Delete comments")
        elif action == 'unreport':
            body = suppress_abuse_report(ln=ln, comIDs=comIDs)
            title = _("Suppress abuse reports")
        elif action == 'undelete':
            body = perform_request_undel_com(ln=ln, comIDs=comIDs)
            title = _("Undelete comments")
        else:
            redirect_to_url(req, CFG_SITE_SECURE_URL + '/admin/webcomment/webcommentadmin.py')
        return page(title=title,
                    body=body,
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)
    else:
        return page_not_authorized(req=req, text=auth_msg, navtrail=navtrail_previous_links)

def undel_com(req, ln=CFG_SITE_LANG, id=""):
    """
    Undelete a comment
    @param req: request object to obtain user information
    @param ln: language
    @param id: comment id
    """
    ln = wash_language(ln)
    user_info = collect_user_info(req)
    referer = user_info['referer']
    (auth_code, auth_msg) = check_user(req,'cfgwebcomment')
    if (auth_code != 'false'):
        perform_request_undel_single_com(ln=ln, id=id)
        redirect_to_url(req, referer)
    else:
        return page_not_authorized(req=req, text=auth_msg)

def del_single_com_mod(req, ln=CFG_SITE_LANG, id=""):
    """
    Allow moderator to delete a single comment
    @param req: request object to obtain user information
    @param ln: language
    @param id: comment id
    """
    ln = wash_language(ln)
    user_info = collect_user_info(req)
    referer = user_info['referer']
    (auth_code, auth_msg) = check_user(req,'cfgwebcomment')
    if (auth_code != 'false') or check_user_is_author(user_info['uid'], id):
        perform_request_del_single_com_mod(ln=ln, id=id)
        redirect_to_url(req, referer)
    else:
        return page_not_authorized(req=req, text=auth_msg)

def del_single_com_auth(req, ln=CFG_SITE_LANG, id=""):
    """
    Allow author to delete a single comment
    @param req: request object to obtain user information
    @param ln: language
    @param id: comment id
    """
    ln = wash_language(ln)
    user_info = collect_user_info(req)
    referer = user_info['referer']
    (auth_code, auth_msg) = check_user(req,'cfgwebcomment')
    if (auth_code != 'false') or check_user_is_author(user_info['uid'], id):
        perform_request_del_single_com_auth(ln=ln, id=id)
        redirect_to_url(req, referer)
    else:
        return page_not_authorized(req=req, text=auth_msg)

def unreport_com(req, ln=CFG_SITE_LANG, id=""):
    """
    Unreport a comment
    @param req: request object to obtain user information
    @param ln: language
    @param id: comment id
    """
    ln = wash_language(ln)
    user_info = collect_user_info(req)
    referer = user_info['referer']
    (auth_code, auth_msg) = check_user(req,'cfgwebcomment')
    if (auth_code != 'false'):
        perform_request_unreport_single_com(ln=ln, id=id)
        redirect_to_url(req, referer)
    else:
        return page_not_authorized(req=req, text=auth_msg)
