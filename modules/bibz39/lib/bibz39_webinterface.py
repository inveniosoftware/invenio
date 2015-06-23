# This file is part of Invenio.
# Copyright (C) 2011, 2012 CERN.
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
"""Invenio Interface for bibz39 live view."""
import cgi
from invenio.bibrecord import create_record, record_add_field

try:
    import json
except ImportError:
    import simplejson as json

from invenio.config import CFG_SITE_URL, CFG_SITE_SECURE_URL
from invenio.access_control_engine import acc_authorize_action
from invenio.webinterface_handler import WebInterfaceDirectory, wash_urlargd
from invenio.webpage import page
from invenio.bibz39_webapi import get_javascript, get_css
from invenio.webuser import page_not_authorized
from invenio.urlutils import redirect_to_url
from invenio.bibedit_utils import create_cache
from invenio.bibedit_dblayer import reserve_record_id
from invenio.webuser import getUid


class WebInterfacebibz39Pages(WebInterfaceDirectory):
    """Defines the set of /bibz39 pages."""

    _exports = ['']

    def index(self, req, form):
        """ Display live bibz39 queue
        """
        referer = '/admin2/bibz39/'
        navtrail = ' <a class="navtrail" href=\"%s/help/admin\">Admin Area</a> ' % CFG_SITE_URL

        auth_code, auth_message = acc_authorize_action(req, 'cfgbibz39')
        if auth_code != 0:
            return page_not_authorized(req=req, referer=referer,
                                       text=auth_message, navtrail=navtrail)

        argd = wash_urlargd(form, {
            'isbn': (str, ''),
            'marcxml': (str, ''),
        })

        if argd['marcxml']:
            uid = getUid(req)
            new_recid = reserve_record_id()
            record = create_record(argd["marcxml"])[0]
            record_add_field(record, '001',
                             controlfield_value=str(new_recid))
            create_cache(new_recid, uid, record, True)
            redirect_to_url(req, '{0}/record/edit/#state=edit&recid={1}'.format(CFG_SITE_SECURE_URL,
                                                                                new_recid))

        body_content = ''
        body_content += """<div id='search_area'><form method="post" action="/admin2/bibz39/">
        <label for="isbn">ISBN:</label>
        <input type="text" name="isbn" id="isbn" />
        <input type="submit" value="query" class="adminbutton" />
        </form></div>"""

        if "isbn" in argd and argd["isbn"]:
            from PyZ3950 import zoom, zmarc

            list_of_marc_record = []

            conn = zoom.Connection('z3950.loc.gov', 7090)
            conn.databaseName = 'VOYAGER'
            conn.preferredRecordSyntax = 'USMARC'

            query = zoom.Query('CCL', 'isbn={0}'.format(argd["isbn"]))

            res = conn.search(query)

            if res:
                body_content += "<div> <table id='result_area'>"
                body_content += "<tr><th>ID</th><th>Title<th><th>Actions</th></tr>"
                for identifier, rec in enumerate(res):
                    list_of_marc_record.append(zmarc.MARC(rec.data))
                    title_constituants = list_of_marc_record[identifier].fields[245][0][2]
                    title = ''
                    for title_constituant in title_constituants:
                        title += title_constituant[1] + "<br>"
                    if identifier % 2:
                        class_html = "class='coloredrow'"
                    else:
                        class_html = ""
                    body_content += "<tr {3}><td>{0}</td><td><a href='#' onclick='showxml({0})'>{1}</a><th><th>{2}</th></tr>".format(
                        identifier, title,
                        '<form method="post" action="/admin2/bibz39/"><input type="hidden"  name="marcxml"  value="{0}"><input type="submit" value="bibedit" /></form>'.format(
                            cgi.escape(list_of_marc_record[identifier].toMARCXML()).replace("\"",
                                                                                            "&quot;").replace(
                                "\'", "&quot;")), class_html)

                body_content += "</table></div>"
                body_content += '<script type="text/javascript">'
                data = {}
                for i, rec in enumerate(list_of_marc_record):
                    data[i] = rec.toMARCXML()
                body_content += " var gAllMarcXml= {0};".format(data)
                body_content += '</script>'
            else:
                body_content += "No result"
            conn.close()

            body_content += '</div>'
        return page(title="bibz39 module",
                    body=body_content,
                    errors=[],
                    warnings=[],
                    metaheaderadd=get_javascript() + get_css(),
                    req=req)

    def __call__(self, req, form):
        """Redirect calls without final slash."""
        redirect_to_url(req, '%s/admin2/bibz39/' % CFG_SITE_SECURE_URL)
