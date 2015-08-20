# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2014, 2015 CERN.
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

"""Global organisation of the application's URLs.

This module binds together Invenio's legacy modules and maps them to their
corresponding URLs.
"""

from invenio.config import CFG_ACCESS_CONTROL_LEVEL_SITE, CFG_DEVEL_SITE
from invenio.ext.legacy.handler import WebInterfaceDirectory
from invenio.ext.legacy.handler import create_handler
from invenio.ext.logging import register_exception
from invenio.legacy.registry import webinterfaces
from invenio.utils import apache


class WebInterfaceDeprecatedPages(WebInterfaceDirectory):

    """Implement dumb interface for deprecated pages."""

    _exports = ['']

    def __call__(self, req, form):
        """Return deprecation warning."""
        try:
            from invenio.legacy.webpage import page
        except ImportError:
            register_exception()

            def page(*args):
                return args[1]
        req.status = apache.HTTP_SERVICE_UNAVAILABLE
        msg = "<p>This functionality will be soon deprecated.</p>"
        try:
            from invenio.config import CFG_SITE_ADMIN_EMAIL
            msg += """<p>If you would still like to use it, please ask your
                Invenio administrator <code>%s</code> to consider enabling it.
                </p>""" % CFG_SITE_ADMIN_EMAIL
        except ImportError:
            pass
        try:
            return page('Service disabled', msg, req=req)
        except Exception:
            return msg

    def _lookup(self, component, path):
        """Return current interface for given path."""
        return WebInterfaceDeprecatedPages(), path

    index = __call__


class WebInterfaceDisabledPages(WebInterfaceDirectory):

    """This class implements a dumb interface to use as a fallback.

    It is used in case the site is switched to read only mode,
    i.e. CFG_ACCESS_CONTROL_LEVEL_SITE>0.
    """

    _exports = ['']

    def __call__(self, req, form):
        try:
            from invenio.legacy.webpage import page
        except ImportError:
            register_exception()

            def page(*args):
                return args[1]
        req.status = apache.HTTP_SERVICE_UNAVAILABLE
        msg = ("<p>This functionality is currently unavailable due to "
               "a service maintenance.</p>")
        try:
            from invenio.config import CFG_SITE_ADMIN_EMAIL
            msg += ("<p>You can contact <code>%s</code> "
                    "in case of questions.</p>" % CFG_SITE_ADMIN_EMAIL)
        except ImportError:
            pass
        msg += """<p>We are going to restore the service soon.</p>
                  <p>Sorry for the inconvenience.</p>"""
        try:
            return page('Service unavailable', msg, req=req)
        except Exception:
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
            from invenio.legacy.webpage import page
        except ImportError:
            def page(*args):
                return args[1]
        req.status = apache.HTTP_INTERNAL_SERVER_ERROR
        msg = "<p>This functionality is experiencing a temporary failure.</p>"
        msg += "<p>The administrator has been informed about the problem.</p>"
        try:
            from invenio.config import CFG_SITE_ADMIN_EMAIL
            msg += ("<p>You can contact <code>%s</code> "
                    "in case of questions.</p>" % CFG_SITE_ADMIN_EMAIL)
        except ImportError:
            pass
        msg += """<p>We hope to restore the service soon.</p>
                  <p>Sorry for the inconvenience.</p>"""
        try:
            return page('Service failure', msg, req=req)
        except Exception:
            return msg

    def _lookup(self, component, path):
        return WebInterfaceDumbPages(), path
    index = __call__

try:
    from invenio.legacy.bibdocfile.webinterface import \
        bibdocfile_legacy_getfile
except ImportError:
    register_exception(alert_admin=True, subject='EMERGENCY')
    bibdocfile_legacy_getfile = WebInterfaceDumbPages


try:
    from invenio.legacy.bibsched.webinterface import \
        WebInterfaceBibSchedPages
except ImportError:
    register_exception(alert_admin=True, subject='EMERGENCY')
    WebInterfaceBibSchedPages = WebInterfaceDumbPages


class WebInterfaceAdminPages(WebInterfaceDirectory):

    """This class implements /admin2 admin pages."""

    _exports = ['index', 'bibsched']

    def index(self, req, form):
        return "FIXME: return /help/admin content"


    bibsched = WebInterfaceBibSchedPages()


class WebInterfaceInvenio(WebInterfaceDirectory):
    """ The global URL layout is composed of the search API plus all
    the other modules."""

    _exports = [
        'youraccount',
        'yourloans',
        'yourcomments',
        'ill',
        'yourtickets',
        'comments',
        'error',
        'oai2d', ('oai2d.py', 'oai2d'),
        ('getfile.py', 'getfile'),
        'rss',
        'stats',
        'journal',
        'exporter',
        'kb',
        'ping',
        'admin2',
        'textmining',
        'info',
    ]

    def __init__(self):
        self.getfile = bibdocfile_legacy_getfile

    _mapping = dict(
        youraccount='WebInterfaceYourAccountPages',
        yourloans='WebInterfaceYourLoansPages',
        ill='WebInterfaceILLPages',
        yourtickets='WebInterfaceYourTicketsPages',
        comments='WebInterfaceCommentsPages',
        oai2d='WebInterfaceOAIProviderPages',
        rss='WebInterfaceRSSFeedServicePages',
        stats='WebInterfaceStatsPages',
        journal='WebInterfaceJournalPages',
        info='WebInterfaceInfoPages',
        exporter='WebInterfaceFieldExporterPages',
        kb='WebInterfaceBibKnowledgePages',
        admin2='WebInterfaceAdminPages',
        textmining='WebInterfaceDocExtract',
        yourcomments='WebInterfaceYourCommentsPages',
    )

    def __new__(cls):
        from flask import current_app
        if CFG_ACCESS_CONTROL_LEVEL_SITE > 0:
            for key in cls._mapping.keys():
                setattr(cls, key, WebInterfaceDisabledPages())
        else:
            webinterfaces_ = dict(webinterfaces)
            webinterfaces_['WebInterfaceAdminPages'] = WebInterfaceAdminPages
            for key, value in cls._mapping.items():
                if value in webinterfaces_:
                    setattr(cls, key, webinterfaces_[value]())
                else:
                    current_app.logger.error(
                        "Can not load {name}.".format(name=value))
                    setattr(cls, key, WebInterfaceDeprecatedPages())
        return super(WebInterfaceInvenio, cls).__new__(cls)


# This creates the 'handler' function, which will be invoked directly
# by mod_python.
invenio_handler = create_handler(WebInterfaceInvenio())
