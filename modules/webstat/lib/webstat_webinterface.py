## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
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

__revision__ = "$Id$"
__lastupdated__ = "$Date$"

import os

from invenio.config import CFG_TMPDIR, CFG_SITE_URL, CFG_SITE_NAME
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory
from invenio.webpage import page
from invenio import template

from invenio.webstat import perform_request_index
from invenio.webstat import perform_display_keyevent
from invenio.webstat import perform_display_customevent
from invenio.webstat import perform_display_customevent_help

def detect_suitable_graph_format():
    """
    Return suitable graph format default argument: gnuplot if it is
    present, otherwise asciiart.
    """
    try:
        import Gnuplot
        suitable_graph_format = "gnuplot"
    except ImportError:
        suitable_graph_format = "asciiart"
    return suitable_graph_format

SUITABLE_GRAPH_FORMAT = detect_suitable_graph_format()

class WebInterfaceStatsPages(WebInterfaceDirectory):
    """Defines the set of stats pages."""

    _exports = [ '',
                 'collection_population', 'search_frequency', 'search_type_distribution',
                 'download_frequency', 'customevent', 'customevent_help',
                 'export' ]

    def index(self, req, _):
        """Index page."""
        return page(title="Statistics",
                    body=perform_request_index(),
                    description="CDS, Statistics",
                    keywords="CDS, statistics",
                    req=req,
                    lastupdated=__lastupdated__,
                    navmenuid='stats')

    # KEY EVENT SECTION

    def collection_population(self, req, form):
        """Collection population statistics page."""
        argd = wash_urlargd(form, {'collection': (str, CFG_SITE_NAME),
                                   'timespan': (str, "today"),
                                   'format': (str, SUITABLE_GRAPH_FORMAT)})

        return page(title="Collection population",
                    body=perform_display_keyevent('collection population', argd, req),
                    navtrail="""<a class="navtrail" href="%s/stats">Statistics</a>""" % CFG_SITE_URL,
                    description="CDS, Statistics, Collection population",
                    keywords="CDS, statistics, collection population",
                    req=req,
                    lastupdated=__lastupdated__,
                    navmenuid='collection population')

    def search_frequency(self, req, form):
        """Search frequency statistics page."""
        argd = wash_urlargd(form, {'timespan': (str, "today"),
                                   'format': (str, SUITABLE_GRAPH_FORMAT)})

        return page(title="Search frequency",
                    body=perform_display_keyevent('search frequency', argd, req),
                    navtrail="""<a class="navtrail" href="%s/stats">Statistics</a>""" % CFG_SITE_URL,
                    description="CDS, Statistics, Search frequency",
                    keywords="CDS, statistics, search frequency",
                    req=req,
                    lastupdated=__lastupdated__,
                    navmenuid='search frequency')

    def search_type_distribution(self, req, form):
        """Search type distribution statistics page."""
        argd = wash_urlargd(form, {'timespan': (str, "today"),
                                   'format': (str, SUITABLE_GRAPH_FORMAT)})

        return page(title="Search type distribution",
                    body=perform_display_keyevent('search type distribution', argd, req),
                    navtrail="""<a class="navtrail" href="%s/stats">Statistics</a>""" % CFG_SITE_URL,
                    description="CDS, Statistics, Search type distribution",
                    keywords="CDS, statistics, search type distribution",
                    req=req,
                    lastupdated=__lastupdated__,
                    navmenuid='search type distribution')

    def download_frequency(self, req, form):
        """Download frequency statistics page."""
        argd = wash_urlargd(form, {'timespan': (str, "today"),
                                   'format': (str, SUITABLE_GRAPH_FORMAT)})

        return page(title="Download frequency",
                    body=perform_display_keyevent('download frequency', argd, req),
                    navtrail="""<a class="navtrail" href="%s/stats">Statistics</a>""" % CFG_SITE_URL,
                    description="CDS, Statistics, Download frequency",
                    keywords="CDS, statistics, download frequency",
                    req=req,
                    lastupdated=__lastupdated__,
                    navmenuid='download frequency')

    # CUSTOM EVENT SECTION

    def customevent(self, req, form):
        """Custom event statistics page"""
        argd = wash_urlargd(form, {'ids': (list, []),
                                   'timespan': (str, ""),
                                   'format': (str, SUITABLE_GRAPH_FORMAT)})

        return page(title="Custom event",
                    body=perform_display_customevent(argd['ids'], argd, req=req),
                    navtrail="""<a class="navtrail" href="%s/stats">Statistics</a>""" % CFG_SITE_URL,
                    description="CDS Personalize, Statistics, Custom event",
                    keywords="CDS, statistics, custom event",
                    req=req,
                    lastupdated=__lastupdated__,
                    navmenuid='custom event')

    def customevent_help(self, req, form):
        """Custom event help page"""
        return page(title="Custom event help",
                    body=perform_display_customevent_help(),
                    navtrail="""<a class="navtrail" href="%s/stats">Statistics</a>""" % CFG_SITE_URL,
                    description="CDS Personalize, Statistics, Custom event help",
                    keywords="CDS, statistics, custom event help",
                    req=req,
                    lastupdated=__lastupdated__,
                    navmenuid='custom event help')

    # EXPORT SECTION

    def export(self, req, form):
        """Exports data"""
        argd = wash_urlargd(form, {"filename": (str, ""),
                                   "mime": (str, "")})

        # Check that the particular file exists and that it's OK to export
        webstat_files = [x for x in os.listdir(CFG_TMPDIR) if x.startswith("webstat")]
        if argd["filename"] not in webstat_files:
            return "Bad file."

        # Set correct header type
        req.content_type = argd["mime"]
        req.send_http_header()

        # Rebuild path, send it to the user, and clean up.
        filename = CFG_TMPDIR + '/' +  argd["filename"]
        req.sendfile(filename)
        os.remove(filename)

