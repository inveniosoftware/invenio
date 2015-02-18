# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012,
#               2015 CERN.
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

__revision__ = "$Id$"

# import interesting modules:

from invenio.config import \
     CFG_ACCESS_CONTROL_LEVEL_SITE, \
     CFG_SITE_LANG, \
     CFG_SITE_NAME, \
     CFG_SITE_SECURE_URL
from invenio.legacy.dbquery import run_sql
from invenio.modules.access.engine import acc_authorize_action
from invenio.modules.access.control import acc_find_possible_roles
from invenio.legacy.webpage import page, error_page
from invenio.legacy.webuser import getUid, get_email, page_not_authorized, collect_user_info
from invenio.base.i18n import gettext_set_language, wash_language

from sqlalchemy.exc import SQLAlchemyError as Error

import invenio.legacy.template
websubmit_templates = invenio.legacy.template.load('websubmit')

def index(req, c=CFG_SITE_NAME, ln=CFG_SITE_LANG, order="", doctype="", deletedId="", deletedAction="", deletedDoctype=""):
    ln = wash_language(ln)

    # load the right message language
    _ = gettext_set_language(ln)

    t = ""
    # get user ID:
    try:
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../yourapprovals.py/index",
                                       navmenuid='yourapprovals')
        u_email = get_email(uid)
    except Error as e:
        return error_page(str(e), req, ln=ln)

    user_info = collect_user_info(req)
    if not user_info['precached_useapprove']:
        return page_not_authorized(req, "../", \
                                    text = _("You are not authorized to use approval system."))

    res = run_sql("SELECT sdocname,ldocname FROM sbmDOCTYPE ORDER BY ldocname")
    referees = []
    for row in res:
        doctype = row[0]
        docname = row[1]
        reftext = ""
        if isRefereed(doctype) and __isReferee(req, doctype):
            referees.append ({'doctype': doctype,
                              'docname': docname,
                              'categories': None})
        else:
            res2 = run_sql("select sname,lname from sbmCATEGORIES where doctype=%s", (doctype,))
            categories = []
            for row2 in res2:
                category = row2[0]
                categname = row2[1]
                if isRefereed(doctype, category) and __isReferee(req, doctype, category):
                    categories.append({
                                        'id' : category,
                                        'name' : categname,
                                      })
            if categories:
                referees.append({
                            'doctype' : doctype,
                            'docname' : docname,
                            'categories' : categories
                           })

    t = websubmit_templates.tmpl_yourapprovals(ln=ln, referees=referees)
    return page(title=_("Your Approvals"),
                navtrail= """<a class="navtrail" href="%(sitesecureurl)s/youraccount/display">%(account)s</a>""" % {
                             'sitesecureurl' : CFG_SITE_SECURE_URL,
                             'account' : _("Your Account"),
                          },
                body=t,
                description="",
                keywords="",
                uid=uid,
                language=ln,
                req=req,
                navmenuid='yourapprovals')

def __isReferee(req, doctype="", categ="*"):
    (auth_code, auth_message) = acc_authorize_action(req, "referee", doctype=doctype, categ=categ)
    if auth_code == 0:
        return 1
    else:
        return 0

def isRefereed(doctype, categ="*"):
    """Check if the given doctype, categ is refereed by at least a role. different than SUPERADMINROLE"""
    roles = acc_find_possible_roles('referee', always_add_superadmin=False, doctype=doctype, categ=categ)
    if roles:
        return True
    return False
