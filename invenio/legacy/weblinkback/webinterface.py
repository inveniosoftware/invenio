# -*- coding: utf-8 -*-
# Comments and reviews for records.

# This file is part of Invenio.
# Copyright (C) 2011 CERN.
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

"""WebLinkback - Web Interface"""

from six import iteritems

from invenio.base.i18n import gettext_set_language
from invenio.ext.legacy.handler import wash_urlargd, WebInterfaceDirectory
from invenio.legacy.webuser import getUid, collect_user_info, page_not_authorized
from invenio.legacy.weblinkback.api import check_user_can_view_linkbacks, \
                                perform_sendtrackback, \
                                perform_request_display_record_linbacks, \
                                perform_request_display_approved_latest_added_linkbacks_to_accessible_records, \
                                perform_sendtrackback_disabled
from invenio.legacy.weblinkback.db_layer import approve_linkback, \
                                        reject_linkback
from invenio.legacy.weblinkback.config import CFG_WEBLINKBACK_LATEST_COUNT_DEFAULT, \
                                       CFG_WEBLINKBACK_SUBSCRIPTION_DEFAULT_ARGUMENT_NAME
from invenio.utils.url import redirect_to_url, make_canonical_urlargd
from invenio.config import CFG_SITE_URL, \
                           CFG_SITE_SECURE_URL, \
                           CFG_SITE_LANG, \
                           CFG_SITE_RECORD, \
                           CFG_WEBLINKBACK_TRACKBACK_ENABLED
from invenio.legacy.search_engine import guess_primary_collection_of_a_record, \
                                  create_navtrail_links
from invenio.legacy.webpage import pageheaderonly, pagefooteronly
from invenio.legacy.websearch.adminlib import get_detailed_page_tabs
from invenio.modules.access.engine import acc_authorize_action
from invenio.modules.collections.models import Collection

import invenio.legacy.template
webstyle_templates = invenio.legacy.template.load('webstyle')
websearch_templates = invenio.legacy.template.load('websearch')
weblinkback_templates = invenio.legacy.template.load('weblinkback')


class WebInterfaceRecordLinkbacksPages(WebInterfaceDirectory):
    """Define the set of record/number/linkbacks pages."""

    _exports = ['', 'display', 'index', 'approve', 'reject', 'sendtrackback']

    def __init__(self, recid = -1):
        self.recid = recid

    def index(self, req, form):
        """
        Redirect to display function
        """
        return self.display(req, form)

    def display(self, req, form):
        """
        Display the linkbacks of a record and admin approve/reject features
        """
        argd = wash_urlargd(form, {})

        _ = gettext_set_language(argd['ln'])

        # Check authorization
        uid = getUid(req)
        user_info = collect_user_info(req)

        (auth_code, auth_msg) = check_user_can_view_linkbacks(user_info, self.recid)
        if auth_code and user_info['email'] == 'guest':
            # Ask to login
            target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                     make_canonical_urlargd({'ln': argd['ln'],
                                             'referer': CFG_SITE_URL + user_info['uri']}, {})
            return redirect_to_url(req, target)
        elif auth_code:
            return page_not_authorized(req,
                                       referer="../",
                                       uid=uid,
                                       text=auth_msg,
                                       ln=argd['ln'])

        show_admin = False
        (auth_code, auth_msg) = acc_authorize_action(req, 'moderatelinkbacks', collection = guess_primary_collection_of_a_record(self.recid))
        if not auth_code:
            show_admin = True

        body = perform_request_display_record_linbacks(req, self.recid, show_admin, weblinkback_templates=weblinkback_templates, ln=argd['ln'])

        title = websearch_templates.tmpl_record_page_header_content(req, self.recid, argd['ln'])[0]

        # navigation, tabs, top and bottom part
        navtrail = create_navtrail_links(cc=guess_primary_collection_of_a_record(self.recid), ln=argd['ln'])
        if navtrail:
            navtrail += ' &gt; '
        navtrail += '<a class="navtrail" href="%s/%s/%s?ln=%s">'% (CFG_SITE_URL, CFG_SITE_RECORD, self.recid, argd['ln'])
        navtrail += title
        navtrail += '</a>'
        navtrail += ' &gt; <a class="navtrail">Linkbacks</a>'

        mathjaxheader, jqueryheader = weblinkback_templates.tmpl_get_mathjaxheader_jqueryheader()

        col_id = Collection.query.filter_by(
            name=guess_primary_collection_of_a_record(self.recid)).value('id')
        unordered_tabs = get_detailed_page_tabs(col_id, self.recid,
                                                ln=argd['ln'])
        ordered_tabs_id = [(tab_id, values['order']) for (tab_id, values) in iteritems(unordered_tabs)]
        ordered_tabs_id.sort(lambda x, y: cmp(x[1], y[1]))
        link_ln = ''
        if argd['ln'] != CFG_SITE_LANG:
            link_ln = '?ln=%s' % argd['ln']
        tabs = [(unordered_tabs[tab_id]['label'], \
                     '%s/%s/%s/%s%s' % (CFG_SITE_URL, CFG_SITE_RECORD, self.recid, tab_id, link_ln), \
                     tab_id in ['linkbacks'],
                     unordered_tabs[tab_id]['enabled']) \
                     for (tab_id, values) in ordered_tabs_id
                     if unordered_tabs[tab_id]['visible'] == True]
        top = webstyle_templates.detailed_record_container_top(self.recid,
                                                              tabs,
                                                              argd['ln'])
        bottom = webstyle_templates.detailed_record_container_bottom(self.recid,
                                                                    tabs,
                                                                    argd['ln'])

        return pageheaderonly(title=title,
                              navtrail=navtrail,
                              uid=uid,
                              verbose=1,
                              metaheaderadd = mathjaxheader + jqueryheader,
                              req=req,
                              language=argd['ln'],
                              navmenuid='search',
                              navtrail_append_title_p=0) + \
                              websearch_templates.tmpl_search_pagestart(argd['ln']) + \
               top + body + bottom + \
               websearch_templates.tmpl_search_pageend(argd['ln']) + \
               pagefooteronly(language=argd['ln'], req=req)

    # Return the same page whether we ask for /CFG_SITE_RECORD/123/linkbacks or /CFG_SITE_RECORD/123/linkbacks/
    __call__ = index

    def approve(self, req, form):
        """
        Approve a linkback
        """
        argd = wash_urlargd(form, {'linkbackid': (int, -1)})

        authorization = self.check_authorization_moderatelinkbacks(req, argd)
        if not authorization:
            approve_linkback(argd['linkbackid'], collect_user_info(req))
            return self.display(req, form)
        else:
            return authorization

    def reject(self, req, form):
        """
        Reject a linkback
        """
        argd = wash_urlargd(form, {'linkbackid': (int, -1)})

        authorization = self.check_authorization_moderatelinkbacks(req, argd)
        if not authorization:
            reject_linkback(argd['linkbackid'], collect_user_info(req))
            return self.display(req, form)
        else:
            return authorization

    def check_authorization_moderatelinkbacks(self, req, argd):
        """
        Check if user has authorization moderate linkbacks
        @return if yes: nothing, if guest: login redirect, otherwise page_not_authorized
        """
        # Check authorization
        uid = getUid(req)
        user_info = collect_user_info(req)

        (auth_code, auth_msg) = acc_authorize_action(req, 'moderatelinkbacks', collection = guess_primary_collection_of_a_record(self.recid))
        if auth_code and user_info['email'] == 'guest':
            # Ask to login
            target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                     make_canonical_urlargd({'ln': argd['ln'],
                                             'referer': CFG_SITE_URL + user_info['uri']}, {})
            return redirect_to_url(req, target)
        elif auth_code:
            return page_not_authorized(req,
                                       referer="../",
                                       uid=uid,
                                       text=auth_msg,
                                       ln=argd['ln'])

    def sendtrackback(self, req, form):
        """
        Send a new trackback
        """
        if CFG_WEBLINKBACK_TRACKBACK_ENABLED:
            argd = wash_urlargd(form, {'url': (str, CFG_WEBLINKBACK_SUBSCRIPTION_DEFAULT_ARGUMENT_NAME),
                                       'title': (str, CFG_WEBLINKBACK_SUBSCRIPTION_DEFAULT_ARGUMENT_NAME),
                                       'excerpt': (str, CFG_WEBLINKBACK_SUBSCRIPTION_DEFAULT_ARGUMENT_NAME),
                                       'blog_name': (str, CFG_WEBLINKBACK_SUBSCRIPTION_DEFAULT_ARGUMENT_NAME),
                                       'id': (str, CFG_WEBLINKBACK_SUBSCRIPTION_DEFAULT_ARGUMENT_NAME),
                                       'source': (str, CFG_WEBLINKBACK_SUBSCRIPTION_DEFAULT_ARGUMENT_NAME),
                                       })

            perform_sendtrackback(req, self.recid, argd['url'], argd['title'], argd['excerpt'], argd['blog_name'], argd['id'], argd['source'], argd['ln'])
        else:
            perform_sendtrackback_disabled(req)


class WebInterfaceRecentLinkbacksPages(WebInterfaceDirectory):
    """Define the set of global /linkbacks pages."""

    _exports = ['', 'display', 'index']

    def index(self, req, form):
        """
        Redirect to display function
        """
        return self.display(req, form)

    def display(self, req, form):
        """
        Display approved latest added linkbacks of the invenio instance
        """
        argd = wash_urlargd(form, {'rg': (int, CFG_WEBLINKBACK_LATEST_COUNT_DEFAULT)})
        # count must be positive
        if argd['rg'] < 0:
            argd['rg'] = -argd['rg']

        _ = gettext_set_language(argd['ln'])

        user_info = collect_user_info(req)

        body = perform_request_display_approved_latest_added_linkbacks_to_accessible_records(argd['rg'], argd['ln'], user_info, weblinkback_templates=weblinkback_templates)

        navtrail = 'Recent Linkbacks'

        mathjaxheader, jqueryheader = weblinkback_templates.tmpl_get_mathjaxheader_jqueryheader()

        return pageheaderonly(title=navtrail,
                              navtrail=navtrail,
                              verbose=1,
                              metaheaderadd = mathjaxheader + jqueryheader,
                              req=req,
                              language=argd['ln'],
                              navmenuid='search',
                              navtrail_append_title_p=0) + \
                              websearch_templates.tmpl_search_pagestart(argd['ln']) + \
               body + \
               websearch_templates.tmpl_search_pageend(argd['ln']) + \
               pagefooteronly(language=argd['ln'], req=req)

    # Return the same page whether we ask for /linkbacks or /linkbacks/
    __call__ = index
