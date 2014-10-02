# -*- coding: utf-8 -*-

## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2012 CERN.
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

"""
Global organisation of the application's URLs.

This module binds together Invenio's modules and maps them to
their corresponding URLs (ie, /search to the websearch modules,...)
"""

from invenio.webinterface_handler import create_handler
from invenio.errorlib import register_exception
from invenio.webinterface_handler import WebInterfaceDirectory
from invenio import webinterface_handler_config as apache
from invenio.config import CFG_DEVEL_SITE, CFG_OPENAIRE_SITE, CFG_ACCESS_CONTROL_LEVEL_SITE


class WebInterfaceDisabledPages(WebInterfaceDirectory):
    """This class implements a dumb interface to use as a fallback in case the
    site is switched to read only mode, i.e. CFG_ACCESS_CONTROL_LEVEL_SITE > 0"""
    _exports = ['']
    def __call__(self, req, form):
        try:
            from invenio.webpage import page
        except ImportError:
            register_exception()
            page = lambda * args: args[1]
        req.status = apache.HTTP_SERVICE_UNAVAILABLE
        msg = "<p>We are currently updating our author pages. Please come back tomorrow to enjoy them in their new design. Thanks for your patience!</p>"
        try:
            from invenio.config import CFG_SITE_ADMIN_EMAIL
            msg += """<p>You can contact <code>%s</code>
                         in case of questions.</p>""" % \
                      CFG_SITE_ADMIN_EMAIL
        except ImportError:
            pass
        msg += """<p>We are going to restore the service soon.</p>
                  <p>Sorry for the inconvenience.</p>"""
        try:
            return page('Service unavailable', msg, req=req)
        except:
            return msg

    def _lookup(self, component, path):
        return WebInterfaceDisabledPages(), path
    index = __call__

class WebInterfaceDumbPages(WebInterfaceDirectory):
    """This class implements a dumb interface to use as a fallback in case of
    errors importing particular module pages."""
    _exports = ['']
    def __call__(self, req, form):
        try:
            from invenio.webpage import page
        except ImportError:
            page = lambda * args: args[1]
        req.status = apache.HTTP_INTERNAL_SERVER_ERROR
        msg = "<p>This functionality is experiencing a temporary failure.</p>"
        msg += "<p>The administrator has been informed about the problem.</p>"
        try:
            from invenio.config import CFG_SITE_ADMIN_EMAIL
            msg += """<p>You can contact <code>%s</code>
                         in case of questions.</p>""" % \
                      CFG_SITE_ADMIN_EMAIL
        except ImportError:
            pass
        msg += """<p>We hope to restore the service soon.</p>
                  <p>Sorry for the inconvenience.</p>"""
        try:
            return page('Service failure', msg, req=req)
        except:
            return msg

    def _lookup(self, component, path):
        return WebInterfaceDumbPages(), path
    index = __call__

try:
    from invenio.websearch_webinterface import WebInterfaceSearchInterfacePages
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceSearchInterfacePages = WebInterfaceDumbPages

try:
    from invenio.websearch_webinterface import WebInterfaceRSSFeedServicePages
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceRSSFeedServicePages = WebInterfaceDumbPages

try:
    from invenio.websearch_webinterface import WebInterfaceUnAPIPages
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceUnAPIPages = WebInterfaceDumbPages

try:
    from invenio.bibdocfile_webinterface import bibdocfile_legacy_getfile
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    bibdocfile_legacy_getfile = WebInterfaceDumbPages

try:
    from invenio.websubmit_webinterface import WebInterfaceSubmitPages
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceSubmitPages = WebInterfaceDumbPages

try:
    from invenio.websession_webinterface import WebInterfaceYourAccountPages
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceYourAccountPages = WebInterfaceDumbPages

try:
    from invenio.websession_webinterface import WebInterfaceYourTicketsPages
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceYourTicketsPages = WebInterfaceDumbPages

try:
    from invenio.websession_webinterface import WebInterfaceYourGroupsPages
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceYourGroupsPages = WebInterfaceDumbPages

try:
    from invenio.webalert_webinterface import WebInterfaceYourAlertsPages
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceYourAlertsPages = WebInterfaceDumbPages

try:
    from invenio.webbasket_webinterface import WebInterfaceYourBasketsPages
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceYourBasketsPages = WebInterfaceDumbPages

try:
    from invenio.webcomment_webinterface import WebInterfaceCommentsPages
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceCommentsPages = WebInterfaceDumbPages

try:
    from invenio.weblinkback_webinterface import WebInterfaceRecentLinkbacksPages
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceRecentLinkbacksPages = WebInterfaceDumbPages

try:
    from invenio.webmessage_webinterface import WebInterfaceYourMessagesPages
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceYourMessagesPages = WebInterfaceDumbPages

try:
    from invenio.errorlib_webinterface import WebInterfaceErrorPages
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceErrorPages = WebInterfaceDumbPages

try:
    from invenio.oai_repository_webinterface import WebInterfaceOAIProviderPages
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceOAIProviderPages = WebInterfaceDumbPages

try:
    from invenio.webstat_webinterface import WebInterfaceStatsPages
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceStatsPages = WebInterfaceDumbPages
try:
    from invenio.bibcirculation_webinterface import WebInterfaceYourLoansPages
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceYourLoansPages = WebInterfaceDumbPages

try:
    from invenio.bibcirculation_webinterface import WebInterfaceILLPages
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceILLPages = WebInterfaceDumbPages

try:
    from invenio.webjournal_webinterface import WebInterfaceJournalPages
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceJournalPages = WebInterfaceDumbPages

try:
    from invenio.webdoc_webinterface import WebInterfaceDocumentationPages
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceDocumentationPages = WebInterfaceDumbPages

try:
    from invenio.webdoc_info_webinterface import WebInterfaceInfoPages
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceInfoPages = WebInterfaceDumbPages


try:
    from invenio.bibexport_method_fieldexporter_webinterface import \
         WebInterfaceFieldExporterPages
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceFieldExporterPages = WebInterfaceDumbPages

try:
    from invenio.bibknowledge_webinterface import WebInterfaceBibKnowledgePages
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceBibKnowledgePages = WebInterfaceDumbPages

try:
    from invenio.batchuploader_webinterface import \
         WebInterfaceBatchUploaderPages
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceBatchUploaderPages = WebInterfaceDumbPages

try:
    from invenio.bibsword_webinterface import \
         WebInterfaceSword
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceSword = WebInterfaceDumbPages

try:
    from invenio.ping_webinterface import \
         WebInterfacePingPages
except:
    register_exception(alert_admin=True, subject='EMERGENCE')
    WebInterfacePingPages = WebInterfaceDumbPages

try:
    from invenio.bibauthorid_webinterface import WebInterfaceAuthor
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceAuthor = WebInterfaceDumbPages

try:
    from invenio.bibauthorid_webinterface import WebInterfacePerson
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfacePerson = WebInterfaceDumbPages

try:
    from invenio.bibcirculationadmin_webinterface import \
         WebInterfaceBibCirculationAdminPages
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceBibCirculationAdminPages = WebInterfaceDumbPages

try:
    from invenio.bibsched_webinterface import \
         WebInterfaceBibSchedPages
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceBibSchedPages = WebInterfaceDumbPages

try:
    from invenio.docextract_webinterface import WebInterfaceDocExtract
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceDocExtract = WebInterfaceDumbPages

try:
    from invenio.webcomment_webinterface import WebInterfaceYourCommentsPages
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceYourCommentsPages = WebInterfaceDumbPages

try:
    from invenio.goto_webinterface import WebInterfaceGotoPages
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceGotoPages = WebInterfaceDumbPages

try:
    from invenio.authorlist_webinterface import WebInterfaceAuthorlistPages
except:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceAuthorlistPages = WebInterfaceDumbPages

if CFG_OPENAIRE_SITE:
    try:
        from invenio.openaire_deposit_webinterface import \
            WebInterfaceOpenAIREDepositPages
    except:
        register_exception(alert_admin=True, subject='EMERGENCY')
        WebInterfaceOpenAIREDepositPages = WebInterfaceDumbPages
    openaire_exports = ['deposit']
else:
    openaire_exports = []

if CFG_DEVEL_SITE:
    try:
        from invenio.httptest_webinterface import WebInterfaceHTTPTestPages
    except:
        register_exception(alert_admin=True, subject='EMERGENCY')
        WebInterfaceHTTPTestPages = WebInterfaceDumbPages
    test_exports = ['httptest']
else:
    test_exports = []

class WebInterfaceAdminPages(WebInterfaceDirectory):
    """This class implements /admin2 admin pages."""
    _exports = ['index', 'bibcirculation', 'bibsched']
    def index(self, req, form):
        return "FIXME: return /help/admin content"
    bibcirculation = WebInterfaceBibCirculationAdminPages()

    bibsched = WebInterfaceBibSchedPages()

class WebInterfaceInvenio(WebInterfaceSearchInterfacePages):
    """ The global URL layout is composed of the search API plus all
    the other modules."""

    _exports = WebInterfaceSearchInterfacePages._exports + \
               [
                   'youraccount',
                   'youralerts',
                   'yourbaskets',
                   'yourmessages',
                   'yourloans',
                   'yourcomments',
                   'ill',
                   'yourgroups',
                   'yourtickets',
                   'comments',
                   'error',
                   'oai2d', ('oai2d.py', 'oai2d'),
                   ('getfile.py', 'getfile'),
                   'submit',
                   'rss',
                   'stats',
                   'journal',
                   'help',
                   'unapi',
                   'exporter',
                   'kb',
                   'batchuploader',
                   'bibsword',
                   'ping',
                   'admin2',
                   'linkbacks',
                   'author',
                   'person',
                   'textmining',
                   'goto',
                   'info',
                   'authorlist',
               ] + test_exports + openaire_exports

    def __init__(self):
        self.getfile = bibdocfile_legacy_getfile
        if CFG_DEVEL_SITE:
            self.httptest = WebInterfaceHTTPTestPages()
        if CFG_OPENAIRE_SITE:
            self.deposit = WebInterfaceOpenAIREDepositPages()

    if CFG_ACCESS_CONTROL_LEVEL_SITE > 0:
        submit = WebInterfaceDisabledPages()
        youraccount = WebInterfaceDisabledPages()
        youralerts = WebInterfaceDisabledPages()
        yourbaskets = WebInterfaceDisabledPages()
        yourmessages = WebInterfaceDisabledPages()
        yourloans = WebInterfaceDisabledPages()
        ill = WebInterfaceDisabledPages()
        yourgroups = WebInterfaceDisabledPages()
        yourtickets = WebInterfaceDisabledPages()
        comments = WebInterfaceDisabledPages()
        error = WebInterfaceErrorPages()
        oai2d = WebInterfaceDisabledPages()
        rss = WebInterfaceRSSFeedServicePages()
        stats = WebInterfaceDisabledPages()
        journal = WebInterfaceDisabledPages()
        help = WebInterfaceDocumentationPages()
        info = WebInterfaceInfoPages()
        unapi = WebInterfaceUnAPIPages()
        exporter = WebInterfaceDisabledPages()
        kb = WebInterfaceBibKnowledgePages()
        admin2 = WebInterfaceDisabledPages()
        batchuploader = WebInterfaceDisabledPages()
        bibsword = WebInterfaceDisabledPages()
        ping = WebInterfacePingPages()
        linkbacks = WebInterfaceDisabledPages()
        author = WebInterfaceDisabledPages()
        person = WebInterfaceDisabledPages()
        textmining = WebInterfaceDocExtract()
        yourcomments = WebInterfaceDisabledPages()
        goto = WebInterfaceDisabledPages()
        authorlist = WebInterfaceDisabledPages()
    else:
        submit = WebInterfaceSubmitPages()
        youraccount = WebInterfaceYourAccountPages()
        youralerts = WebInterfaceYourAlertsPages()
        yourbaskets = WebInterfaceYourBasketsPages()
        yourmessages = WebInterfaceYourMessagesPages()
        yourloans = WebInterfaceYourLoansPages()
        ill = WebInterfaceILLPages()
        yourgroups = WebInterfaceYourGroupsPages()
        yourtickets = WebInterfaceYourTicketsPages()
        comments = WebInterfaceCommentsPages()
        error = WebInterfaceErrorPages()
        oai2d = WebInterfaceOAIProviderPages()
        rss = WebInterfaceRSSFeedServicePages()
        stats = WebInterfaceStatsPages()
        journal = WebInterfaceJournalPages()
        help = WebInterfaceDocumentationPages()
        info = WebInterfaceInfoPages()
        unapi = WebInterfaceUnAPIPages()
        exporter = WebInterfaceFieldExporterPages()
        kb = WebInterfaceBibKnowledgePages()
        admin2 = WebInterfaceAdminPages()
        batchuploader = WebInterfaceBatchUploaderPages()
        bibsword = WebInterfaceSword()
        ping = WebInterfacePingPages()
        linkbacks = WebInterfaceRecentLinkbacksPages()
        author = WebInterfaceDisabledPages() #WebInterfaceAuthor()
        person = WebInterfaceDisabledPages() #WebInterfacePerson()
        textmining = WebInterfaceDocExtract()
        yourcomments = WebInterfaceYourCommentsPages()
        goto = WebInterfaceGotoPages()
        authorlist = WebInterfaceAuthorlistPages()


# This creates the 'handler' function, which will be invoked directly
# by mod_python.
invenio_handler = create_handler(WebInterfaceInvenio())
