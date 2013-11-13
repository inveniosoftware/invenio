## This file is part of Invenio.
## Copyright (C) 2011, 2012 CERN.
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

# pylint: disable=C0103
"""Invenio Interface for bibsched live view."""

import sys
if sys.hexversion < 0x2060000:
    try:
        import simplejson as json
        simplejson_available = True
    except ImportError:
        # Okay, no Ajax app will be possible, but continue anyway,
        # since this package is only recommended, not mandatory.
        simplejson_available = False
else:
    import json
    simplejson_available = True

from invenio.config import CFG_SITE_URL
from invenio.access_control_engine import acc_authorize_action
from invenio.ext.legacy.handler import WebInterfaceDirectory
from invenio.bibrankadminlib import tupletotable
from invenio.webpage import page
from invenio.bibsched_webapi import get_javascript, get_bibsched_tasks, \
                                    get_bibsched_mode, get_css, get_motd_msg
from invenio.legacy.webuser import page_not_authorized

import time

class WebInterfaceBibSchedPages(WebInterfaceDirectory):
    """Defines the set of /bibsched pages."""

    _exports = ['',]

    def __init__(self):
        """Initialize."""
        pass

    def index(self, req, form):
        """ Display live BibSched queue
        """
        referer = '/admin2/bibsched/'
        navtrail = (' <a class="navtrail" href=\"%s/help/admin\">Admin Area</a> '
            ) % CFG_SITE_URL
        auth_code, auth_message = acc_authorize_action(req, 'cfgbibsched')
        if auth_code != 0:
            return page_not_authorized(req=req, referer=referer,
                                       text=auth_message, navtrail=navtrail)
        bibsched_tasks = get_bibsched_tasks()
        header = ["ID", "Name", "Priority", "User", "Time", "Status",
                  "Progress"]
        map_status_css = {'WAITING': 'task_waiting', 'RUNNING': 'task_running',
                          'DONE WITH ERRORS': 'task_error'}
        bibsched_error = False
        motd_msg = get_motd_msg()
        actions = []
        body_content = ''
        if len(motd_msg) > 0:
            body_content += '<div class="clean_error">' + motd_msg + '</div><br />'
        if not form.has_key('jsondata'):
            body_content = '<div id="bibsched_table">'
        if len(bibsched_tasks) > 0:
            for task in bibsched_tasks:
                (tskid, proc, priority, user, runtime, status, progress) = task
                actions.append([tskid, proc, priority, user, runtime,
                               '<span class=%s>' % (status in map_status_css and
                                map_status_css[status] or '') + (status !="" and
                                status or '') + '</span>', (progress !="" and
                                progress or '')])
                if 'ERROR' in status:
                    bibsched_error = True
            body_content += tupletotable(header=header, tuple=actions,
                                         alternate_row_colors_p=True)
        if bibsched_error:
            body_content += '<br /><img src="%s"><span class="bibsched_status"> The queue contains errors</span><br />' % ("/img/aid_reject.png")
        else:
            body_content += '<br /><img src="%s"><span class="bibsched_status"> BibSched is working without errors</span><br />' % ("/img/aid_check.png")
        body_content += '<br /><span class="mode">Mode: %s</span>' % (get_bibsched_mode())
        body_content += '<br /><br /><span class="last_updated">Last updated: %s</span>' % (time.strftime("%a %b %d, %Y  %-I:%M:%S %p", time.localtime(time.time())))
        if form.has_key('jsondata'):
            json_response = {}
            json_response.update({'bibsched': body_content})
            return json.dumps(json_response)
        else:
            body_content += '</div>'
            return page(title       = "BibSched live view",
                        body        = body_content,
                        errors      = [],
                        warnings    = [],
                        metaheaderadd = get_javascript() + get_css(),
                        req         = req)
