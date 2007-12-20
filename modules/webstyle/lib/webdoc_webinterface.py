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
WebDoc web interface, handling URLs such as </help/foo?ln=el>.
"""

__revision__ = \
     "$Id$"

__lastupdated__ = """$Date$"""

import cgi
from invenio.config import weburl, cdslang, cdsname, cdsnameintl
from invenio.messages import gettext_set_language
from invenio.webpage import page
from invenio.webuser import getUid
from invenio.webdoc import get_webdoc_parts, get_webdoc_topics
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory
from invenio.urlutils import redirect_to_url

class WebInterfaceDocumentationPages(WebInterfaceDirectory):
    """Defines the set of documentation pages, usually installed under /help."""

    def __init__(self, webdocname='', categ='help'):
        """Constructor."""
        self.webdocname = webdocname
        self.categ = categ

    def _lookup(self, component, path):
        """This handler parses dynamic URLs (/help/component)."""
        if component in ['admin', 'hacking'] and len(path) == 1:
            if path[0] != '':
                webdocname = path[0]   # /help/hacking/coding-style use
                                       # coding-style.webdoc
            elif component == 'admin':
                webdocname = 'admin'   # /help/admin/ use admin.webdoc
            else:
                webdocname = 'hacking' # /help/hacking/ use
                                       # hacking.webdoc
            return WebInterfaceDocumentationPages(webdocname, component), []
        elif len(path) == 0:
            # Accept any other 'leaf' pages ('help' pages)
            if component == '':
                component = 'help-central'
            return WebInterfaceDocumentationPages(component), []
        else:
            # This is a wrong url eg. /help/help-central/foo
            return None, []

    def __call__(self, req, form):
        """Serve webdoc page in the given language."""
        argd = wash_urlargd(form, {'ln': (str, cdslang)})
        if self.webdocname in ['admin', 'hacking', ''] and \
               self.categ == 'help':
            # Eg. /help/hacking -> /help/hacking/
            #     /help         -> /help/
            redirect_to_url(req, req.uri + "/")
        else:
            return display_webdoc_page(self.webdocname, categ=self.categ, ln=argd['ln'], req=req)

    index = __call__

def display_webdoc_page(webdocname, categ="help", ln=cdslang, req=None):
    """Display webdoc page WEBDOCNAME in language LN."""

    _ = gettext_set_language(ln)

    uid = getUid(req)

    # wash arguments:
    if not webdocname:
        webdocname = 'help-central'

    # get page parts in given language:
    if webdocname != 'topics':
        page_parts = get_webdoc_parts(webdocname, parts=['title','body',
                                                         'navtrail', 'lastupdated',
                                                         'description', 'keywords'],
                                      categ=categ,
                                      ln=ln)
    else:
        page_parts = {'title': _("Help Pages Topics"),
                      'body': '<strong>Last modifications</strong>' + \
                              get_webdoc_topics(sort_by='date', sc=0, limit=5) + \
                              '<br/>' + \
                              get_webdoc_topics(sort_by='name', sc=1),
                      'navtrail': ''
                      }
    # set page title:
    page_title = page_parts.get('title', '')
    if not page_title:
        page_title = _("Page %s Not Found") % cgi.escape(webdocname)

    # set page navtrail:
    page_navtrail = page_parts.get('navtrail', '')

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

    # set page description:
    page_description = page_parts.get('description' , '')

    # set page keywords:
    page_keywords = page_parts.get('keywords' , '')

    # set page last updated timestamp:
    page_last_updated = page_parts.get('lastupdated' , '')

    if categ == 'hacking':
        categ = 'help'

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
                navmenuid=categ)
