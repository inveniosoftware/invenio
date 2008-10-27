# -*- coding: utf-8 -*-
##
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

"""Comments and reviews administrative interface."""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

from invenio.webcommentadminlib import *
from invenio.bibrankadminlib import check_user
from invenio.webpage import page, create_error_box
from invenio.config import CFG_SITE_URL,CFG_SITE_LANG,CFG_SITE_NAME
from invenio.dbquery import Error
from invenio.webuser import getUid, page_not_authorized
from invenio.urlutils import wash_url_argument, redirect_to_url
from invenio.messages import wash_language, gettext_set_language

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
    @param ln: language
    @param comid: comment id
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
        (body, errors, warnings) = perform_request_delete(ln=ln,
                                                          comID=comid,
                                                          recID=recid,
                                                          uid=uid,
                                                          reviews=reviews)
        return page(title=(reviews=='1' and _("Delete Reviews") or _("Delete Comments")) +' / ' + _("Suppress abuse reports"),
                body=body,
                uid=uid,
                language=ln,
                navtrail = navtrail_previous_links,
                req = req,
                errors = errors,
                warnings = warnings,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth_msg, navtrail=navtrail_previous_links)


def comments(req, ln=CFG_SITE_LANG, uid="", comid="", reviews=0):
    """
    View reported comments, filter by either user or a specific comment (only one given at a time)
    @param ln: language
    @param uid: user id
    @param comid: comment id
    @param reviews: boolean enabled for reviews, disabled for comments
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
        return page(title=(reviews=='0' and _("View all reported comments") or _("View all reported reviews")),
                    body=perform_request_comments(ln=ln, uid=uid, comID=comid, reviews=reviews, abuse=True),
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
    private funciton
    Delete a comment
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
        else:
            redirect_to_url(req, CFG_SITE_URL + '/admin/webcomment/webcommentadmin.py')
        return page(title=title,
                    body=body,
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)
    else:
        return page_not_authorized(req=req, text=auth_msg, navtrail=navtrail_previous_links)
