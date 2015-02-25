# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013, 2014 CERN.
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

"""Invenio WebAuthorlistmanager Administrator Interface."""

import sys
from invenio.ext.legacy.handler import WebInterfaceDirectory, wash_urlargd
from invenio.legacy.wsgi.utils import Field
from invenio.utils.json import json, json_unicode_to_utf8, CFG_JSON_AVAILABLE
from invenio.config import CFG_SITE_LANG, CFG_SITE_SECURE_URL, CFG_SITE_URL
from invenio.base.i18n import gettext_set_language
from invenio.legacy.webpage import page
from invenio.legacy.webuser import getUid
from invenio.utils.url import redirect_to_url

import invenio.legacy.template
authorlist_templates = invenio.legacy.template.load('authorlist')
from invenio.legacy.authorlist import engine as authorlist_engine
from invenio.legacy.authorlist import dblayer as authorlist_db

navtrail = (' <a class="navtrail" href=\"%s/youraccount/display\">Admin Area</a> '
            ) % CFG_SITE_SECURE_URL

__lastupdated__ = """$Date$"""

class WebInterfaceAuthorlistPages(WebInterfaceDirectory):

    _exports = ['']

    def index(self, req, form):
        """Handle all requests"""

        uid = getUid(req)
        argd = wash_urlargd(form, {'ln' : (str, CFG_SITE_LANG),
                           'state' : (str, '')})
        ln = argd['ln']
        state = argd['state']
        _ = gettext_set_language(ln)

        # Abort if the simplejson module isn't available
        if not CFG_JSON_AVAILABLE:
            title = 'Authorlist Manager'
            body = '''Sorry, the record editor cannot operate when the
                `simplejson' module is not installed.  Please see the INSTALL
                file.'''
            return page(title       = title,
                        body        = body,
                        errors      = [],
                        warnings    = [],
                        uid         = uid,
                        language    = ln,
                        navtrail    = navtrail,
                        lastupdated = __lastupdated__,
                        req         = req)

        # Extract additional JSON data from form
        if 'options' in form:
            options = json.loads(str(form['options']))
            # Deunicode all strings (Invenio doesn't have unicode
            # support).
            options = json_unicode_to_utf8(options)

        # Authorization.
        not_authorized = authorlist_engine.user_authorization(req, ln)
        if not_authorized:
            return not_authorized

        # User is authorized, let's handle different states
        # if no state parameter, load the main page
        if state == '':

            return page(title         = _('Author List Manager'),
                        metaheaderadd = authorlist_templates.index_header(),
                        body          = authorlist_templates.body(),
                        errors        = [],
                        warnings      = [],
                        uid           = uid,
                        language      = ln,
                        navtrail      = navtrail,
                        lastupdated   = __lastupdated__,
                        req           = req)

        elif state == 'itemize':
            data = authorlist_db.itemize(uid)

            req.content_type = 'application/json'
            req.write(json.dumps(data))

        # open paremeter set? initialize a Authorlist instance
        elif state == 'open':
            # if 'id' in url, check if user has right to modify this paper
            try:
                received = wash_urlargd(form, {'id': (str, None)})
                paper_id = received['id']

                if authorlist_engine.check_user_rights(uid, paper_id):
                    return page(title         = _('Author List Manager'),
                        metaheaderadd = authorlist_templates.list_header(),
                        body          = authorlist_templates.body(),
                        errors        = [],
                        warnings      = [],
                        uid           = uid,
                        language      = ln,
                        navtrail      = navtrail,
                        lastupdated   = __lastupdated__,
                        req           = req)
                else:
                    # no rights to modify this paper
                    redirect_to_url(req, '%s/authorlist/' % (CFG_SITE_URL))
            except:
                # redirect to the main page if weird stuff happens
                redirect_to_url(req, '%s/authorlist/' % (CFG_SITE_URL))

        # On load state we will answer with the JSON encoded data of the passed
        # paper id. Should usually not be directly surfed by the user.
        elif state == 'load':
            try:
                received = wash_urlargd(form, {'id': (str, None)})
                paper_id = received['id']
                data = authorlist_db.load(paper_id)

                req.content_type = 'application/json'
                req.write(json.dumps(data))
            except:
                # redirect to the main page if weird stuff happens
                redirect_to_url(req, '%s/authorlist/' % (CFG_SITE_URL))

        # The save state saves the send data in the database using the passed
        # paper id. Responds with a JSON object containing the id of the paper
        # as saved in the database. Should usually not be surfed directly by the
        # user
        elif state == 'save':
            try:
                received = wash_urlargd(form, {'id': (str, None),
                                               'data': (str, '')})
                paper_id = received['id']
                in_data = json.loads(received['data'])
                out_data = authorlist_db.save(paper_id, uid, in_data)

                req.content_type = 'application/json'
                req.write(json.dumps(out_data))
            except:
                # redirect to the main page if something weird happens
                redirect_to_url(req, '%s/authorlist/' % (CFG_SITE_URL))

        # Clones the paper with the given id in the database and responds with a
        # JSON object containing the id of the clone. Should usually not surfed
        # directly by the user.
        elif state == 'clone':
            try:
                received = wash_urlargd(form, {'id': (str, None)})
                paper_id = received['id']
                data = authorlist_db.clone(paper_id, uid)

                req.content_type = 'application/json'
                req.write(json.dumps(data))
            except:
                # redirect to the main page if something weird happens
                redirect_to_url(req, '%s/authorlist/' % (CFG_SITE_URL))

        # Transform the sent data into the format passed in the URL using a
        # authorlist_engine converter. Reponds with the MIME type of the
        # converter and offers it as a download (content-disposition header).
        elif state == 'export':
            try:
                received = wash_urlargd(form, {'format': (str, None),
                                               'data': (str, '')})
                data_format = received['format']
                data = received['data']

                converter = authorlist_engine.Converters.get(data_format)

                attachement = 'attachement; filename="%s"' % converter.FILE_NAME
                req.headers_out['Content-Type'] = converter.CONTENT_TYPE
                req.headers_out['Content-Disposition'] = attachement
                #redirect_to_url(req, authorlist_engine.dumps(data, converter))
                req.write(authorlist_engine.dumps(data, converter))
            except:
                # throw exception if something weird happens
                return sys.exc_info()

        elif state == 'delete':
            try:
                received = wash_urlargd(form, {'id': (str, None)})
                paper_id = received['id']

                data = authorlist_db.delete(paper_id)

                req.content_type = 'application/json'
                req.write(json.dumps(data))
            except:
                # redirect to the main page if something weird happens
                redirect_to_url(req, '%s/authorlist/' % (CFG_SITE_URL))

        elif state == 'import':
            try:
                received = wash_urlargd(form, {'importid': (str, None)})
                recID = received['importid']
                data = authorlist_engine.retrieve_data_from_record(recID)
                req.content_type = 'application/json'
                req.write(json.dumps(data))
            except:
                # redirect to the main page if something weird happens
                redirect_to_url(req, '%s/authorlist/' % (CFG_SITE_URL))

        elif state == 'importxml':
            try:
                received = wash_urlargd(form, {'xmlfile': (Field, None)})
                xml_string = received['xmlfile'].value
                import_data = authorlist_engine.retrieve_data_from_xml(xml_string)
                req.content_type = 'application/json'
                req.write(json.dumps(import_data))
            except:
                # redirect to the main page if something weird happens
                redirect_to_url(req, '%s/authorlist/' % (CFG_SITE_URL))
        # No state given, just go to the main page.
        else:
            redirect_to_url(req, '%s/authorlist/' % (CFG_SITE_URL))

    def __call__(self, req, form):
        """Redirect calls without final slash."""
        redirect_to_url(req, '%s/authorlist/' % (CFG_SITE_SECURE_URL))
