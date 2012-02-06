## This file is part of Invenio.
## Copyright (C) 2011, 2012 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Invenio BibSort Administrator Interface."""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

from invenio.webpage import page, create_error_box
from invenio.config import CFG_SITE_URL, CFG_SITE_LANG, CFG_SITE_NAME
from invenio.dbquery import Error
from invenio.webuser import getUid, page_not_authorized
from invenio.urlutils import wash_url_argument
from invenio import bibsortadminlib as bsc


def index(req, ln=CFG_SITE_LANG, action='', bsrID='', sm_name='', sm_def_type='', sm_def_value='', sm_washer='', sm_locale=''):
    """
    Display the initial(main) page
    """
    navtrail_previous_links = bsc.getnavtrail()

    try:
        uid = getUid(req)
    except Error:
        return error_page(req)

    auth = bsc.check_user(req,'cfgbibsort')
    if not auth[0]:
        action = wash_url_argument(action, 'str')
        bsrID = wash_url_argument(bsrID, 'int')
        sm_name = wash_url_argument(sm_name, 'str')
        sm_def_type = wash_url_argument(sm_def_type, 'str')
        sm_def_value = wash_url_argument(sm_def_value, 'str')
        sm_washer = wash_url_argument(sm_washer, 'str')
        sm_locale = wash_url_argument(sm_locale, 'str')
        return page(title="BibSort Admin Interface",
                body=bsc.perform_index(ln, action, bsrID, sm_name, sm_def_type, sm_def_value, sm_washer, sm_locale),
                uid=uid,
                language=ln,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__,
                req=req)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


def modifytranslations(req, ln=CFG_SITE_LANG, bsrID='', trans=None, confirm=0):
    """
    Display the modify translations page
    """
    navtrail_previous_links = bsc.getnavtrail()+ """&gt; <a class="navtrail" href="%s/admin/bibsort/bibsortadmin.py/">BibSort Admin Interface</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except Error:
        return error_page(req)

    auth = bsc.check_user(req,'cfgbibsort')
    if not auth[0]:
        bsrID = wash_url_argument(bsrID, 'int')
        confirm = wash_url_argument(confirm, 'int')
        return page(title="Modify translations",
                    body=bsc.perform_modifytranslations(ln, bsrID, trans, confirm),
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


def error_page(req, ln=CFG_SITE_LANG, verbose=1):
    """
    Returns a default error page
    """
    return page(title="Internal Error",
                body = create_error_box(req, verbose=verbose, ln=ln),
                description="%s - Internal Error" % CFG_SITE_NAME,
                keywords="%s, Internal Error" % CFG_SITE_NAME,
                language=ln,
                req=req)
