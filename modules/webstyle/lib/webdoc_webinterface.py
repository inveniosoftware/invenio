## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

"""
WebDoc web interface, handling URLs such as </doc/foo?ln=el>.
"""

__revision__ = \
     "$Id$"

__lastupdated__ = """$Date$"""

import cgi
from invenio.config import weburl, cdslang, cdsname, cdsnameintl
from invenio.messages import gettext_set_language
from invenio.webpage import page
from invenio.webuser import getUid
from invenio.webdoc import get_webdoc_parts
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory

class WebInterfaceDocumentationPages(WebInterfaceDirectory):
    """Defines the set of /doc pages."""

    def __init__(self, webdocname='search-help'):
        """Constructor."""
        self.webdocname = webdocname

    def _lookup(self, component, path):
        """This handler parses dynamic URLs (/doc/component)."""
        return WebInterfaceDocumentationPages(component), path

    def __call__(self, req, form):
        """Serve webdoc page in the given language."""
        argd = wash_urlargd(form, {'ln': (str, cdslang)})
        return display_webdoc_page(self.webdocname, ln=argd['ln'], req=req)

    index = __call__

def display_webdoc_page(webdocname, ln=cdslang, req=None):
    """Display webdoc page WEBDOCNAME in language LN."""

    _ = gettext_set_language(ln)

    uid = getUid(req)

    # wash arguments:
    if not webdocname:
        webdocname = 'search-help'

    # get page parts in given language:
    page_parts = get_webdoc_parts(webdocname, parts=['title','body',
                                                     'navtrail-previous-links'],
                                  ln=ln)

    # set page title:
    page_title = page_parts.get('title', '')
    if not page_title:
        page_title = _("Page %s Not Found") % cgi.escape(webdocname)

    # set page navtrail:
    page_navtrail = page_parts.get('navtrail-previous-links', '')

    # set page body:
    page_body = page_parts.get('body' , '')
    if not page_body:
        page_body = '<p>' + (_("Sorry, page %s does not seem to exist.") % \
                    ('<strong>' + cgi.escape(webdocname) + '</strong>')) + \
                    '</p>'
        page_body += '<p>' + (_("You may want to start browsing from %s.") % \
                                ('<a href="' + weburl + '?ln=' + ln + '">' + \
                                   cdsnameintl.get(ln, cdsname) + '</a>')) + \
                     '</p>'

    # FIXME:
    page_description = "FIXME: description"
    page_keywords = "FIXME: keywords"
    page_last_updated = "FIXME: last updated"
    page_navmenuid = "FIXME: navmenuid"

    # display page:
    return page(title=page_title,
                body=page_body,
                navtrail=page_navtrail,
                description=page_description,
                keywords=page_keywords,
                uid=uid,
                language=ln,
                req=req,
                lastupdated=page_last_updated,
                navmenuid=page_navmenuid)
