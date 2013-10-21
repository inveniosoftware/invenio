## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011 CERN.
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
"""Invenio BibEdit Administrator Interface."""

__revision__ = "$Id"

__lastupdated__ = """$Date: 2008/08/12 09:26:46 $"""

import cProfile
import cStringIO
import pstats

from invenio.jsonutils import json, json_unicode_to_utf8
from invenio.access_control_engine import acc_authorize_action
from invenio.bibedit_engine import (perform_request_ajax,
                                    perform_request_init,
                                    perform_request_newticket,
                                    perform_request_compare,
                                    perform_request_init_template_interface,
                                    perform_request_ajax_template_interface)
from invenio.bibedit_utils import user_can_edit_record_collection
from invenio.config import CFG_SITE_LANG, CFG_SITE_SECURE_URL, CFG_SITE_RECORD
from invenio.messages import gettext_set_language
from invenio.urlutils import redirect_to_url
from invenio.webinterface_handler import WebInterfaceDirectory, wash_urlargd
from invenio.webpage import page
from invenio.webuser import collect_user_info, getUid, page_not_authorized

navtrail = (' <a class="navtrail" href=\"%s/help/admin\">Admin Area</a> '
            ) % CFG_SITE_SECURE_URL
navtrail_bibedit = (' <a class="navtrail" href=\"%s/help/admin\">Admin Area</a> ' + \
                    ' &gt; <a class="navtrail" href=\"%s/%s/edit\">Record Editor</a>'
            ) % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, CFG_SITE_RECORD)


def wrap_json_req_profiler(func):

    def json_req_profiler(self, req, form):
        if "ajaxProfile" in form:
            profiler = cProfile.Profile()
            return_val = profiler.runcall(func, self, req, form)

            results = cStringIO.StringIO()
            stats = pstats.Stats(profiler, stream=results)
            stats.sort_stats('cumulative')
            stats.print_stats(100)

            json_in = json.loads(str(form['jsondata']))
            # Deunicode all strings (Invenio doesn't have unicode
            # support).
            json_in = json_unicode_to_utf8(json_in)

            json_data = json.loads(return_val)
            json_data.update({"profilerStats": "<pre style='overflow: scroll'>" + json_in['requestType'] + results.getvalue() + "</pre>"})
            return json.dumps(json_data)
        else:
            return func(self, req, form)

    return json_req_profiler

class WebInterfaceEditPages(WebInterfaceDirectory):
    """Defines the set of /edit pages."""

    _exports = ['', 'new_ticket', 'compare_revisions', 'templates']

    def __init__(self, recid=None):
        """Initialize."""
        self.recid = recid

    @wrap_json_req_profiler
    def index(self, req, form):
        """Handle all BibEdit requests.
        The responsibilities of this functions is:
        * JSON decoding and encoding.
        * Redirection, if necessary.
        * Authorization.
        * Calling the appropriate function from the engine.

        """
        uid = getUid(req)
        argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG)})

        # If it is an Ajax request, extract any JSON data.
        ajax_request, recid = False, None
        if form.has_key('jsondata'):
            json_data = json.loads(str(form['jsondata']))
            # Deunicode all strings (Invenio doesn't have unicode
            # support).
            json_data = json_unicode_to_utf8(json_data)
            ajax_request = True
            if json_data.has_key('recID'):
                recid = json_data['recID']
            json_response = {'resultCode': 0, 'ID': json_data['ID']}

        # Authorization.
        user_info = collect_user_info(req)
        if user_info['email'] == 'guest':
            # User is not logged in.
            if not ajax_request:
                # Do not display the introductory recID selection box to guest
                # users (as it used to be with v0.99.0):
                auth_code, auth_message = acc_authorize_action(req,
                                                               'runbibedit')
                referer = '/edit/'
                if self.recid:
                    referer = '/%s/%s/edit/' % (CFG_SITE_RECORD, self.recid)
                return page_not_authorized(req=req, referer=referer,
                                           text=auth_message, navtrail=navtrail)
            else:
                # Session has most likely timed out.
                json_response.update({'resultCode': 100})
                return json.dumps(json_response)

        elif self.recid:
            # Handle redirects from /record/<record id>/edit
            # generic URL.
            redirect_to_url(req, '%s/%s/edit/#state=edit&recid=%s&recrev=%s' % (
                    CFG_SITE_SECURE_URL, CFG_SITE_RECORD, self.recid, ""))

        elif recid is not None:
            json_response.update({'recID': recid})
            if json_data['requestType'] == "getRecord":
                # Authorize access to record.
                if not user_can_edit_record_collection(req, recid):
                    json_response.update({'resultCode': 101})
                    return json.dumps(json_response)

        # Handle request.
        if not ajax_request:
            # Show BibEdit start page.
            body, errors, warnings = perform_request_init(uid, argd['ln'], req, __lastupdated__)
            title = 'Record Editor'
            return page(title       = title,
                        body        = body,
                        errors      = errors,
                        warnings    = warnings,
                        uid         = uid,
                        language    = argd['ln'],
                        navtrail    = navtrail,
                        lastupdated = __lastupdated__,
                        req         = req,
                        body_css_classes = ['bibedit'])
        else:
            # Handle AJAX request.
            json_response.update(perform_request_ajax(req, recid, uid,
                                                      json_data))
            return json.dumps(json_response)

    def compare_revisions(self, req, form):
        """Handle the compare revisions request"""
        argd = wash_urlargd(form, { \
                'ln': (str, CFG_SITE_LANG), \
                'rev1' : (str, ''), \
                'rev2' : (str, ''), \
                'recid': (int, 0)})

        ln = argd['ln']
        uid = getUid(req)
        _ = gettext_set_language(ln)

        # Checking if currently logged user has permission to perform this request

        auth_code, auth_message = acc_authorize_action(req, 'runbibedit')
        if auth_code != 0:
            return page_not_authorized(req=req, referer="/edit",
                                       text=auth_message, navtrail=navtrail)
        recid = argd['recid']
        rev1 = argd['rev1']
        rev2 = argd['rev2']
        ln = argd['ln']

        body, errors, warnings = perform_request_compare(ln, recid, rev1, rev2)

        return page(title = _("Comparing two record revisions"),
                    body =  body,
                    errors = errors,
                    warnings = warnings,
                    uid = uid,
                    language = ln,
                    navtrail    = navtrail,
                    lastupdated = __lastupdated__,
                    req         = req,
                    body_css_classes = ['bibedit'])

    def new_ticket(self, req, form):
        """handle a edit/new_ticket request"""
        argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG), 'recid': (int, 0)})
        ln = argd['ln']
        _ = gettext_set_language(ln)
        auth_code, auth_message = acc_authorize_action(req, 'runbibedit')
        if auth_code != 0:
            return page_not_authorized(req=req, referer="/edit",
                                       text=auth_message, navtrail=navtrail)
        uid = getUid(req)
        if argd['recid']:
            (errmsg, url) = perform_request_newticket(argd['recid'], uid)
            if errmsg:
                return page(title       = _("Failed to create a ticket"),
                            body        = _("Error")+": "+errmsg,
                            errors      = [],
                            warnings    = [],
                            uid         = uid,
                            language    = ln,
                            navtrail    = navtrail,
                            lastupdated = __lastupdated__,
                            req         = req,
                            body_css_classes = ['bibedit'])
            else:
                #redirect..
                redirect_to_url(req, url)

    def templates(self, req, form):
        """handle a edit/templates request"""
        uid = getUid(req)
        argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG)})

        # If it is an Ajax request, extract any JSON data.
        ajax_request = False
        if form.has_key('jsondata'):
            json_data = json.loads(str(form['jsondata']))
            # Deunicode all strings (Invenio doesn't have unicode
            # support).
            json_data = json_unicode_to_utf8(json_data)
            ajax_request = True
            json_response = {'resultCode': 0}

        # Authorization.
        user_info = collect_user_info(req)
        if user_info['email'] == 'guest':
            # User is not logged in.
            if not ajax_request:
                # Do not display the introductory recID selection box to guest
                # users (as it used to be with v0.99.0):
                dummy_auth_code, auth_message = acc_authorize_action(req,
                                                                     'runbibedit')
                referer = '/edit'
                return page_not_authorized(req=req, referer=referer,
                                           text=auth_message, navtrail=navtrail)
            else:
                # Session has most likely timed out.
                json_response.update({'resultCode': 100})
                return json.dumps(json_response)
        # Handle request.
        if not ajax_request:
            # Show BibEdit template management start page.
            body, errors, warnings = perform_request_init_template_interface()
            title = 'Record Editor Template Manager'
            return page(title       = title,
                        body        = body,
                        errors      = errors,
                        warnings    = warnings,
                        uid         = uid,
                        language    = argd['ln'],
                        navtrail    = navtrail_bibedit,
                        lastupdated = __lastupdated__,
                        req         = req,
                        body_css_classes = ['bibedit'])
        else:
            # Handle AJAX request.
            json_response.update(perform_request_ajax_template_interface(json_data))
            return json.dumps(json_response)

    def __call__(self, req, form):
        """Redirect calls without final slash."""
        if self.recid:
            redirect_to_url(req, '%s/%s/%s/edit/' % (CFG_SITE_SECURE_URL,
                                                         CFG_SITE_RECORD,
                                                         self.recid))
        else:
            redirect_to_url(req, '%s/%s/edit/' % (CFG_SITE_SECURE_URL, CFG_SITE_RECORD))
