# -*- coding: utf-8 -*-
## $Id$
## Migrate PHP version of Bibformat to Python version

## This file is part of CDS Invenio.
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

from invenio.bibformat_migration_kit_assistant_lib import *
from invenio.bibrankadminlib import check_user
from invenio.webpage import page, create_error_box
from invenio.config import weburl,cdslang
from invenio.webuser import getUid, page_not_authorized
from invenio.urlutils import wash_url_argument, redirect_to_url
from invenio.messages import wash_language, gettext_set_language

def index(req, ln=cdslang):
    """
    Shows status of migration and options to continue migration
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = getnavtrail()

    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)

    (auth_code, auth_msg) = check_user(uid, 'cfgbibformat')
    if not auth_code:
        return page(title=_("Migrate Bibformat Settings"),
                body=perform_request_migration_kit_status(ln=ln),
                uid=uid,
                language=ln,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__,
                req=req)   
    else:
        return page_not_authorized(req=req, text=auth_msg, navtrail=navtrail_previous_links)

  
def migrate_kb(req, ln=cdslang):
    """
    Migrate kbs and tell users the result of migration
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = getnavtrail(' &gt; <a class=navtrail href="%s/admin/bibformat/bibformat_migration_kit_assistant.py">Migration Kit</a>'%weburl)

    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)

    (auth_code, auth_msg) = check_user(uid, 'cfgbibformat')
    if not auth_code:
        return page(title=_("Migrate Knowledge Bases"),
                body=perform_request_migration_kit_knowledge_bases(ln=ln),
                uid=uid,
                language=ln,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__,
                req=req)   
    else:
        return page_not_authorized(req=req, text=auth_msg, navtrail=navtrail_previous_links)


def migrate_behaviours(req, ln=cdslang):
    """
    Migrate behaviours and tell users the result of migration
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = getnavtrail(' &gt; <a class=navtrail href="%s/admin/bibformat/bibformat_migration_kit_assistant.py">Migration Kit</a>'%weburl)

    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)

    (auth_code, auth_msg) = check_user(uid, 'cfgbibformat')
    if not auth_code:
        return page(title=_("Migrate Behaviours"),
                body=perform_request_migration_kit_behaviours(ln=ln),
                uid=uid,
                language=ln,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__,
                req=req)   
    else:
        return page_not_authorized(req=req, text=auth_msg, navtrail=navtrail_previous_links)

def migrate_formats(req, ln=cdslang):
    """
    Shows the interface for migrating formats to format templates and format elements
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = getnavtrail(' &gt; <a class=navtrail href="%s/admin/bibformat/bibformat_migration_kit_assistant.py">Migration Kit</a>'%weburl)

    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)

    (auth_code, auth_msg) = check_user(uid, 'cfgbibformat')
    if not auth_code:
        return page(title=_("Migrate Formats"),
                body=perform_request_migration_kit_formats(ln=ln),
                uid=uid,
                language=ln,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__,
                req=req)   
    else:
        return page_not_authorized(req=req, text=auth_msg, navtrail=navtrail_previous_links) 

def migrate_formats_do(req, ln=cdslang):
    """
    Migrate formats and tell user how migration went
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = getnavtrail(' &gt; <a class=navtrail href="%s/admin/bibformat/bibformat_migration_kit_assistant.py">Migration Kit</a>'%weburl)

    try:
        uid = getUid(req)
    except MySQLdb.Error, e:
        return error_page(req)

    (auth_code, auth_msg) = check_user(uid, 'cfgbibformat')
    if not auth_code:
        return page(title=_("Migrate Formats"),
                body=perform_request_migration_kit_formats_do(ln=ln),
                uid=uid,
                language=ln,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__,
                req=req)   
    else:
        return page_not_authorized(req=req, text=auth_msg, navtrail=navtrail_previous_links) 
