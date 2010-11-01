## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
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

__revision__ = "$Id$"

## import interesting modules:
import urllib

from invenio.config import \
     CFG_ACCESS_CONTROL_LEVEL_SITE, \
     CFG_SITE_LANG, \
     CFG_SITE_NAME, \
     CFG_SITE_URL, \
     CFG_SITE_NAME_INTL
from invenio.dbquery import run_sql
from invenio.websubmit_config import *
from invenio.webpage import page
from invenio.webuser import getUid, page_not_authorized
from invenio.messages import wash_language, gettext_set_language
from invenio.urlutils import redirect_to_url

def index(req, c=CFG_SITE_NAME, ln=CFG_SITE_LANG):
    """Approval web Interface.
    GET params:

    """
    uid = getUid(req)
    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
        return page_not_authorized(req, "../approve.py/index",
                                   navmenuid='yourapprovals')

    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    form = req.form
    if form.keys():
        # form keys can be a list of 'access pw' and ln, so remove 'ln':
        for key in form.keys():
            if key != 'ln':
                access = key
        if access == "":
            return warningMsg(_("approve.py: cannot determine document reference"), req)
        res = run_sql("select doctype,rn from sbmAPPROVAL where access=%s",(access,))
        if len(res) == 0:
            return warningMsg(_("approve.py: cannot find document in database"), req)
        else:
            doctype = res[0][0]
            rn = res[0][1]
        res = run_sql("select value from sbmPARAMETERS where name='edsrn' and doctype=%s",(doctype,))
        edsrn = res[0][0]
        url = "%s/submit/direct?%s" % (CFG_SITE_URL, urllib.urlencode({
            edsrn: rn,
            'access' : access,
            'sub' : 'APP%s' % doctype,
            'ln' : ln
        }))
        redirect_to_url(req, url)
    else:
        return warningMsg(_("Sorry parameter missing..."), req, c, ln)

def warningMsg(title, req, c=None, ln=CFG_SITE_LANG):
    # load the right message language
    _ = gettext_set_language(ln)

    if c is None:
        c = CFG_SITE_NAME_INTL.get(ln, CFG_SITE_NAME)

    return page(title = _("Warning"),
                body = title,
                description="%s - Internal Error" % c,
                keywords="%s, Internal Error" % c,
                uid = getUid(req),
                language=ln,
                req=req,
                navmenuid='submit')

