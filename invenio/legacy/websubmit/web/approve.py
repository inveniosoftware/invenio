# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012 CERN.
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
import urllib

from invenio.config import \
     CFG_ACCESS_CONTROL_LEVEL_SITE, \
     CFG_SITE_LANG, \
     CFG_SITE_NAME, \
     CFG_SITE_SECURE_URL, \
     CFG_SITE_SECURE_URL
from invenio.legacy.websubmit.db_layer import get_approval_url_parameters
from invenio.legacy.webpage import warning_page
from invenio.legacy.webuser import getUid, page_not_authorized
from invenio.base.i18n import wash_language, gettext_set_language
from invenio.utils.url import redirect_to_url
from invenio.ext.legacy.handler import wash_urlargd
from invenio.modules.access.engine import acc_authorize_action

def index(req, c=CFG_SITE_NAME, ln=CFG_SITE_LANG):
    """Approval web Interface.
    GET params:

    """
    uid = getUid(req)
    (auth_code, auth_message) = acc_authorize_action(uid, 'submit')
    if auth_code > 0 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
        return page_not_authorized(req, "../approve.py/index",
                                   navmenuid='yourapprovals',
                                   text=auth_message)

    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    args = wash_urlargd(req.form, {'access': (str, '')})
    if args['access'] == "":
        return warning_page(_("approve.py: cannot determine document reference"), req, ln)
    url_params = get_approval_url_parameters(args['access'])
    if not url_params:
        return warning_page(_("approve.py: cannot find document in database"), req, ln)
    url_params['ln'] = ln
    url = "%s/submit/direct?%s" % (CFG_SITE_SECURE_URL, urllib.urlencode(url_params))
    redirect_to_url(req, url)
