# -*- coding: utf-8 -*-
## $Id$

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
Global organisation of the application's URLs.

This module binds together CDS Invenio's modules and maps them to
their corresponding URLs (ie, /search to the websearch modules,...)
"""

__revision__ = \
    "$Id$"

from invenio.webinterface_handler import create_handler

from invenio.websearch_webinterface import WebInterfaceSearchInterfacePages, \
     WebInterfaceAuthorPage, WebInterfaceRSSFeedServicePages
from invenio.websubmit_webinterface import websubmit_legacy_getfile, \
     WebInterfaceSubmitPages
from invenio.websession_webinterface import WebInterfaceYourAccountPages, \
     WebInterfaceYourGroupsPages
from invenio.webalert_webinterface import WebInterfaceYourAlertsPages
from invenio.webbasket_webinterface import WebInterfaceYourBasketsPages
from invenio.webcomment_webinterface import WebInterfaceCommentsPages
from invenio.webmessage_webinterface import WebInterfaceYourMessagesPages
from invenio.errorlib_webinterface import WebInterfaceErrorPages
from invenio.oai_repository_webinterface import WebInterfaceOAIProviderPages
from invenio.webstat_webinterface import WebInterfaceStatsPages

try:
    from invenio.webjournal_webinterface import WebInterfaceJournalPages
except:
    WebInterfaceJournalPages=WebInterfaceErrorPages
from invenio.webdoc_webinterface import WebInterfaceDocumentationPages

class WebInterfaceInvenio(WebInterfaceSearchInterfacePages):
    """ The global URL layout is composed of the search API plus all
    the other modules."""

    _exports = WebInterfaceSearchInterfacePages._exports + WebInterfaceAuthorPage._exports + [
        'youraccount',
        'youralerts',
        'yourbaskets',
        'yourmessages',
        'yourgroups',
        'comments',
        'error',
        'oai2d', ('oai2d.py', 'oai2d'),
        ('getfile.py', 'getfile'),
        'submit',
        'rss',
        'stats',
	'journal',
        'help'
        ]

    def __init__(self):
        self.getfile = websubmit_legacy_getfile
        return

    author = WebInterfaceAuthorPage()

    submit = WebInterfaceSubmitPages()

    youraccount = WebInterfaceYourAccountPages()

    youralerts = WebInterfaceYourAlertsPages()

    yourbaskets = WebInterfaceYourBasketsPages()

    yourmessages = WebInterfaceYourMessagesPages()

    yourgroups = WebInterfaceYourGroupsPages()

    comments = WebInterfaceCommentsPages()

    error = WebInterfaceErrorPages()

    oai2d = WebInterfaceOAIProviderPages()

    rss = WebInterfaceRSSFeedServicePages()

    stats = WebInterfaceStatsPages()

    journal = WebInterfaceJournalPages()

    help = WebInterfaceDocumentationPages()

# This creates the 'handler' function, which will be invoked directly
# by mod_python.
handler = create_handler(WebInterfaceInvenio())
