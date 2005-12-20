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

__lastupdated__ = """$Date$"""

from cdsware.webcommentadminlib import *
from cdsware.webpage import page, create_error_box
from cdsware.config import weburl,cdslang
from cdsware.webuser import getUid, page_not_authorized

def index(req, ln=cdslang):
    """
    Menu of admin options
    @param ln: language  
    """
    navtrail_previous_links = getnavtrail() + """ &gt; <a class="navtrail" href="%s/admin/webcomment/webcommentadmin.py/">Comment Management</a>""" % (weburl,)

    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)

    (auth_code, auth_msg) = check_user(uid,'cfgwebcomment')
    if not auth_code:
        return page(title="Comment Management",
                body=perform_request_index(ln=ln),
                uid=uid,
                language=ln,
                urlargs=req.args,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)   
    else:
        return page_not_authorized(req=req, text=auth_msg, navtrail=navtrail_previous_links)

def delete(req, ln=cdslang, comid=""):
    """
    Delete a comment by giving its comment id
    @param ln: language
    @param comid: comment id
    """
    navtrail_previous_links = getnavtrail() + """ &gt; <a class="navtrail" href="%s/admin/webcomment/webcommentadmin.py/">Comment Management</a>""" % (weburl,)
                                                                                                                                                                                                     
    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)
                                                                                                                                                                                                     
    (auth_code, auth_msg) = check_user(uid,'cfgwebcomment')
    if not auth_code:
        (body, errors, warnings) = perform_request_delete(ln=ln, comID=comid)
        return page(title="Delete Comment",
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
    navtrail_previous_links = getnavtrail() + """ &gt; <a class="navtrail" href="%s/admin/webcomment/webcommentadmin.py/">Comment Management</a>""" % (weburl,)
                                                                                                                                                                                                     
    try:
        auid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)
                                                                                                                                                                                                     
    (auth_code, auth_msg) = check_user(auid,'cfgwebcomment')
    if not auth_code:
        return page(title="View all Reported %s" % (reviews>0 and "Reviews" or "Comments",),
                body=perform_request_comments(ln=ln, uid=uid, comID=comid, reviews=reviews),
                uid=auid,
                language=ln,
                urlargs=req.args,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth_msg, navtrail=navtrail_previous_links)


def users(req, ln=cdslang):
    """
    View a list of all the users that have been reported, sorted by most reported
    @param ln: language 
    """
    navtrail_previous_links = getnavtrail() + """ &gt; <a class="navtrail" href="%s/admin/webcomment/webcommentadmin.py/">Comment Management</a>""" % (weburl,)
                                                                                                                                                                                                     
    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)
                                                                                                                                                                                                     
    (auth_code, auth_msg) = check_user(uid,'cfgwebcomment')
    if not auth_code:
        return page(title="View all Reported Users",
                body=perform_request_users(ln=ln),
                uid=uid,
                language=ln,
                urlargs=req.args,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth_msg, navtrail=navtrail_previous_links)

def del_com(req, ln=cdslang, **hidden):
    """
    private funciton
    Delete a comment
    @param ln: language
    @param **hidden: ids of comments to delete sent as individual variables comidX=on, where X is id
    """
    navtrail_previous_links = getnavtrail() + """ &gt; <a class="navtrail" href="%s/admin/webcomment/webcommentadmin.py/">Comment Management</a>""" % (weburl,)
                                                                                                                                                                                                     
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
        return page(title="Delete Comments",
                body=perform_request_del_com(ln=ln, comIDs=comIDs),
                uid=uid,
                language=ln,
                urlargs=req.args,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth_msg, navtrail=navtrail_previous_links)

