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
"""CDS Invenio BibMerge Administrator Interface."""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

from invenio.access_control_engine import acc_authorize_action
from invenio.config import CFG_SITE_LANG, CFG_SITE_URL
from invenio.search_engine import record_exists
from invenio.webpage import page
from invenio.webuser import getUid, page_not_authorized, collect_user_info

from invenio.urlutils import redirect_to_url
from invenio.webinterface_handler import WebInterfaceDirectory
from invenio.bibedit_utils import json_unicode_to_utf8
import simplejson as json
from invenio.bibmerge_engine import perform_request_init, \
                                    perform_record_compare, \
                                    perform_candidate_record_search, \
                                    perform_request_record, \
                                    perform_request_update_record, \
                                    perform_small_request_update_record

navtrail = (' <a class="navtrail" href=\"%s/help/admin\">Admin Area</a> '
            ) % CFG_SITE_URL


class WebInterfaceMergePages(WebInterfaceDirectory):
    """Defines the set of /merge pages."""

    _exports = ['']

    def __init__(self, recid=None):
        """Initialize."""
        self.recid = recid

    def index(self, req, form):
        """BibMerge Admin interface."""
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
                referer = '/merge/'
                return page_not_authorized(req=req, referer=referer,
                                           text=auth_message, navtrail=navtrail)

            elif self.recid:
                # Handle RESTful call by storing recid and redirecting to
                # generic URL.
                redirect_to_url(req, '%s/record/merge/' % CFG_SITE_URL )

            metaheaderadd = """<script type="text/javascript" src="%(site)s/js/jquery.min.js"></script>
  <script type="text/javascript" src="%(site)s/js/json2.js"></script>
  <script type="text/javascript" src="%(site)s/js/bibmerge_engine.js"></script>""" % {'site': CFG_SITE_URL}

            title = "BibMerge Admin"
            ln = CFG_SITE_LANG
            body, errors, warnings = perform_request_init()

            return page(title         = title,
                        metaheaderadd = metaheaderadd,
                        body          = body,
                        errors        = errors,
                        warnings      = warnings,
                        uid           = getUid(req),
                        language      = ln,
                        navtrail      = navtrail,
                        lastupdated   = __lastupdated__,
                        req           = req)

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
            data = json_unicode_to_utf8(data)
            import os

            uid = getUid(req)
            requestType = data['requestType']
            if requestType == "getRecordCompare" or requestType == 'submit' or requestType == 'cancel':
                recid1 = data["recID1"]
                recid2 = data["recID2"]
                result = perform_request_record(req, requestType, recid1, recid2, uid)
            elif requestType == 'getFieldGroup'  or requestType == 'getFieldGroupDiff' \
               or requestType == 'mergeFieldGroup' or requestType == 'mergeNCFieldGroup' \
               or requestType == 'replaceField' or requestType == 'addField' \
               or requestType == 'deleteField' or requestType == 'mergeField':
                recid1 = data["recID1"]
                recid2 = data["recID2"]
                result = perform_request_update_record(requestType, recid1, recid2, uid, data)
            elif requestType == "searchCanditates":
                result = perform_candidate_record_search(data['query'])
            elif requestType == 'deleteSubfield' or requestType == 'addSubfield' \
               or requestType == 'replaceSubfield' or requestType == 'diffSubfield':
                result = perform_small_request_update_record(requestType, data, uid)
            else:
                result = { 'resultCode': 1, 'resultText': 'Error unknown' }

            return json.dumps(result)

    def __call__(self, req, form):
        """Redirect calls without final slash."""
        redirect_to_url(req, '%s/record/merge/' % CFG_SITE_URL)

