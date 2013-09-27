## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011, 2012 CERN.
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
"""Invenio BibMerge Administrator Interface."""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

from invenio.access_control_engine import acc_authorize_action
from invenio.config import CFG_SITE_LANG, CFG_SITE_SECURE_URL, CFG_SITE_RECORD
from invenio.search_engine import guess_primary_collection_of_a_record
from invenio.webpage import page
from invenio.webuser import getUid, page_not_authorized, collect_user_info
from invenio.utils.json import json, json_unicode_to_utf8
from invenio.utils.url import redirect_to_url
from invenio.webinterface_handler import WebInterfaceDirectory, wash_urlargd
from invenio.bibmerge_engine import perform_request_init, \
                                    perform_request_ajax

navtrail = (' <a class="navtrail" href=\"%s/help/admin\">Admin Area</a> '
            ) % CFG_SITE_SECURE_URL


class WebInterfaceMergePages(WebInterfaceDirectory):
    """Defines the set of /merge pages."""

    _exports = ['']

    def __init__(self, recid=None):
        """Initialize."""
        self.recid = recid

    def index(self, req, form):
        """Handle all BibMerge requests.
        The responsibilities of this functions are:
        * JSON decoding and encoding.
        * Redirection, if necessary.
        * Authorization.
        * Calling the appropriate function from the engine.
        """
        # If it is an Ajax request, extract any JSON data.
        ajax_request, recid1, recid2 = False, None, None
        argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG)})
        if form.has_key('jsondata'):
            json_data = json.loads(str(form['jsondata']))
            # Deunicode all strings (Invenio doesn't have unicode
            # support).
            json_data = json_unicode_to_utf8(json_data)
            ajax_request = True
            json_response = {}
            if json_data.has_key('recID1'):
                recid1 = json_data['recID1']
            if json_data.has_key('recID2'):
                recid2 = json_data['recID2']

        # Authorization.
        user_info = collect_user_info(req)
        if user_info['email'] == 'guest':
            # User is not logged in.
            if not ajax_request:
                # Do not display the introductory recID selection box to guest
                # users (as it used to be with v0.99.0):
                auth_code, auth_message = acc_authorize_action(req, 'runbibmerge')
                referer = '/merge/'
                return page_not_authorized(req=req, referer=referer,
                                           text=auth_message, navtrail=navtrail)
            else:
                # Session has most likely timed out.
                json_response.update({'resultCode': 1,
                                      'resultText': 'Error: Not logged in'})
                return json.dumps(json_response)

        elif self.recid:
            # Handle RESTful call by storing recid and redirecting to
            # generic URL.
            redirect_to_url(req, '%s/%s/merge/' % (CFG_SITE_SECURE_URL, CFG_SITE_RECORD) )

        if recid1 is not None:
            # Authorize access to record 1.
            auth_code, auth_message = acc_authorize_action(req, 'runbibmerge',
                collection=guess_primary_collection_of_a_record(recid1))
            if auth_code != 0:
                json_response.update({'resultCode': 1, 'resultText': 'No access to record %s' % recid1})
                return json.dumps(json_response)
        if recid2 is not None:
            # Authorize access to record 2.
            auth_code, auth_message = acc_authorize_action(req, 'runbibmerge',
                collection=guess_primary_collection_of_a_record(recid2))
            if auth_code != 0:
                json_response.update({'resultCode': 1, 'resultText': 'No access to record %s' % recid2})
                return json.dumps(json_response)

        # Handle request.
        uid = getUid(req)
        if not ajax_request:
            # Show BibEdit start page.
            body, errors, warnings = perform_request_init()
            metaheaderadd = """<script type="text/javascript" src="%(site)s/js/json2.js"></script>
  <script type="text/javascript" src="%(site)s/js/bibmerge_engine.js"></script>""" % {'site': CFG_SITE_SECURE_URL}
            title = 'Record Merger'
            return page(title         = title,
                        metaheaderadd = metaheaderadd,
                        body          = body,
                        errors        = errors,
                        warnings      = warnings,
                        uid           = uid,
                        language      = argd['ln'],
                        navtrail      = navtrail,
                        lastupdated   = __lastupdated__,
                        req           = req)
        else:
            # Handle AJAX request.
            json_response = perform_request_ajax(req, uid, json_data)
            return json.dumps(json_response)

    def __call__(self, req, form):
        """Redirect calls without final slash."""
        redirect_to_url(req, '%s/%s/merge/' % (CFG_SITE_SECURE_URL, CFG_SITE_RECORD))
