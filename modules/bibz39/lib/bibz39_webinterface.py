# coding=utf-8

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
from PyZ3950 import zoom, zmarc
from invenio.bibrecord import create_record, record_add_field, record_xml_output

try:
    import json
except ImportError:
    import simplejson as json

from invenio.bibz39_config import CFG_Z39_SERVER
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

        auth_code, auth_message = acc_authorize_action(req, 'cfgbibedit')
        if auth_code != 0:
            return page_not_authorized(req=req, referer=referer,
                                       text=auth_message, navtrail=navtrail)

        argd = wash_urlargd(form, {
            'search': (str, ''),
            'marcxml': (str, ''),
            'server': (list, []),
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
        body_content += """<div id='search_area'><form id='search_form' method="post" action="/admin2/bibz39/">
        <label for="search">Search request:</label><br>
        <input type="text" name="search" id="search" value="{0}" />
        <select multiple='multiple' name='server'> """.format(cgi.escape(argd['search']))

        for server in CFG_Z39_SERVER.keys():
            body_content += "<option value='{0}'>{0}</option>".format(server)

        body_content += """</select>
        <input type="submit" value="query" class="adminbutton" />

        </form></div>"""

        if "search" in argd and argd["search"]:

            conn = None
            list_of_record = []
            try:
                for server in argd["server"]:

                    res = []
                    err = False
                    conn = zoom.Connection(CFG_Z39_SERVER[server]["address"],
                                           CFG_Z39_SERVER[server]["port"],
                                           user=CFG_Z39_SERVER[server].get("user", None),
                                           password=CFG_Z39_SERVER[server].get("password", None))
                    conn.databaseName = CFG_Z39_SERVER[server]["databasename"]
                    conn.preferredRecordSyntax = CFG_Z39_SERVER[server]["preferredRecordSyntax"]
                    query = zoom.Query('CCL', '{0}'.format(argd["search"]))
                    body_content += "<div id='middle_area'><h3>{0}</h3>".format(server)
                    try:
                        for conn_res in conn.search(query):
                            res.append(conn_res)

                        if len(res) <= 1:
                            body_content += "1 result"
                        else:
                            body_content += "{0} results".format(len(res))
                    except zoom.Bib1Err as e:
                        body_content += "<h4>{0}</h4>".format(e)
                        body_content += '</div>'
                        err = True
                    conn.close()

                    if res:
                        body_content += "<table id='result_area'>"
                        body_content += "<tr><th>ID</th><th>Title<th><th>Actions</th></tr>"

                        for identifier, rec in enumerate(res):
                            list_of_record.append(
                                create_record(
                                    self.interpret_string(
                                        zmarc.MARC(rec.data, strict=0).toMARCXML()))[0])
                            title = ''
                            for title_constituant in list_of_record[identifier]["245"][0][0]:
                                title += title_constituant[1] + "<br>"

                            if identifier % 2:
                                class_html = "class='coloredrow'"
                            else:
                                class_html = ""

                            body_content += "<tr {3}><td>{0}</td><td><a href='#' onclick='showxml({0})'>{1}</a><th><th>{2}</th></tr>".format(
                                identifier, title,
                                '<form method="post" action="/admin2/bibz39/"><input type="hidden"  name="marcxml"  value="{0}"><input type="submit" value="bibedit" /></form>'.format(
                                    cgi.escape(
                                        record_xml_output(list_of_record[identifier])).replace("\"","&quot;").replace("\'", "&quot;")), class_html)

                        body_content += "</table></div>"
                        body_content += '<script type="text/javascript">'
                        body_content += "var gAllMarcXml= {"
                        for i, rec in enumerate(list_of_record):
                            body_content += "{0}:{1},".format(i, json.dumps(record_xml_output(rec)))
                        body_content += "};"
                        body_content += '</script>'

                    else:
                        if not err:
                            body_content += "No result"

            except zoom.QuerySyntaxError:
                body_content += "<div> There is an error in the query syntax<br></div>"
                body_content += '</div>'
                if conn:
                    conn.close()
            except Exception:
                if conn:
                    conn.close()
                raise

            body_content += '</div>'

        return page(title="bibz39 module",
                    body=body_content,
                    errors=[],
                    warnings=[],
                    metaheaderadd=get_javascript() + get_css(),
                    req=req)

    def interpret_string(self, data):
        try:
            list_data = data.split("\n")
            for i in range(len(list_data)):
                list_data[i] = zmarc.MARC8_to_Unicode().translate(list_data[i])
            return "\n".join(list_data)
        except:
            return data

    def __call__(self, req, form):
        """Redirect calls without final slash."""
        redirect_to_url(req, '%s/admin2/bibz39/' % CFG_SITE_SECURE_URL)
