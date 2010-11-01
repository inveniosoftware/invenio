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

__revision__ = "$Id$"
__lastupdated__ = "$Date$"

import os
from urllib import unquote
from invenio import webinterface_handler_config as apache

from invenio.config import \
     CFG_TMPDIR, \
     CFG_SITE_URL, \
     CFG_SITE_NAME, \
     CFG_SITE_LANG
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory
from invenio.webpage import page
from invenio.access_control_engine import acc_authorize_action
from invenio.webuser import collect_user_info, page_not_authorized
from invenio.urlutils import redirect_to_url

from invenio.webstat import perform_request_index
from invenio.webstat import perform_display_keyevent
from invenio.webstat import perform_display_customevent
from invenio.webstat import perform_display_customevent_help
from invenio.webstat import register_customevent

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
                 'download_frequency', 'customevent', 'customevent_help', 'customevent_register',
                 'export' ]

    navtrail = """<a class="navtrail" href="%s/stats/%%(ln_link)s">Statistics</a>""" % CFG_SITE_URL

    def __call__(self, req, form):
        """Index page."""
        argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG)})
        ln = argd['ln']
        user_info = collect_user_info(req)
        (auth_code, auth_msg) = acc_authorize_action(user_info, 'runwebstatadmin')
        if auth_code:
            return page_not_authorized(req,
                navtrail=self.navtrail % {'ln_link':(ln != CFG_SITE_LANG and '?ln='+ln) or ''},
                text=auth_msg,
                navmenuid='index',
                ln=ln)

        return page(title="Statistics",
                    body=perform_request_index(ln=ln),
                    description="CDS, Statistics",
                    keywords="CDS, statistics",
                    req=req,
                    lastupdated=__lastupdated__,
                    navmenuid='stats',
                    language=ln)

    # KEY EVENT SECTION

    def collection_population(self, req, form):
        """Collection population statistics page."""
        argd = wash_urlargd(form, {'collection': (str, CFG_SITE_NAME),
                                   'timespan': (str, "today"),
                                   'format': (str, SUITABLE_GRAPH_FORMAT),
                                   'ln': (str, CFG_SITE_LANG)})
        ln = argd['ln']
        user_info = collect_user_info(req)
        (auth_code, auth_msg) = acc_authorize_action(user_info, 'runwebstatadmin')
        if auth_code:
            return page_not_authorized(req,
                navtrail=self.navtrail % {'ln_link':(ln != CFG_SITE_LANG and '?ln='+ln) or ''},
                text=auth_msg,
                navmenuid='collection population',
                ln=ln)

        return page(title="Collection population",
                    body=perform_display_keyevent('collection population', argd, req, ln=ln),
                    navtrail="""<a class="navtrail" href="%s/stats/%s">Statistics</a>""" % \
                    (CFG_SITE_URL, (ln != CFG_SITE_LANG and '?ln='+ln) or ''),
                    description="CDS, Statistics, Collection population",
                    keywords="CDS, statistics, collection population",
                    req=req,
                    lastupdated=__lastupdated__,
                    navmenuid='collection population',
                    language=ln)

    def search_frequency(self, req, form):
        """Search frequency statistics page."""
        argd = wash_urlargd(form, {'timespan': (str, "today"),
                                   'format': (str, SUITABLE_GRAPH_FORMAT),
                                   'ln': (str, CFG_SITE_LANG)})
        ln = argd['ln']
        user_info = collect_user_info(req)
        (auth_code, auth_msg) = acc_authorize_action(user_info, 'runwebstatadmin')
        if auth_code:
            return page_not_authorized(req,
                navtrail=self.navtrail % {'ln_link':(ln != CFG_SITE_LANG and '?ln='+ln) or ''},
                text=auth_msg,
                navmenuid='search frequency',
                ln=ln)

        return page(title="Search frequency",
                    body=perform_display_keyevent('search frequency', argd, req, ln=ln),
                    navtrail="""<a class="navtrail" href="%s/stats/%s">Statistics</a>""" % \
                    (CFG_SITE_URL, (ln != CFG_SITE_LANG and '?ln='+ln) or ''),
                    description="CDS, Statistics, Search frequency",
                    keywords="CDS, statistics, search frequency",
                    req=req,
                    lastupdated=__lastupdated__,
                    navmenuid='search frequency',
                    language=ln)

    def search_type_distribution(self, req, form):
        """Search type distribution statistics page."""
        user_info = collect_user_info(req)
        (auth_code, auth_msg) = acc_authorize_action(user_info, 'runwebstatadmin')
        argd = wash_urlargd(form, {'timespan': (str, "today"),
                                   'format': (str, SUITABLE_GRAPH_FORMAT),
                                   'ln': (str, CFG_SITE_LANG)})
        ln = argd['ln']
        if auth_code:
            return page_not_authorized(req,
                navtrail=self.navtrail % {'ln_link':(ln != CFG_SITE_LANG and '?ln='+ln) or ''},
                text=auth_msg,
                navmenuid='search type distribution',
                ln=ln)

        return page(title="Search type distribution",
                    body=perform_display_keyevent('search type distribution', argd, req, ln=ln),
                    navtrail="""<a class="navtrail" href="%s/stats/%s">Statistics</a>""" % \
                    (CFG_SITE_URL, (ln != CFG_SITE_LANG and '?ln='+ln) or ''),
                    description="CDS, Statistics, Search type distribution",
                    keywords="CDS, statistics, search type distribution",
                    req=req,
                    lastupdated=__lastupdated__,
                    navmenuid='search type distribution',
                    language=ln)

    def download_frequency(self, req, form):
        """Download frequency statistics page."""
        argd = wash_urlargd(form, {'timespan': (str, "today"),
                                   'format': (str, SUITABLE_GRAPH_FORMAT),
                                   'ln': (str, CFG_SITE_LANG)})
        ln = argd['ln']
        user_info = collect_user_info(req)
        (auth_code, auth_msg) = acc_authorize_action(user_info, 'runwebstatadmin')
        if auth_code:
            return page_not_authorized(req,
                navtrail=self.navtrail % {'ln_link':(ln != CFG_SITE_LANG and '?ln='+ln) or ''},
                text=auth_msg,
                navmenuid='download frequency',
                ln=ln)

        return page(title="Download frequency",
                    body=perform_display_keyevent('download frequency', argd, req, ln=ln),
                    navtrail="""<a class="navtrail" href="%s/stats/%s">Statistics</a>""" % \
                    (CFG_SITE_URL, (ln != CFG_SITE_LANG and '?ln='+ln) or ''),
                    description="CDS, Statistics, Download frequency",
                    keywords="CDS, statistics, download frequency",
                    req=req,
                    lastupdated=__lastupdated__,
                    navmenuid='download frequency',
                    language=ln)

    # CUSTOM EVENT SECTION

    def customevent(self, req, form):
        """Custom event statistics page"""
        arg_format = {'ids': (list, []),
                     'timespan': (str, "today"),
                     'format': (str, SUITABLE_GRAPH_FORMAT),
                     'ln': (str, CFG_SITE_LANG)}
        for key in form.keys():
            if key[:4] == 'cols':
                i = key[4:]
                arg_format['cols'+i]=(list, [])
                arg_format['col_value'+i]=(list, [])
                arg_format['bool'+i]=(list, [])
        argd = wash_urlargd(form, arg_format)

        ln = argd['ln']
        user_info = collect_user_info(req)
        (auth_code, auth_msg) = acc_authorize_action(user_info, 'runwebstatadmin')
        if auth_code:
            return page_not_authorized(req,
                navtrail=self.navtrail % {'ln_link':(ln != CFG_SITE_LANG and '?ln='+ln) or ''},
                text=auth_msg,
                navmenuid='custom event',
                ln=ln)

        body = perform_display_customevent(argd['ids'], argd, req=req, ln=ln)
        return page(title="Custom event",
                    body=body,
                    navtrail="""<a class="navtrail" href="%s/stats/%s">Statistics</a>""" % \
                    (CFG_SITE_URL, (ln != CFG_SITE_LANG and '?ln='+ln) or ''),
                    description="CDS Personalize, Statistics, Custom event",
                    keywords="CDS, statistics, custom event",
                    req=req,
                    lastupdated=__lastupdated__,
                    navmenuid='custom event',
                    language=ln)

    def customevent_help(self, req, form):
        """Custom event help page"""
        argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG)})
        ln = argd['ln']
        user_info = collect_user_info(req)
        (auth_code, auth_msg) = acc_authorize_action(user_info, 'runwebstatadmin')
        if auth_code:
            return page_not_authorized(req,
                navtrail=self.navtrail % {'ln_link':(ln != CFG_SITE_LANG and '?ln='+ln) or ''},
                text=auth_msg,
                navmenuid='custom event help',
                ln=ln)

        return page(title="Custom event help",
                    body=perform_display_customevent_help(ln=ln),
                    navtrail="""<a class="navtrail" href="%s/stats/%s">Statistics</a>""" % \
                    (CFG_SITE_URL, (ln != CFG_SITE_LANG and '?ln='+ln) or ''),
                    description="CDS Personalize, Statistics, Custom event help",
                    keywords="CDS, statistics, custom event help",
                    req=req,
                    lastupdated=__lastupdated__,
                    navmenuid='custom event help',
                    language=ln)

    def customevent_register(self, req, form):
        """Register a customevent and reload to it defined url"""
        argd = wash_urlargd(form, {'id': (str, ""),
                                   'arg': (str, ""),
                                   'url': (str, ""),
                                   'ln': (str, CFG_SITE_LANG)})
        params = argd['arg'].split(',')
        if "WEBSTAT_IP" in params:
            index = params.index("WEBSTAT_IP")
            params[index] = str(req.remote_ip)
        register_customevent(argd['id'], params)
        return redirect_to_url(req, unquote(argd['url']), apache.HTTP_MOVED_PERMANENTLY)


    # EXPORT SECTION

    def export(self, req, form):
        """Exports data"""
        argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG)})
        ln = argd['ln']
        user_info = collect_user_info(req)
        (auth_code, auth_msg) = acc_authorize_action(user_info, 'runwebstatadmin')
        if auth_code:
            return page_not_authorized(req,
                navtrail=self.navtrail % {'ln_link':(ln != CFG_SITE_LANG and '?ln='+ln) or ''},
                text=auth_msg,
                navmenuid='export',
                ln=ln)

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

    index = __call__
