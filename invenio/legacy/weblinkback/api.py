# -*- coding: utf-8 -*-

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

"""WebLinkback - Handling Linkbacks"""

from invenio.config import CFG_SITE_URL, \
                           CFG_SITE_RECORD, \
                           CFG_SITE_ADMIN_EMAIL, \
                           CFG_SITE_LANG
from invenio.legacy.weblinkback.config import CFG_WEBLINKBACK_TYPE, \
                                       CFG_WEBLINKBACK_SUBSCRIPTION_DEFAULT_ARGUMENT_NAME, \
                                       CFG_WEBLINKBACK_STATUS, \
                                       CFG_WEBLINKBACK_ORDER_BY_INSERTION_TIME, \
                                       CFG_WEBLINKBACK_LIST_TYPE, \
                                       CFG_WEBLINKBACK_TRACKBACK_SUBSCRIPTION_ERROR_MESSAGE, \
                                       CFG_WEBLINKBACK_PAGE_TITLE_STATUS, \
                                       CFG_WEBLINKBACK_BROKEN_COUNT, \
                                       CFG_WEBLINKBACK_LATEST_FACTOR, \
                                       CFG_WEBLINKBACK_MAX_LINKBACKS_IN_EMAIL
from invenio.legacy.weblinkback.db_layer import create_linkback, \
                                        get_url_list, \
                                        get_all_linkbacks, \
                                        get_approved_latest_added_linkbacks, \
                                        approve_linkback, \
                                        get_urls_and_titles, \
                                        update_url_title, \
                                        set_url_broken, \
                                        increment_broken_count, \
                                        remove_linkback
from invenio.legacy.search_engine import check_user_can_view_record, \
                                  guess_primary_collection_of_a_record
from invenio.modules.access.engine import acc_authorize_action, \
                                          acc_get_authorized_emails
from invenio.legacy.webuser import collect_user_info
from invenio.ext.email import send_email
from invenio.utils.url import get_title_of_page


def check_user_can_view_linkbacks(user_info, recid):
    """
    Check if the user is authorized to view linkbacks for a given recid.
    Returns the same type as acc_authorize_action
    """
    # check user cannot view the record itself
    (auth_code, auth_msg) = check_user_can_view_record(user_info, recid)
    if auth_code:
        return (auth_code, auth_msg)

    # check if user can view the linkbacks
    record_primary_collection = guess_primary_collection_of_a_record(recid)
    return acc_authorize_action(user_info, 'viewlinkbacks', authorized_if_no_roles=True, collection=record_primary_collection)


def generate_redirect_url(recid, ln=CFG_SITE_LANG, action = None):
    """
    Get redirect URL for an action
    @param action: the action, must be defined in weblinkback_webinterface.py
    @return "CFG_SITE_URL/CFG_SITE_RECORD/recid/linkbacks/action?ln=%s" if action != None,
        otherwise CFG_SITE_URL/CFG_SITE_RECORD/recid/linkbacks?ln=%s
    """

    result = "%s/%s/%s/linkbacks" % (CFG_SITE_URL, CFG_SITE_RECORD, recid)

    if action != None:
        return result + "/%s?ln=%s" % (action, ln)
    else:
        return result + "?ln=%s" % ln


def split_in_days(linkbacks):
    """
    Split linkbacks in days
    @param linkbacks: a list of this format: [(linkback_id,
                                              origin_url,
                                              recid,
                                              additional_properties,
                                              type,
                                              status,
                                              insert_time)]
                                              in ascending or descending order by insert_time
    @return a list of lists of linkbacks
    """
    result = []
    same_day_list = []
    previous_date = None
    current_date = None
    for i in range(len(linkbacks)):
        current_linkback = linkbacks[i]
        previous_date = None
        if i > 0:
            previous_date = current_date
        else:
            previous_date = current_linkback[6]

        current_date = current_linkback[6]

        # same day --> same group
        if (current_date.year == previous_date.year and
            current_date.month == previous_date.month and
            current_date.day == previous_date.day):
            same_day_list.append(current_linkback)
        else:
            result.append(same_day_list)
            same_day_list = []
            same_day_list.append(current_linkback)

    # add last group if non-empty
    if same_day_list:
        result.append(same_day_list)

    return result


def create_trackback(recid, url, title, excerpt, blog_name, blog_id, source, user_info):
    """
    Create a trackback
    @param recid
    """
    # copy optional arguments
    argument_copy = {}
    if title != CFG_WEBLINKBACK_SUBSCRIPTION_DEFAULT_ARGUMENT_NAME:
        argument_copy['title'] = title
    if excerpt != CFG_WEBLINKBACK_SUBSCRIPTION_DEFAULT_ARGUMENT_NAME:
        argument_copy['excerpt'] = excerpt
    if blog_name != CFG_WEBLINKBACK_SUBSCRIPTION_DEFAULT_ARGUMENT_NAME:
        argument_copy['blog_name'] = blog_name
    if blog_id != CFG_WEBLINKBACK_SUBSCRIPTION_DEFAULT_ARGUMENT_NAME:
        argument_copy['id'] = blog_id
    if source != CFG_WEBLINKBACK_SUBSCRIPTION_DEFAULT_ARGUMENT_NAME:
        argument_copy['source'] = source

    additional_properties = ""
    if len(argument_copy) > 0:
        additional_properties = argument_copy

    return create_linkback(url, recid, additional_properties, CFG_WEBLINKBACK_TYPE['TRACKBACK'], user_info)


def send_pending_linkbacks_notification(linkback_type):
    """
    Send notification emails to all linkback moderators for all pending linkbacks
    @param linkback_type: of CFG_WEBLINKBACK_LIST_TYPE
    """
    pending_linkbacks = get_all_linkbacks(linkback_type=CFG_WEBLINKBACK_TYPE['TRACKBACK'], status=CFG_WEBLINKBACK_STATUS['PENDING'])

    if pending_linkbacks:
        pending_count = len(pending_linkbacks)
        cutoff_text = ''
        if pending_count > CFG_WEBLINKBACK_MAX_LINKBACKS_IN_EMAIL:
            cutoff_text = ' (Printing only the first %s requests)' % CFG_WEBLINKBACK_MAX_LINKBACKS_IN_EMAIL

        content = """There are %(count)s new %(linkback_type)s requests which you should approve or reject%(cutoff)s:
                  """ % {'count': pending_count,
                         'linkback_type': linkback_type,
                         'cutoff': cutoff_text}

        for pending_linkback in pending_linkbacks[0:CFG_WEBLINKBACK_MAX_LINKBACKS_IN_EMAIL]:
            content += """
                       For %(recordURL)s from %(origin_url)s.
                       """ % {'recordURL': generate_redirect_url(pending_linkback[2]),
                              'origin_url': pending_linkback[1]}

        for email in acc_get_authorized_emails('moderatelinkbacks'):
            send_email(CFG_SITE_ADMIN_EMAIL, email, 'Pending ' + linkback_type + ' requests', content)


def infix_exists_for_url_in_list(url, list_type):
    """
    Check if an infix of a url exists in a list
    @param url
    @param list_type, of CFG_WEBLINKBACK_LIST_TYPE
    @return True, False
    """
    urls = get_url_list(list_type)
    for current_url in urls:
        if current_url in url:
            return True
    return False


def get_latest_linkbacks_to_accessible_records(rg, linkbacks, user_info):
    result = []
    for linkback in linkbacks:
        (auth_code, auth_msg) = check_user_can_view_record(user_info, linkback[2]) # pylint: disable=W0612
        if not auth_code:
            result.append(linkback)
            if len(result) == rg:
                break
    return result


def perform_request_display_record_linbacks(req, recid, show_admin, weblinkback_templates, ln): # pylint: disable=W0613
    """
    Display linkbacks of a record
    @param recid
    @param argd
    @param show_admin: True, False --> show admin parts to approve/reject linkbacks pending requests
    @param weblinkback_templates: template object reference
    """
    out = weblinkback_templates.tmpl_linkbacks_general(recid=recid,
                                                       ln=ln)
    if show_admin:
        pending_linkbacks = get_all_linkbacks(recid, CFG_WEBLINKBACK_STATUS['PENDING'], CFG_WEBLINKBACK_ORDER_BY_INSERTION_TIME['DESC'])
        out += weblinkback_templates.tmpl_linkbacks_admin(pending_linkbacks=pending_linkbacks,
                                                          recid=recid,
                                                          ln=ln)

    approved_linkbacks = get_all_linkbacks(recid, CFG_WEBLINKBACK_STATUS['APPROVED'], CFG_WEBLINKBACK_ORDER_BY_INSERTION_TIME['DESC'])
    out += weblinkback_templates.tmpl_linkbacks(approved_linkbacks=approved_linkbacks,
                                                ln=ln)

    return out


def perform_request_display_approved_latest_added_linkbacks_to_accessible_records(rg, ln, user_info, weblinkback_templates):
    """
    Display approved latest added linbacks to accessible records
    @param rg: count of linkbacks to display
    @param weblinkback_templates: template object reference
    """
    latest_linkbacks = get_approved_latest_added_linkbacks(rg * CFG_WEBLINKBACK_LATEST_FACTOR)
    latest_linkbacks = get_latest_linkbacks_to_accessible_records(rg, latest_linkbacks, user_info)
    latest_linkbacks_in_days = split_in_days(latest_linkbacks)

    out = weblinkback_templates.tmpl_get_latest_linkbacks_top(rg, ln)
    out += '<br>'
    out += weblinkback_templates.tmpl_get_latest_linkbacks(latest_linkbacks_in_days, ln)

    return out


def perform_sendtrackback(recid, url, title, excerpt, blog_name, blog_id, source, current_user):
    """
    Send trackback
    @param recid: recid
    """
    # assume unsuccessful request
    status = 400
    xml_response = '<response>'
    xml_error_response = """<error>1</error>
                             <message>%s</message>
                         """

    blacklist_match = infix_exists_for_url_in_list(url, CFG_WEBLINKBACK_LIST_TYPE['BLACKLIST'])
    whitelist_match = infix_exists_for_url_in_list(url, CFG_WEBLINKBACK_LIST_TYPE['WHITELIST'])

    # faulty request, url argument not set
    if url in (CFG_WEBLINKBACK_SUBSCRIPTION_DEFAULT_ARGUMENT_NAME, None, ''):
        xml_response += xml_error_response % CFG_WEBLINKBACK_TRACKBACK_SUBSCRIPTION_ERROR_MESSAGE['BAD_ARGUMENT']
    # request refused: whitelist match has precedence over blacklist match
    elif blacklist_match and not whitelist_match:
        xml_response += xml_error_response % CFG_WEBLINKBACK_TRACKBACK_SUBSCRIPTION_ERROR_MESSAGE['BLACKLIST']
    # request accepted: will be either approved automatically or pending
    else:
        status = 200
        linkback_id = create_trackback(recid, url, title, excerpt, blog_name, blog_id, source, current_user)
        # approve request automatically from url in whitelist
        if  whitelist_match:
            approve_linkback(linkback_id, current_user)

    xml_response += '</response>'

    return xml_response, status


def perform_sendtrackback_disabled():
    status = 404
    xml_response = """<response>
                      <error>1</error>
                      <message>Trackback facility disabled</message>
                      </response>"""
    return xml_response, status


def update_linkbacks(mode):
    """
    Update titles of pages that link to the instance
    @param mode: 1 update page titles of new linkbacks
                 2 update page titles of old linkbacks
                 3 update manually set page titles
                 4 detect and disable broken linkbacks
    """
    if mode in (1, 2, 3):
        if mode == 1:
            urls_and_titles = get_urls_and_titles(CFG_WEBLINKBACK_PAGE_TITLE_STATUS['NEW'])
        elif mode == 2:
            urls_and_titles = get_urls_and_titles(CFG_WEBLINKBACK_PAGE_TITLE_STATUS['OLD'])
        elif mode == 3:
            urls_and_titles = get_urls_and_titles(CFG_WEBLINKBACK_PAGE_TITLE_STATUS['MANUALLY_SET'])

        for (url, title, manual_set, broken_count) in urls_and_titles: # pylint: disable=W0612
            new_title = get_title_of_page(url)
            # Only accept valid titles
            if new_title != None:
                update_url_title(url, new_title)

    elif mode == 4:
        urls_and_titles = get_urls_and_titles()
        for (url, title, manual_set, broken_count) in urls_and_titles: # pylint: disable=W0612
            new_title = get_title_of_page(url)
            # Broken one detected
            if new_title == None:
                increment_broken_count(url)
                if broken_count + 1 == CFG_WEBLINKBACK_BROKEN_COUNT:
                    set_url_broken(url)


def delete_linkbacks_on_blacklist():
    """
    Delete all rejected, broken and pending linkbacks whose URL on in the blacklist
    """
    linkbacks = list(get_all_linkbacks(status=CFG_WEBLINKBACK_STATUS['PENDING']))
    linkbacks.extend(list(get_all_linkbacks(status=CFG_WEBLINKBACK_STATUS['REJECTED'])))
    linkbacks.extend(list(get_all_linkbacks(status=CFG_WEBLINKBACK_STATUS['BROKEN'])))

    for linkback in linkbacks:
        if infix_exists_for_url_in_list(linkback[1], CFG_WEBLINKBACK_LIST_TYPE['BLACKLIST']):
            remove_linkback(linkback[0])
