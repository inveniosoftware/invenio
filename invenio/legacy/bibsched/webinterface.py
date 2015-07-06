# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2014 CERN.
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

# pylint: disable=C0103
"""Invenio Interface for bibsched live view."""

import time
try:
    import json
except ImportError:
    import simplejson as json

from invenio.config import CFG_SITE_URL, CFG_SITE_SECURE_URL
from invenio.modules.access.engine import acc_authorize_action
from invenio.ext.legacy.handler import WebInterfaceDirectory
from invenio.legacy.webpage import page
from invenio.legacy.bibsched.webapi import get_javascript, get_bibsched_tasks, \
    get_bibsched_mode, get_css, get_motd_msg
from invenio.legacy.webuser import page_not_authorized
from invenio.utils.url import redirect_to_url


def tupletotable(header=[], tuple=[], start='', end='', extracolumn='', highlight_rows_p=False, alternate_row_colors_p=False):
    """create html table for a tuple.
         header - optional header for the columns
          tuple - create table of this
          start - text to be added in the beginning, most likely beginning of a form
            end - text to be added in the end, mot likely end of a form.
    extracolumn - mainly used to put in a button.
      highlight_rows_p - if the cursor hovering a row should highlight the full row or not
alternate_row_colors_p - if alternate background colours should be used for the rows
    """

    # study first row in tuple for alignment
    align = []
    try:
        firstrow = tuple[0]

        if type(firstrow) in [int, long]:
            align = ['admintdright']
        elif type(firstrow) in [str, dict]:
            align = ['admintdleft']
        else:
            for item in firstrow:
                if type(item) is int:
                    align.append('admintdright')
                else:
                    align.append('admintdleft')
    except IndexError:
        firstrow = []

    tblstr = ''
    for h in header + ['']:
        tblstr += '  <th class="adminheader">%s</th>\n' % (h, )
    if tblstr:
        tblstr = ' <tr>\n%s\n </tr>\n' % (tblstr, )

    tblstr = start + '<table class="admin_wvar_nomargin">\n' + tblstr

    # extra column
    try:
        extra = '<tr class="%s">' % (
            highlight_rows_p and 'admin_row_highlight' or '')

        if type(firstrow) not in [int, long, str, dict]:
            # for data in firstrow: extra += '<td class="%s">%s</td>\n' % ('admintd', data)
            for i in range(len(firstrow)):
                extra += '<td class="{0}">{1}</td>\n'.format(
                    align[i], firstrow[i])
        else:
            extra += '  <td class="%s">%s</td>\n' % (align[0], firstrow)
        extra += '<td class="extracolumn" rowspan="%s" style="vertical-align: top;">\n%s\n</td>\n</tr>\n' % (
            len(tuple), extracolumn)
    except IndexError:
        extra = ''
    tblstr += extra

    # for i in range(1, len(tuple)):
    j = 0
    for row in tuple[1:]:
        j += 1
        tblstr += ' <tr class="%s %s">\n' % (highlight_rows_p and 'admin_row_highlight' or '',
                                             (j % 2 and alternate_row_colors_p) and 'admin_row_color' or '')
        # row = tuple[i]
        if type(row) not in [int, long, str, dict]:
            # for data in row: tblstr += '<td class="admintd">%s</td>\n' % (data,)
            for i in range(len(row)):
                tblstr += '<td class="{0}">{1}</td>\n'.format(align[i], utf8ifier(row[i]))
        else:
            tblstr += '  <td class="%s">%s</td>\n' % (align[0], row)
        tblstr += ' </tr> \n'

    tblstr += '</table> \n '
    tblstr += end

    return tblstr


class WebInterfaceBibSchedPages(WebInterfaceDirectory):
    """Defines the set of /bibsched pages."""

    _exports = ['']

    def index(self, req, form):
        """ Display live BibSched queue
        """
        referer = '/admin2/bibsched/'
        navtrail = ' <a class="navtrail" href=\"%s/help/admin\">Admin Area</a> ' % CFG_SITE_URL

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
        if 'jsondata' not in form:
            body_content = '<div id="bibsched_table">'
        if bibsched_tasks:
            for task in bibsched_tasks:
                tskid, proc, priority, user, runtime, status, progress = task
                actions.append([tskid, proc, priority, user, runtime,
                               '<span class=%s>' % (status in map_status_css and
                                map_status_css[status] or '') + (status != "" and
                                status or '') + '</span>', (progress != "" and
                                progress or '')])
                if 'ERROR' in status:
                    bibsched_error = True
        if bibsched_error:
            body_content += '<br /><img src="%s"><span class="bibsched_status"> The queue contains errors</span><br />' % ("/img/aid_reject.png")
        else:
            body_content += '<br /><img src="%s"><span class="bibsched_status"> BibSched is working without errors</span><br />' % ("/img/aid_check.png")
        body_content += '<br /><span class="mode">Mode: %s</span>' % (get_bibsched_mode())
        body_content += '<br /><br /><span class="last_updated">Last updated: %s</span>' % \
                (time.strftime("%a %b %d, %Y  %-I:%M:%S %p",
                 time.localtime(time.time())))
        if 'jsondata' in form:
            json_response = {}
            json_response.update({'bibsched': body_content})
            return json.dumps(json_response)
        else:
            body_content += '</div>'
            return page(title="BibSched live view",
                        body=body_content,
                        errors=[],
                        warnings=[],
                        metaheaderadd=get_javascript() + get_css(),
                        req=req)

    def __call__(self, req, form):
        """Redirect calls without final slash."""
        redirect_to_url(req, '%s/admin2/bibsched/' % CFG_SITE_SECURE_URL)
