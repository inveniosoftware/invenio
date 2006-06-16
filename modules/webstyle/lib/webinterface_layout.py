# -*- coding: utf-8 -*-
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

"""
Global organisation of the application's URLs.

This module binds together CDS Invenio's modules and maps them to
their corresponding URLs (ie, /search to the websearch modules,...)
"""

from invenio.config import webdir
from invenio.webinterface_handler import create_handler, WebInterfaceDirectory

from invenio.websearch_webinterface import WebInterfaceSearchInterfacePages
from invenio.websubmit_webinterface import websubmit_legacy_getfile, WebInterfaceSubmitPages
from invenio.websession_webinterface import WebInterfaceYourAccountPages
from invenio.webalert_webinterface import WebInterfaceYourAlertsPages
from invenio.webbasket_webinterface import WebInterfaceYourBasketsPages
from invenio.webcomment_webinterface import WebInterfaceCommentsPages
from invenio.webmessage_webinterface import WebInterfaceYourMessagesPages
from invenio.errorlib_webinterface import WebInterfaceErrorPages
from invenio.oai_repository_webinterface import WebInterfaceOAIProviderPages

from invenio.urlutils import redirect_to_url

class WebInterfaceInvenio(WebInterfaceSearchInterfacePages):
    """ The global URL layout is composed of the search API plus all
    the other modules."""
    
    _exports = WebInterfaceSearchInterfacePages._exports + [
        'youraccount',
        'youralerts',
        'yourbaskets',
        'yourmessages',
        'comments',
        'error',
        'oai2d', ('oai2d.py', 'oai2d'),
        ('getfile.py', 'getfile'),
        'submit',
        ]

    def __init__(self):
        self.getfile = websubmit_legacy_getfile
        return

    submit = WebInterfaceSubmitPages()

    youraccount = WebInterfaceYourAccountPages()

    youralerts = WebInterfaceYourAlertsPages()

    yourbaskets = WebInterfaceYourBasketsPages()

    yourmessages = WebInterfaceYourMessagesPages()

    comments = WebInterfaceCommentsPages()

    error = WebInterfaceErrorPages()

    oai2d = WebInterfaceOAIProviderPages()

# This creates the 'handler' function, which will be invoked directly
# by mod_python.
handler = create_handler(WebInterfaceInvenio())
