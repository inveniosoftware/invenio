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

# pylint: disable-msg=C0103
"""CDS Invenio BibEdit Administrator Interface."""

__revision__ = "$Id"

__lastupdated__ = """$Date: 2008/08/12 09:26:46 $"""

try:
    import simplejson as json
except ImportError:
    pass # okay, no Ajax app will be possible, but continue anyway

from invenio.access_control_engine import acc_authorize_action
from invenio.bibedit_engine import perform_request_init, \
    perform_request_record, perform_request_search, \
    perform_request_update_record, perform_request_user
from invenio.bibedit_utils import json_unicode_to_utf8
from invenio.config import CFG_SITE_LANG, CFG_SITE_URL
from invenio.search_engine import guess_primary_collection_of_a_record
from invenio.urlutils import redirect_to_url
from invenio.webinterface_handler import WebInterfaceDirectory
from invenio.webpage import page
from invenio.webuser import collect_user_info, getUid, page_not_authorized

navtrail = (' <a class="navtrail" href=\"%s/help/admin\">Admin Area</a> '
            ) % CFG_SITE_URL

class WebInterfaceEditPages(WebInterfaceDirectory):
    """Defines the set of /edit pages."""

    _exports = ['']

    def __init__(self, recid=None):
        """Initialize."""
        self.recid = recid

    def index(self, req, form):
        """Handle all BibEdit requests."""

        # Get any JSON data.
        jsondata = None
        if form.has_key('jsondata'):
            jsondata = form['jsondata']

        user_info = collect_user_info(req)
        if not jsondata:
            # Handle intial request.
            if user_info['email'] == 'guest':
                # Do not display the introductory recID selection box to guest
                # users (as it used to be with v0.99.0):
                auth_code, auth_message = acc_authorize_action(req,
                                                               'runbibedit')
                referer = '/edit/'
                if self.recid:
                    referer = '/edit/#state=edit&recid=%s' % self.recid
                return page_not_authorized(req=req, referer=referer,
                                           text=auth_message, navtrail=navtrail)

            elif self.recid:
                # Handle RESTful call by storing recid and redirecting to
                # generic URL.
                redirect_to_url(req, '%s/record/edit/#state=edit&recid=%s' % (
                        CFG_SITE_URL, self.recid))

            else:
                # Show BibEdit start page.
                body, errors, warnings = perform_request_init()

                title = 'BibEdit'
                ln = CFG_SITE_LANG

                return page(title       = title,
                            body        = body,
                            errors      = errors,
                            warnings    = warnings,
                            uid         = getUid(req),
                            language    = ln,
                            navtrail    = navtrail,
                            lastupdated = __lastupdated__,
                            req         = req)

        # Handle Ajax requests..
        result = {}
        if user_info['email'] == 'guest':
            # Session has most likely timed out.
            result.update({
                    'resultCode': 1,
                    'resultText':
                        'Error: Not logged in'
                    })

        else:
            data = json.loads(str(jsondata))
            # Deunicode all strings (CDS Invenio doesn't have unicode
            # support).
            data = json_unicode_to_utf8(data)

            # Authentication.
            try:
                recid = data['recID']
            except KeyError:
                # Not all requests have a record ID attached (like search).
                auth_code, auth_message = acc_authorize_action(req,
                                                               'runbibedit')
            else:
                auth_code, auth_message = acc_authorize_action(req,
                    'runbibedit',
                    collection=guess_primary_collection_of_a_record(recid))
            if auth_code != 0:
                result.update({
                        'resultCode': 1,
                        'resultText':
                            'Error: Permission denied'
                        })

            else:
                uid = getUid(req)
                requestType = data['requestType']

                if requestType in ('searchForRecord'):
                    # Search request.
                    result.update(perform_request_search(req, data))

                elif requestType in ('changeTagFormat'):
                    # User related requests.
                    result.update(perform_request_user(req, requestType, recid,
                                                       data))
                elif requestType in ('getRecord', 'submit', 'deleteRecord',
                                   'cancel'):
                    # 'Major' record related requests
                    result.update(perform_request_record(req, requestType,
                                                         recid, uid))
                else:
                    # Record updates
                    result.update(perform_request_update_record(
                            requestType, recid, uid, data))

        return json.dumps(result)

    def __call__(self, req, form):
        """Redirect calls without final slash."""
        if self.recid:
            redirect_to_url(req, '%s/record/%s/edit/' % (CFG_SITE_URL,
                                                         self.recid))
        else:
            redirect_to_url(req, '%s/record/edit/' % CFG_SITE_URL)
