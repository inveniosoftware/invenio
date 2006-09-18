## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

"""CDS Invenio Web Page Functions"""

__revision__ = "$Id$"

import time

from invenio.config import *
from invenio.messages import gettext_set_language
from invenio.webuser import create_userinfobox_body
from invenio.errorlib import get_msgs_for_code_list, register_errors 

import invenio.template
webstyle_templates = invenio.template.load('webstyle')

def create_navtrailbox_body(title,
                            previous_links,
                            prolog="",
                            separator=""" &gt; """,
                            epilog="",
                            language=cdslang):
    """Create navigation trail box body
       input: title = page title;
              previous_links = the trail content from site title until current page (both ends exlusive).
       output: text containing the navtrail
    """

    return webstyle_templates.tmpl_navtrailbox_body(ln = language,
                                                    title = title,
                                                    previous_links = previous_links,
                                                    separator = separator,
                                                    prolog = prolog,
                                                    epilog = epilog)

def page(title, body, navtrail="", description="", keywords="", uid=0,
         cdspageheaderadd="", cdspageboxlefttopadd="",
         cdspageboxleftbottomadd="", cdspageboxrighttopadd="",
         cdspageboxrightbottomadd="", cdspagefooteradd="", lastupdated="",
         language=cdslang, verbose=1, titleprologue="",
         titleepilogue="", secure_page_p=0, req=None, errors=[], warnings=[]):

    """page(): display CDS web page
        input: title of the page
               body of the page in html format
               description goes to the metadata in the header of the HTML page
               keywords goes to the metadata in the header of the html page
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
       output: the final cds page with header, footer, etc.
    """

    _ = gettext_set_language(language)
    
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
                                        userinfobox = create_userinfobox_body(req, uid, language),
                                        navtrailbox = create_navtrailbox_body(title, navtrail, language=language),                                        
                                        uid = uid,
                                        secure_page_p = secure_page_p,
                                        # pageheader = CFG_WEBSTYLE_CDSPAGEHEADER,
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
                                        # pagefooter = CFG_WEBSTYLE_CDSPAGEFOOTER,
                                        lastupdated = lastupdated,
                                        pagefooteradd = cdspagefooteradd)

def pageheaderonly(title, navtrail="", description="", keywords="", uid=0, cdspageheaderadd="", language=cdslang, req=None, secure_page_p=0, verbose=1):
    """Return just the beginning of page(), with full headers.
       Suitable for the search results page and any long-taking scripts."""

    return webstyle_templates.tmpl_pageheader(req,
                                              ln = language,
                                              headertitle = title,
                                              description = description,
                                              keywords = keywords,                                              
                                              userinfobox = create_userinfobox_body(req, uid, language),
                                              navtrailbox = create_navtrailbox_body(title, navtrail, language=language),
                                              uid = uid,
                                              secure_page_p = secure_page_p,
                                              # pageheader = CFG_WEBSTYLE_CDSPAGEHEADER,
                                              pageheaderadd = cdspageheaderadd)

def pagefooteronly(cdspagefooteradd="", lastupdated="", language=cdslang, req=None, verbose=1):
    """Return just the ending of page(), with full footer.
       Suitable for the search results page and any long-taking scripts."""

    return webstyle_templates.tmpl_pagefooter(req,
                                              ln=language,
                                              lastupdated = lastupdated,
                                              pagefooteradd = cdspagefooteradd)

def create_error_box(req, title=None, verbose=1, ln=cdslang, errors=None):
    """Analyse the req object and the sys traceback and return a text
       message box with internal information that would be suitful to
       display when something bad has happened.
    """
    _ = gettext_set_language(ln)
    return webstyle_templates.tmpl_error_box(title = title,
                                             ln = ln,
                                             verbose = verbose,
                                             req = req,
                                             supportemail = supportemail,
                                             errors = errors)
