# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2009, 2010, 2011 CERN.
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

"""
WebDoc web interface, handling URLs such as </help/foo?ln=el>.
"""

__revision__ = \
     "$Id$"

__lastupdated__ = """$Date$"""

import cgi

from six import iteritems

from invenio.config import CFG_SITE_URL, CFG_SITE_LANG, CFG_SITE_LANGS
from invenio.base.i18n import gettext_set_language
from invenio.legacy.webpage import page
from invenio.legacy.webuser import getUid
from invenio.legacy.webdoc.api import get_webdoc_parts, get_webdoc_topics
from invenio.ext.legacy.handler import wash_urlargd, WebInterfaceDirectory
from invenio.utils.url import redirect_to_url

class WebInterfaceDocumentationPages(WebInterfaceDirectory):
    """Defines the set of documentation pages, usually installed under /help."""

    def __init__(self, webdocname='', categ='help'):
        """Constructor."""
        self.webdocname = webdocname
        self.categ = categ
        self.legacy_urls_mappings = {'tips': 'search-tips',
                                     'guide': 'search-guide',
                                     'submit': 'submit-guide',
                                     'index': '',
                                     '': ''}

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
        elif len(path) == 0 and \
                 component != 'search' and \
                 component != 'submit':
            # Accept any other 'leaf' pages ('help' pages),
            # excepted /help/search/ and /help/submit/ which are legacy urls
            if component == '':
                component = 'help-central'
            return WebInterfaceDocumentationPages(component), []
        else:
            # This is maybe a wrong url eg. /help/help-central/foo
            # or a legacy url eg. /help/search/tips.en.html
            #                     /help/search/
            if ((component == 'submit' or \
                   component == 'search') and (len(path) == 0 or path[0] == '')) or \
                   path[0].endswith('.html'):
                # Legacy url?
                return WebInterfaceDocumentationPages(), []
            # Wrong url
            return None, []

    def __call__(self, req, form):
        """Serve webdoc page in the given language."""
        argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG)})
        if self.webdocname in ['admin', 'hacking', ''] and \
               self.categ == 'help' and \
               not (req.uri.endswith('.html') or \
                    req.uri.endswith('/help/search/') or \
                    req.uri.endswith('/help/submit/')):
            # Eg. /help/hacking -> /help/hacking/
            #     /help         -> /help/
            ln_link = (argd['ln'] != CFG_SITE_LANG and '?ln=' + argd['ln']) or ''
            redirect_to_url(req, req.uri + "/" + ln_link)
        elif req.uri.endswith('.html') or \
                 req.uri.endswith('/help/search/') or \
                 req.uri.endswith('/help/submit/'):
            # Legacy urls
            path = req.uri.split('/')
            parts = path[-1].split('.')
            title = parts[0]
            ln = CFG_SITE_LANG
            if len(parts) > 1 and parts[1] in CFG_SITE_LANGS:
                ln = parts[1]
            category = path[-2]
            webdocname = self.legacy_urls_mappings.get(title, '')
            if category == 'submit':
                webdocname = 'submit-guide'
                category = ''
            elif category == 'help' or category == 'search':
                category = ''
            if category != '':
                category += '/'

            url = CFG_SITE_URL + '/help/' + category  + webdocname
            ln_link = (ln != CFG_SITE_LANG and '?ln=' + ln) or ''
            redirect_to_url(req, url + ln_link)
        else:
            return display_webdoc_page(self.webdocname, categ=self.categ, ln=argd['ln'], req=req)

    index = __call__

def display_webdoc_page(webdocname, categ="help", ln=CFG_SITE_LANG, req=None):
    """Display webdoc page WEBDOCNAME in language LN."""

    _ = gettext_set_language(ln)

    uid = getUid(req)

    # wash arguments:
    if not webdocname:
        webdocname = 'help-central'

    ln_link = (ln != CFG_SITE_LANG and '?ln=' + ln) or ''

    # get page parts in given language:
    if webdocname != 'contents':
        page_parts = get_webdoc_parts(webdocname, parts=['title', 'body',
                                                         'navtrail', 'lastupdated',
                                                         'description', 'keywords'],
                                      categ=categ,
                                      ln=ln)
    else:
        # Print Table of Contents
        see_also_links = {'admin': '<a href="%s/help/admin/contents%s">%s</a>' % \
                          (CFG_SITE_URL, ln_link, _('Admin Pages')),
                          'help':'<a href="%s/help/contents%s">%s</a>' % \
                          (CFG_SITE_URL, ln_link, _('Help Pages')),
                          'hacking':'<a href="%s/help/hacking/contents%s">%s</a>' % \
                          (CFG_SITE_URL, ln_link, _('Hacking Pages'))}
        titles = {'admin': _("Admin Pages"),
                  'help': _("Help Pages"),
                  'hacking': _("Hacking Pages")}
        navtrails = {'admin': '<a class="navtrail" href="/help/admin%s">%s</a>' % \
                     (ln_link, _("Admin Area")),
                     'help': '<a class="navtrail" href="/help/%s">%s</a>' % \
                     (ln_link, _("Help Central")),
                     'hacking': '<a class="navtrail" href="/help/hacking%s">%s</a>' % \
                     (ln_link, _("Hacking Invenio"))}
        body = '<div class="container" ><div class="row">' + \
               '<div  class="col-md-8"><h5>' + \
              _('Table of contents of the %(x_category)s pages.',
                x_category=_(categ))
        if categ != 'help':
            body += ' <small>' + _('See also') + ' ' + \
                              ', '.join([ link for (category, link) in \
                                          iteritems(see_also_links) \
                                          if category != categ]) + '.</small>'

        body += '</h5>' + get_webdoc_topics(sort_by='name', sc=1,
                                          categ=[categ], ln=ln) + \
                '</div><div  class="col-md-4">' + \
                '<h5>'+_("Latest modifications:") + '</h5>' + \
                get_webdoc_topics(sort_by='date', sc=0, limit=5,
                                  categ=[categ], ln=ln)+'</div></div></div>'
        page_parts = {'title': titles.get(categ, ''),
                      'body': body,
                      'navtrail': navtrails.get(categ, '')
                      }

    # set page title:
    page_title = page_parts.get('title', '')
    if not page_title:
        page_title = _("Page %(page)s Not Found", page=cgi.escape(webdocname))

    # set page navtrail:
    page_navtrail = page_parts.get('navtrail', '')

    # set page body:
    page_body = page_parts.get('body' , '')
    if not page_body:
        page_body = '<p>' + \
                    _("Sorry, page %(page)s does not seem to exist.",
                      page='<strong>' + cgi.escape(webdocname) + '</strong>') + \
                    '</p>'
        page_body += '<p>' + \
                     _("You may want to look at the %(x_url_open)s%(x_category)s pages%(x_url_close)s.",
                       x_category=_(categ),
                       x_url_open='<a href="%s/help/%scontents%s">' % (CFG_SITE_URL, ((categ != 'help' and categ + '/') or ''), ln_link),
                       x_url_close='</a>') + \
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
                navmenuid=categ)
