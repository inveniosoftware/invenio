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

"""WebLinkback - Administrative Lib"""

from invenio.config import CFG_SITE_LANG, CFG_SITE_URL
from invenio.utils.url import wash_url_argument
from invenio.base.i18n import gettext_set_language, wash_language
from invenio.legacy.webuser import collect_user_info
from invenio.legacy.weblinkback.db_layer import get_all_linkbacks, \
                                        approve_linkback,\
                                        reject_linkback, \
                                        remove_url, \
                                        add_url_to_list, \
                                        url_exists, \
                                        get_urls,\
                                        get_url_title
from invenio.legacy.weblinkback.config import CFG_WEBLINKBACK_ORDER_BY_INSERTION_TIME, \
                                       CFG_WEBLINKBACK_ADMIN_MODERATION_ACTION, \
                                       CFG_WEBLINKBACK_STATUS, \
                                       CFG_WEBLINKBACK_ACTION_RETURN_CODE
from invenio.legacy.bibrank.adminlib import addadminbox, \
                                    tupletotable
from invenio.utils.date import convert_datetext_to_dategui
from invenio.modules.formatter import format_record

import cgi
import urllib

import invenio.legacy.template
weblinkback_templates = invenio.legacy.template.load('weblinkback')


def get_navtrail(previous = '', ln=CFG_SITE_LANG):
    """Get the navtrail"""
    previous = wash_url_argument(previous, 'str')
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail = """<a class="navtrail" href="%s/help/admin">%s</a> """ % (CFG_SITE_URL, _("Admin Area"))
    navtrail = navtrail + previous
    return navtrail


def perform_request_index(ln=CFG_SITE_LANG):
    """
    Display main admin page
    """
    return weblinkback_templates.tmpl_admin_index(ln)


def perform_request_display_list(return_code, url_field_value, ln=CFG_SITE_LANG):
    """
    Display a list
    @param return_code: might indicate errors from a previous action, of CFG_WEBLINKBACK_ACTION_RETURN_CODE
    @param url_field_value: value of the url text field
    """
    _ = gettext_set_language(ln)
    urls = get_urls()
    entries = []
    for url in urls:
        entries.append(('<a href="%s">%s</a>' % (cgi.escape(url[0]), cgi.escape(url[0])),
                        url[1].lower(),
                        '<a href="moderatelist?url=%s&action=%s&ln=%s">%s</a>' % (urllib.quote(url[0]), CFG_WEBLINKBACK_ADMIN_MODERATION_ACTION['DELETE'], ln, CFG_WEBLINKBACK_ADMIN_MODERATION_ACTION['DELETE'].lower())))

    header = ['URL', 'List', '']

    error_message = ""
    if return_code != CFG_WEBLINKBACK_ACTION_RETURN_CODE['OK']:
        error_message = _("Unknown error")
        if return_code == CFG_WEBLINKBACK_ACTION_RETURN_CODE['DUPLICATE']:
            error_message = _("The URL already exists in one of the lists")
        elif return_code == CFG_WEBLINKBACK_ACTION_RETURN_CODE['INVALID_ACTION']:
            error_message = _("Invalid action")
        elif return_code == CFG_WEBLINKBACK_ACTION_RETURN_CODE['BAD_INPUT']:
            error_message = _("Invalid URL, might contain spaces")

    error_message_html = ""
    if error_message != "":
        error_message_html = "<dt><b><font color=red>" + error_message + "</font></b></dt>" + "<br>"

    out = """
    <dl>
    %(error_message)s
    <dt>%(whitelist)s</dt>
    <dd>%(whitelistText)s</dd>
    <dt>%(blacklist)s</dt>
    <dd>%(blacklistText)s</dd>
    <dt>%(explanation)s</dt>

    </dl>
    <table class="admin_wvar" cellspacing="0">
    <tr><td>
    <form action='moderatelist'>
    URL:
    <input type="text" name="url" value="%(url)s" />
    <input type="hidden" name="action" value="%(action)s" />
    <select name="listtype" size="1">
    <option value=whitelist>whitelist</option>
    <option value=blacklist>blacklist</option>
    </select>
    <input type="submit" class="adminbutton" value="%(buttonText)s">
    </form>
    </td></tr></table>
    """ % {'whitelist': _('Whitelist'),
           'whitelistText': _('linkback requests from these URLs will be approved automatically.'),
           'blacklist': _('Blacklist'),
           'blacklistText': _('linkback requests from these URLs will be refused automatically, no data will be saved.'),
           'explanation': _('All URLs in these lists are checked for containment (infix) in any linkback request URL. A whitelist match has precedence over a blacklist match.'),
           'url': cgi.escape(url_field_value),
           'action': CFG_WEBLINKBACK_ADMIN_MODERATION_ACTION['INSERT'],
           'buttonText': _('Add URL'),
           'error_message': error_message_html}

    if entries:
        out += tupletotable(header=header, tuple=entries, highlight_rows_p=True,
                            alternate_row_colors_p=True)
    else:
        out += "<i>%s</i>" % _('There are no URLs in both lists.')

    return addadminbox('<b>%s</b>'% _("Reduce the amount of future pending linkback requests"), [out])


def perform_moderate_url(req, url, action, list_type):
    """
    Perform a url action
    @param url
    @param action: CFG_WEBLINKBACK_ADMIN_MODERATION_ACTION['INSERT'] or CFG_WEBLINKBACK_ADMIN_MODERATION_ACTION['DELETE']
    @param list_type: of CFG_WEBLINKBACK_LIST_TYPE
    @return (String, CFG_WEBLINKBACK_ACTION_RETURN_CODE) the String is url if CFG_WEBLINKBACK_ACTION_RETURN_CODE['BAD_INPUT')
    """
    if url == '' or ' ' in url:
        return (url, CFG_WEBLINKBACK_ACTION_RETURN_CODE['BAD_INPUT'])
    elif action == CFG_WEBLINKBACK_ADMIN_MODERATION_ACTION['INSERT']:
        if url_exists(url):
            return ('', CFG_WEBLINKBACK_ACTION_RETURN_CODE['DUPLICATE'])
        else:
            add_url_to_list(url, list_type, collect_user_info(req))
    elif action == CFG_WEBLINKBACK_ADMIN_MODERATION_ACTION['DELETE']:
        remove_url(url)
    else:
        return ('', CFG_WEBLINKBACK_ACTION_RETURN_CODE['INVALID_ACTION'])

    return ('', CFG_WEBLINKBACK_ACTION_RETURN_CODE['OK'])


def perform_request_display_linkbacks(status, return_code, ln=CFG_SITE_LANG):
    """
    Display linkbacks
    @param status: of CFG_WEBLINKBACK_STATUS, currently only CFG_WEBLINKBACK_STATUS['PENDING'] is supported
    """
    _ = gettext_set_language(ln)
    if status == CFG_WEBLINKBACK_STATUS['PENDING']:
        linkbacks = get_all_linkbacks(status=status, order=CFG_WEBLINKBACK_ORDER_BY_INSERTION_TIME['DESC'])
        entries = []

        for (linkbackid, origin_url, recid, additional_properties, linkback_type, linkback_status, insert_time) in linkbacks: # pylint: disable=W0612
            moderation_prefix = '<a href="moderatelinkback?action=%%s&linkbackid=%s&ln=%s">%%s</a>' % (linkbackid, ln)
            entries.append((linkback_type,
                            format_record(recID=recid, of='hs', ln=ln),
                            '<a href="%s">%s</a>' % (cgi.escape(origin_url), cgi.escape(get_url_title(origin_url))),
                            convert_datetext_to_dategui(str(insert_time)),
                            moderation_prefix % (CFG_WEBLINKBACK_ADMIN_MODERATION_ACTION['APPROVE'], 'Approve') + " / " + moderation_prefix % (CFG_WEBLINKBACK_ADMIN_MODERATION_ACTION['REJECT'], 'Reject')))

        header = ['Linkback type', 'Record', 'Origin', 'Submitted on', '']

        error_message = ""
        if return_code != CFG_WEBLINKBACK_ACTION_RETURN_CODE['OK']:
            error_message = _("Unknown error")
            if return_code == CFG_WEBLINKBACK_ACTION_RETURN_CODE['INVALID_ACTION']:
                error_message = _("Invalid action")

        error_message_html = ""
        if error_message != "":
            error_message_html = "<dt><b><font color=red>" + error_message + "</font></b></dt>" + "<br>"

        out = """
        <dl>
        %(error_message)s
        <dt>%(heading)s</dt>
        <dd>%(description)s</dd>
        </dl>
        """ % {'heading': _("Pending linkbacks"),
               'description': _("these linkbacks are not visible to users, they must be approved or rejected."),
               'error_message': error_message_html}

        if entries:
            out += tupletotable(header=header, tuple=entries, highlight_rows_p=True,
                                alternate_row_colors_p=True)
        else:
            out += "<i>There are no %s linkbacks.</i>" % status.lower()

        return addadminbox('<b>%s</b>'% _("Reduce the amount of currently pending linkback requests"), [out])
    else:
        return "<i>%s</i>" % _('Currently only pending linkbacks are supported.')


def perform_moderate_linkback(req, linkbackid, action):
    """
    Moderate linkbacks
    @param linkbackid: linkback id
    @param action: of CFG_WEBLINKBACK_ADMIN_MODERATION_ACTION
    @return CFG_WEBLINKBACK_ACTION_RETURN_CODE
    """
    if action == CFG_WEBLINKBACK_ADMIN_MODERATION_ACTION['APPROVE']:
        approve_linkback(linkbackid, collect_user_info(req))
    elif action == CFG_WEBLINKBACK_ADMIN_MODERATION_ACTION['REJECT']:
        reject_linkback(linkbackid, collect_user_info(req))
    else:
        return CFG_WEBLINKBACK_ACTION_RETURN_CODE['INVALID_ACTION']

    return CFG_WEBLINKBACK_ACTION_RETURN_CODE['OK']
