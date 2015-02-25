# -*- coding: utf-8 -*-
#
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

"""WebLinkback - Administrative Interface"""

from invenio.base.i18n import wash_language, gettext_set_language
from invenio.modules.access.engine import acc_authorize_action
from invenio.legacy.webpage import page
from invenio.config import CFG_SITE_URL, CFG_SITE_LANG
from invenio.legacy.webuser import getUid, page_not_authorized, collect_user_info
from invenio.legacy.weblinkback.adminlib import get_navtrail, \
                                        perform_request_index, \
                                        perform_request_display_list, \
                                        perform_request_display_linkbacks, \
                                        perform_moderate_linkback, \
                                        perform_moderate_url
from invenio.legacy.weblinkback.config import CFG_WEBLINKBACK_STATUS, \
                                       CFG_WEBLINKBACK_ACTION_RETURN_CODE


def index(req, ln=CFG_SITE_LANG):
    """
    Menu of admin options
    @param ln: language
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = get_navtrail()
    navtrail_previous_links +=' &gt; <a class="navtrail" href="%s/admin/weblinkback/weblinkbackadmin.py/">' % CFG_SITE_URL
    navtrail_previous_links += _("WebLinkback Admin") + '</a>'

    uid = getUid(req)
    user_info = collect_user_info(req)
    (auth_code, auth_msg) = acc_authorize_action(user_info, 'cfgweblinkback')
    if auth_code:
        return page_not_authorized(req=req, text=auth_msg, navtrail=navtrail_previous_links)
    else:
        return page(title=_("WebLinkback Admin"),
                    body=perform_request_index(ln=ln),
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    req=req)


def lists(req, urlfieldvalue='', returncode=CFG_WEBLINKBACK_ACTION_RETURN_CODE['OK'], ln=CFG_SITE_LANG):
    """
    Display whitelist and blacklist
    @param urlFieldValue: value of the url input field
    @return_code: might indicate errors from a previous action, of CFG_WEBLINKBACK_ACTION_RETURN_CODE
    @param ln: language
    """
    # is passed as a string, must be an integer
    return_code = int(returncode)
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = get_navtrail()
    navtrail_previous_links +=' &gt; <a class="navtrail" href="%s/admin/weblinkback/weblinkbackadmin.py/">' % CFG_SITE_URL
    navtrail_previous_links += _("WebLinkback Admin") + '</a>'

    uid = getUid(req)
    userInfo = collect_user_info(req)
    (auth_code, auth_msg) = acc_authorize_action(userInfo, 'cfgweblinkback')
    if auth_code:
        return page_not_authorized(req=req, text=auth_msg, navtrail=navtrail_previous_links)
    else:
        return page(title=_("Linkback Whitelist/Blacklist Manager"),
                    body=perform_request_display_list(return_code=return_code, url_field_value=urlfieldvalue, ln=ln),
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    req=req)


def moderatelist(req, url, action, listtype=None, ln=CFG_SITE_LANG):
    """
    Add URL to list
    @param url: url
    @param listType: of CFG_WEBLINKBACK_LIST_TYPE
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = get_navtrail()
    navtrail_previous_links +=' &gt; <a class="navtrail" href="%s/admin/weblinkback/weblinkbackadmin.py/">' % CFG_SITE_URL
    navtrail_previous_links += _("WebLinkback Admin") + '</a>'

    user_info = collect_user_info(req)
    (auth_code, auth_msg) = acc_authorize_action(user_info, 'cfgweblinkback')
    if auth_code:
        return page_not_authorized(req=req, text=auth_msg, navtrail=navtrail_previous_links)
    else:
        url_field_value, return_code = perform_moderate_url(req=req, url=url, action=action, list_type=listtype)
        return lists(req=req,
                     urlfieldvalue=url_field_value,
                     returncode=return_code,
                     ln=ln)


def linkbacks(req, status, returncode=CFG_WEBLINKBACK_ACTION_RETURN_CODE['OK'], ln=CFG_SITE_LANG):
    """
    Display linkbacks
    @param ln: language
    @param status: of CFG_WEBLINKBACK_STATUS, currently only CFG_WEBLINKBACK_STATUS['PENDING'] is supported
    """
    return_code = int(returncode)
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = get_navtrail()
    navtrail_previous_links +=' &gt; <a class="navtrail" href="%s/admin/weblinkback/weblinkbackadmin.py/">' % CFG_SITE_URL
    navtrail_previous_links += _("WebLinkback Admin") + '</a>'

    uid = getUid(req)
    user_info = collect_user_info(req)
    (auth_code, auth_msg) = acc_authorize_action(user_info, 'cfgweblinkback')
    if auth_code:
        return page_not_authorized(req=req, text=auth_msg, navtrail=navtrail_previous_links)
    else:
        return page(title=_("Pending Linkbacks"),
                    body=perform_request_display_linkbacks(return_code=return_code, status=status, ln=ln),
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    req=req)


def moderatelinkback(req, action, linkbackid, ln=CFG_SITE_LANG):
    """
    Moderate linkbacks
    @param linkbackId: linkback id
    @param action: of CFG_WEBLINKBACK_ADMIN_MODERATION_ACTION
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail_previous_links = get_navtrail()
    navtrail_previous_links +=' &gt; <a class="navtrail" href="%s/admin/weblinkback/weblinkbackadmin.py/">' % CFG_SITE_URL
    navtrail_previous_links += _("WebLinkback Admin") + '</a>'

    user_info = collect_user_info(req)
    (auth_code, auth_msg) = acc_authorize_action(user_info, 'cfgweblinkback')
    if auth_code:
        return page_not_authorized(req=req, text=auth_msg, navtrail=navtrail_previous_links)
    else:
        return_code = perform_moderate_linkback(req=req, linkbackid=linkbackid, action=action)
        return linkbacks(req=req,
                         status=CFG_WEBLINKBACK_STATUS['PENDING'],
                         returncode=return_code,
                         ln=ln)
