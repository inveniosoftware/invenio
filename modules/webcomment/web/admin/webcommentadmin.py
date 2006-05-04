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

__lastupdated__ = """$Date$"""

from invenio.webcommentadminlib import *
from invenio.bibrankadminlib import check_user
from invenio.webpage import page, create_error_box
from invenio.config import weburl,cdslang
from invenio.webuser import getUid, page_not_authorized
from invenio.urlutils import wash_url_argument, redirect_to_url
from invenio.messages import wash_language, gettext_set_language

def index(req, ln=cdslang):
    """
    Menu of admin options
    @param ln: language  
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = getnavtrail()
    navtrail_previous_links +=' &gt; <a class="navtrail" href="%s/admin/webcomment/webcommentadmin.py/">' % weburl
    navtrail_previous_links += _("Comment Management") + '</a>'

    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)

    (auth_code, auth_msg) = check_user(uid, 'cfgwebcomment')
    if not auth_code:
        return page(title=_("Comment Management"),
                body=perform_request_index(ln=ln),
                uid=uid,
                language=ln,
                urlargs=req.args,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__,
                req=req)   
    else:
        return page_not_authorized(req=req, text=auth_msg, navtrail=navtrail_previous_links)

def delete(req, ln=cdslang, comid=""):
    """
    Delete a comment by giving its comment id
    @param ln: language
    @param comid: comment id
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = getnavtrail()
    navtrail_previous_links += ' &gt; <a class="navtrail" href="%s/admin/webcomment/webcommentadmin.py/">' % weburl
    navtrail_previous_links += _("Comment Management") + '</a>'

    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)
                                                                                                                                                                                                     
    (auth_code, auth_msg) = check_user(uid,'cfgwebcomment')
    if not auth_code:
        (body, errors, warnings) = perform_request_delete(ln=ln, comID=comid)
        return page(title=_("Delete Comment"),
                body=body,
                uid=uid,
                language=ln,
                urlargs=req.args,
                navtrail = navtrail_previous_links,
                req = req,
                errors = errors, 
                warnings = warnings,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth_msg, navtrail=navtrail_previous_links)


def comments(req, ln=cdslang, uid="", comid="", reviews=0):
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
    navtrail_previous_links += ' &gt; <a class="navtrail" href="%s/admin/webcomment/webcommentadmin.py/">' % weburl
    navtrail_previous_links += _("Comment Management") + '</a>'
    
    try:
        auid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)
    
    (auth_code, auth_msg) = check_user(auid,'cfgwebcomment')
    if not auth_code:
        if reviews==0:
            raise ValueError
        return page(title=_("View all Reported %s") % (reviews>0 and _("Reviews") or _("Comments")),
                body=perform_request_comments(ln=ln, uid=uid, comID=comid, reviews=reviews),
                uid=auid,
                language=ln,
                urlargs=req.args,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__,
                req=req)
    else:
        return page_not_authorized(req=req, text=auth_msg, navtrail=navtrail_previous_links)


def users(req, ln=cdslang):
    """
    View a list of all the users that have been reported, sorted by most reported
    @param ln: language 
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = getnavtrail()
    navtrail_previous_links += ' &gt; <a class="navtrail" href="%s/admin/webcomment/webcommentadmin.py/">' % weburl
    navtrail_previous_links += _("Comment Management") + '</a>'

    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)
    (auth_code, auth_msg) = check_user(uid,'cfgwebcomment')
    if not auth_code:
        return page(title=_("View all Reported Users"),
                    body=perform_request_users(ln=ln),
                    uid=uid,
                    language=ln,
                    urlargs=req.args,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)
    else:

        return page_not_authorized(req=req, text=auth_msg, navtrail=navtrail_previous_links)

def del_com(req, ln=cdslang, action="delete", **hidden):
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
    navtrail_previous_links += ' &gt; <a class="navtrail" href="%s/admin/webcomment/webcommentadmin.py/">' % weburl
    navtrail_previous_links += _("Comment Management") + '</a>'

    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)
    (auth_code, auth_msg) = check_user(uid,'cfgwebcomment')
    if not auth_code:
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
            redirect_to_url(req, weburl + '/admin/webcomment/webcommentadmin.py')
        return page(title=title,
                    body=body,
                    uid=uid,
                    language=ln,
                    urlargs=req.args,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)
    else:
        return page_not_authorized(req=req, text=auth_msg, navtrail=navtrail_previous_links)
