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

"""Invenio Web Page Functions"""

__revision__ = "$Id$"

from invenio.config import \
     CFG_WEBSTYLE_CDSPAGEBOXLEFTBOTTOM, \
     CFG_WEBSTYLE_CDSPAGEBOXLEFTTOP, \
     CFG_WEBSTYLE_CDSPAGEBOXRIGHTBOTTOM, \
     CFG_WEBSTYLE_CDSPAGEBOXRIGHTTOP, \
     CFG_SITE_LANG, \
     CFG_SITE_URL, \
     CFG_SITE_SECURE_URL
from invenio.access_control_config import CFG_EXTERNAL_AUTH_USING_SSO
from invenio.messages import gettext_set_language
from invenio.webuser import \
     create_userinfobox_body, \
     create_useractivities_menu, \
     create_adminactivities_menu, \
     getUid, \
     isGuestUser
from invenio.errorlib import get_msgs_for_code_list, register_errors

import invenio.template
webstyle_templates = invenio.template.load('webstyle')

from xml.dom.minidom import getDOMImplementation

def create_navtrailbox_body(title,
                            previous_links,
                            prolog="",
                            separator=""" &gt; """,
                            epilog="",
                            language=CFG_SITE_LANG):
    """Create navigation trail box body
       input: title = page title;
              previous_links = the trail content from site title until current page (both ends exclusive).
       output: text containing the navtrail
    """

    return webstyle_templates.tmpl_navtrailbox_body(ln = language,
                                                    title = title,
                                                    previous_links = \
                                                    previous_links,
                                                    separator = separator,
                                                    prolog = prolog,
                                                    epilog = epilog)

def page(title, body, navtrail="", description="", keywords="",
         metaheaderadd="", uid=None,
         cdspageheaderadd="", cdspageboxlefttopadd="",
         cdspageboxleftbottomadd="", cdspageboxrighttopadd="",
         cdspageboxrightbottomadd="", cdspagefooteradd="", lastupdated="",
         language=CFG_SITE_LANG, verbose=1, titleprologue="",
         titleepilogue="", secure_page_p=0, req=None, errors=[], warnings=[], navmenuid="admin",
         navtrail_append_title_p=1, of="", rssurl=CFG_SITE_URL+"/rss", show_title_p=True,
         body_css_classes=None):

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
               errors is the list of error codes as defined in the moduleName_config.py file of the calling module
               log is the string of data that should be appended to the log file (errors automatically logged)
               secure_page_p is 0 or 1 and tells whether we are to use HTTPS friendly page elements or not
               navmenuid the section of the website this page belongs (search, submit, baskets, etc.)
               navtrail_append_title_p is 0 or 1 and tells whether page title is appended to navtrail
               of is an output format (use xx for xml output (e.g. AJAX))
               rssfeed is the url of the RSS feed for this page
               show_title_p is 0 or 1 and tells whether page title should be displayed in body of the page
       output: the final cds page with header, footer, etc.
    """

    _ = gettext_set_language(language)
    if req and uid is None:
        uid = getUid(req)
        if CFG_EXTERNAL_AUTH_USING_SSO and not isGuestUser(uid):
            ## If the user is logged in and we are using SSO
            ## this trick will keep the SSO session alive
            ## (SSO session need an https connection)
            body += """<img src="%s/img/keep_sso_connection_alive.gif"
                    alt=" " width="0" height="0"
                    style="visibility : hidden;" />""" % CFG_SITE_SECURE_URL
    elif uid is None:
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
        if errors:
            errors_node = output.createElement('errors')
            errors = get_msgs_for_code_list(errors, 'error', language)
            register_errors(errors, 'error', req)
            for (error_code, error_msg) in errors:
                error_node = output.createElement('error')
                error_node.setAttribute('code', error_code)
                error_text = output.createTextNode(error_msg)
                error_node.appendChild(error_text)
                errors_node.appendChild(error_node)
            root.appendChild(errors_node)
        if warnings:
            warnings_node = output.createElement('warnings')
            warnings = get_msgs_for_code_list(warnings, 'warning', language)
            register_errors(warnings, 'warning')
            for (warning_code, warning_msg) in warnings:
                warning_node = output.createElement('warning')
                warning_node.setAttribute('code', warning_code)
                warning_text = output.createTextNode(warning_msg)
                warning_node.appendChild(warning_text)
                warnings_node.appendChild(warning_node)
            root.appendChild(warnings_node)
        return output.toprettyxml(encoding="utf-8" )

    else:
        #usual output
        # if there are event
        if warnings:
            warnings = get_msgs_for_code_list(warnings, 'warning', language)
            register_errors(warnings, 'warning')

        # if there are errors
        if errors:
            errors = get_msgs_for_code_list(errors, 'error', language)
            register_errors(errors, 'error', req)
            body = create_error_box(req, errors=errors, ln=language)

        return webstyle_templates.tmpl_page(req, ln=language,
                          description = description,
                          keywords = keywords,
                          metaheaderadd = metaheaderadd,
                          userinfobox = create_userinfobox_body(req, uid, language),
                          useractivities_menu = create_useractivities_menu(req, uid, navmenuid, language),
                          adminactivities_menu = create_adminactivities_menu(req, uid, navmenuid, language),
                          navtrailbox = create_navtrailbox_body(navtrail_append_title_p \
                                                                and title or '',
                                                                navtrail,
                                                                language=language),
                          uid = uid,
                          secure_page_p = secure_page_p,
                          pageheaderadd = cdspageheaderadd,
                          boxlefttop = CFG_WEBSTYLE_CDSPAGEBOXLEFTTOP,
                          boxlefttopadd = cdspageboxlefttopadd,
                          boxleftbottomadd = cdspageboxleftbottomadd,
                          boxleftbottom = CFG_WEBSTYLE_CDSPAGEBOXLEFTBOTTOM,
                          boxrighttop = CFG_WEBSTYLE_CDSPAGEBOXRIGHTTOP,
                          boxrighttopadd = cdspageboxrighttopadd,
                          boxrightbottomadd = cdspageboxrightbottomadd,
                          boxrightbottom = CFG_WEBSTYLE_CDSPAGEBOXRIGHTBOTTOM,
                          titleprologue = titleprologue,
                          title = title,
                          titleepilogue = titleepilogue,
                          body = body,
                          lastupdated = lastupdated,
                          pagefooteradd = cdspagefooteradd,
                          navmenuid = navmenuid,
                          rssurl = rssurl,
                          show_title_p = show_title_p,
                          body_css_classes=body_css_classes)


def pageheaderonly(title, navtrail="", description="", keywords="", uid=0,
                   cdspageheaderadd="", language=CFG_SITE_LANG, req=None,
                   secure_page_p=0, verbose=1, navmenuid="admin",
                   navtrail_append_title_p=1, metaheaderadd="",
                   rssurl=CFG_SITE_URL+"/rss", body_css_classes=None):
    """Return just the beginning of page(), with full headers.
       Suitable for the search results page and any long-taking scripts."""

    return webstyle_templates.tmpl_pageheader(req,
                      ln = language,
                      headertitle = title,
                      description = description,
                      keywords = keywords,
                      metaheaderadd = metaheaderadd,
                      userinfobox = create_userinfobox_body(req, uid, language),
                      useractivities_menu = create_useractivities_menu(req, uid, navmenuid, language),
                      adminactivities_menu = create_adminactivities_menu(req, uid, navmenuid, language),
                      navtrailbox = create_navtrailbox_body(navtrail_append_title_p \
                                                            and title or '',
                                                            navtrail,
                                                            language=language),
                      uid = uid,
                      secure_page_p = secure_page_p,
                      pageheaderadd = cdspageheaderadd,
                      navmenuid = navmenuid,
                      rssurl = rssurl,
                      body_css_classes=body_css_classes)

def pagefooteronly(cdspagefooteradd="", lastupdated="",
                   language=CFG_SITE_LANG, req=None, verbose=1):
    """Return just the ending of page(), with full footer.
       Suitable for the search results page and any long-taking scripts."""

    return webstyle_templates.tmpl_pagefooter(req,
                                              ln=language,
                                              lastupdated = lastupdated,
                                              pagefooteradd = cdspagefooteradd)

def create_error_box(req, title=None, verbose=1, ln=CFG_SITE_LANG, errors=None):
    """Analyse the req object and the sys traceback and return a text
       message box with internal information that would be suitful to
       display when something bad has happened.
    """
    _ = gettext_set_language(ln)
    return webstyle_templates.tmpl_error_box(title = title,
                                             ln = ln,
                                             verbose = verbose,
                                             req = req,
                                             errors = errors)

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

