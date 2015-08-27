# This file is part of Invenio.
# Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010,
#               2011, 2012, 2015 CERN.
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

"""Invenio Web Page Functions"""

__revision__ = "$Id$"

from invenio.config import \
     CFG_SITE_LANG, \
     CFG_SITE_URL, \
     CFG_SITE_NAME_INTL, \
     CFG_SITE_NAME
from invenio_base.i18n import gettext_set_language
from invenio.legacy.webuser import \
     getUid

from xml.dom.minidom import getDOMImplementation


def page(title, body, navtrail="", description="", keywords="",
         metaheaderadd="", uid=None,
         cdspageheaderadd="", cdspageboxlefttopadd="",
         cdspageboxleftbottomadd="", cdspageboxrighttopadd="",
         cdspageboxrightbottomadd="", cdspagefooteradd="", lastupdated="",
         language=CFG_SITE_LANG, verbose=1, titleprologue="",
         titleepilogue="", secure_page_p=0, req=None, errors=None, warnings=None, navmenuid="admin",
         navtrail_append_title_p=1, of="", rssurl=CFG_SITE_URL+"/rss", show_title_p=True,
         body_css_classes=None, show_header=True, show_footer=True):

    """page(): display CDS web page
        input: title of the page
               body of the page in html format
               description goes to the metadata in the header of the HTML page
               keywords goes to the metadata in the header of the html page
               metaheaderadd goes to further metadata in the header of the html page
               cdspageheaderadd is a message to be displayed just under the page header
               cdspageboxlefttopadd is a message to be displayed in the page body on left top
               cdspageboxleftbottomadd is a message to be displayed in the page body on left bottom
               cdspageboxrighttopadd is a message to be displayed in the page body on right top
               cdspageboxrightbottomadd is a message to be displayed in the page body on right bottom
               cdspagefooteradd is a message to be displayed on the top of the page footer
               lastupdated is a text containing the info on last update (optional)
               language is the language version of the page
               verbose is verbosity of the page (useful for debugging)
               titleprologue is to be printed right before page title
               titleepilogue is to be printed right after page title
               req is the mod_python request object
               log is the string of data that should be appended to the log file (errors automatically logged)
               secure_page_p is 0 or 1 and tells whether we are to use HTTPS friendly page elements or not
               navmenuid the section of the website this page belongs (search, submit, baskets, etc.)
               navtrail_append_title_p is 0 or 1 and tells whether page title is appended to navtrail
               of is an output format (use xx for xml output (e.g. AJAX))
               rssfeed is the url of the RSS feed for this page
               show_title_p is 0 or 1 and tells whether page title should be displayed in body of the page
               show_header is 0 or 1 and tells whether page header should be displayed or not
               show_footer is 0 or 1 and tells whether page footer should be displayed or not
       output: the final cds page with header, footer, etc.
    """

    if req is not None:
        if uid is None:
            uid = getUid(req)
        secure_page_p = req.is_https() and 1 or 0
    if uid is None:
        ## 0 means generic guest user.
        uid = 0
    if of == 'xx':
        #xml output (e.g. AJAX calls) => of=xx
        req.content_type = 'text/xml'
        impl = getDOMImplementation()
        output = impl.createDocument(None, "invenio-message", None)
        root = output.documentElement
        body_node = output.createElement('body')
        body_text = output.createCDATASection(unicode(body, 'utf_8'))
        body_node.appendChild(body_text)
        root.appendChild(body_node)
        return output.toprettyxml(encoding="utf-8" )


def adderrorbox(header='', datalist=[]):
    """used to create table around main data on a page, row based"""

    try:
        perc = str(100 // len(datalist)) + '%'
    except ZeroDivisionError:
        perc = 1

    output  = '<table class="errorbox">'
    output += '<thead><tr><th class="errorboxheader" colspan="%s">%s</th></tr></thead>' % (len(datalist), header)
    output += '<tbody>'
    for row in [datalist]:
        output += '<tr>'
        for data in row:
            output += '<td style="vertical-align: top; margin-top: 5px; width: %s;">' % (perc, )
            output += data
            output += '</td>'
        output += '</tr>'
    output += '</tbody></table>'
    return output

def warning_page(title, req, ln=CFG_SITE_LANG):
    # load the right message language
    _ = gettext_set_language(ln)

    site_name = CFG_SITE_NAME_INTL.get(ln, CFG_SITE_NAME)

    return page(title = _("Warning"),
                body = title,
                description="%s - Internal Error" % site_name,
                keywords="%s, Internal Error" % site_name,
                uid = getUid(req),
                language=ln,
                req=req)
