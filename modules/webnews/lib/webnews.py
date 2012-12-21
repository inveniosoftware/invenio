# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

""" WebNews module """

__revision__ = "$Id$"

# GENERAL IMPORTS
from cgi import escape
import sys
CFG_JSON_AVAILABLE = True
if sys.hexversion < 0x2060000:
    try:
        import simplejson as json
    except:
        CFG_JSON_AVAILABLE = False
else:
    import json

# GENERAL IMPORTS
from urlparse import urlsplit
import time

# INVENIO IMPORTS
from invenio.config import CFG_SITE_LANG
from invenio.webinterface_handler_wsgi_utils import Cookie, \
                                                    get_cookie
                                                    # INFO: Old API, ignore
                                                    #add_cookies, \
from invenio.messages import gettext_set_language
from invenio.urlutils import get_referer

# MODULE IMPORTS
from invenio.webnews_dblayer import get_latest_story_id, \
                                    get_story_tooltips
from invenio.webnews_config import CFG_WEBNEWS_TOOLTIPS_DISPLAY, \
                                   CFG_WEBNEWS_TOOLTIPS_COOKIE_LONGEVITY, \
                                   CFG_WEBNEWS_TOOLTIPS_COOKIE_NAME

def _create_tooltip_cookie(name      = CFG_WEBNEWS_TOOLTIPS_COOKIE_NAME,
                           value     = "",
                           path      = "/",
                           longevity = CFG_WEBNEWS_TOOLTIPS_COOKIE_LONGEVITY):
    """
    Private shortcut function that returns an instance of a Cookie for the
    tooltips.
    """

    # The local has to be English for this to work!
    longevity_time = time.time() + ( longevity * 24 * 60 * 60 )
    longevity_expression = time.strftime("%a, %d-%b-%Y %T GMT", time.gmtime(longevity_time))

    cookie = Cookie(name,
                    value,
                    path = path,
                    expires = longevity_expression)

    return cookie

def _paths_match(path1, path2):
    """
    Internal path matcher.
    "*" acts as a wildcard for individual path parts.
    """

    # Start off by assuming that the paths don't match
    paths_match_p = False

    # Get the individual path parts.
    path1_parts = path1.strip("/").split("/")
    path2_parts = path2.strip("/").split("/")

    # If the 2 paths have different number of parts don't even bother checking
    if len(path1_parts) == len(path2_parts):
        # Check if the individual path parts match
        for (part1, part2) in zip(path1_parts, path2_parts):
            paths_match_p = ( part1 == part2 ) or ( "*" in (part1, part2) )
            if not paths_match_p:
                break

    return paths_match_p

def _does_referer_match_target_page(referer,
                                    target_page):
    """
    Compares the referer and the target page in a smart way and
    returns True if they match, otherwise False.
    """

    try:
        return ( target_page == "*" ) or _paths_match(urlsplit(target_page)[2], urlsplit(referer)[2])
    except:
        return False

def perform_request_tooltips(req = None,
                             uid = 0,
                             story_id = 0,
                             tooltip_id = 0,
                             ln = CFG_SITE_LANG):
    """
    Calculates and returns the tooltips information in JSON.
    """

    tooltips_dict = {}

    #tooltips_json = json.dumps(tooltips_dict)
    tooltips_json = '{}'

    # Did we import json?
    # Should we display tooltips at all?
    # Does the request exist?
    if not CFG_JSON_AVAILABLE or not CFG_WEBNEWS_TOOLTIPS_DISPLAY or req is None:
        return tooltips_json

    if story_id == 0:
        # Is there a latest story to display?
        story_id = get_latest_story_id()

    if story_id is None:
        return tooltips_json
    else:
        # Are there any tooltips associated to this story?
        # TODO: Filter the unwanted tooltips in the DB query.
        # We can already filter by REFERER and by the tooltips IDs in the cookie
        # In that case we don't have to iterate through the tooltips later and
        # figure out which ones to keep.
        tooltips = get_story_tooltips(story_id)
        if tooltips is None:
            return tooltips_json

    # In a more advance scenario we would save the information on whether the
    # the user has seen the tooltips:
    # * in a session param for the users that have logged in
    # * in a cookie for guests
    # We could then use a combination of these two to decide whether to display
    # the tooltips or not.
    #
    # In that case, the following tools could be used:
    #from invenio.webuser import isGuestUser, \
    #                            session_param_get, \
    #                            session_param_set
    #is_user_guest = isGuestUser(uid)
    #if not is_user_guest:
    #    try:
    #        tooltip_information = session_param_get(req, CFG_WEBNEWS_TOOLTIPS_SESSION_PARAM_NAME)
    #    except KeyError:
    #        session_param_set(req, CFG_WEBNEWS_TOOLTIPS_SESSION_PARAM_NAME, "")

    cookie_name = "%s_%s" % (CFG_WEBNEWS_TOOLTIPS_COOKIE_NAME, str(story_id))

    try:
        # Get the cookie
        cookie = get_cookie(req, cookie_name)
        # Get the tooltip IDs that have already been displayed
        tooltips_in_cookie = filter(None, str(cookie.value).split(","))
    except:
        # TODO: Maybe set a cookie with an emptry string as value?
        tooltips_in_cookie = []

    # Prepare the user's prefered language and labels.
    _ = gettext_set_language(ln)
    readmore_label = _("Learn more")
    dismiss_label  = _("I got it!")

    # Get the referer, in order to check if we should display
    # the tooltip in the given page.
    referer = get_referer(req)

    tooltips_list = []

    for tooltip in tooltips:
        tooltip_notification_id = 'ttn_%s_%s' % (str(story_id), str(tooltip[0]))
        # INFO: the tooltip body is not escaped!
        #       it's up to the admin to insert proper body text.
        #tooltip_body            = escape(tooltip[1], True)
        tooltip_body            = tooltip[1]
        tooltip_target_element  = tooltip[2]
        tooltip_target_page     = tooltip[3]

        # Only display the tooltips that match the referer and that the user
        # has not already seen.
        if _does_referer_match_target_page(referer, tooltip_target_page) and \
           ( tooltip_notification_id not in tooltips_in_cookie ):

            # Add this tooltip to the tooltips that we will display.
            tooltips_list.append({
                'id'       : tooltip_notification_id,
                'target'   : tooltip_target_element,
                'body'     : tooltip_body,
                'readmore' : readmore_label,
                'dismiss'  : dismiss_label,
            })

            # Add this tooltip to the tooltips that the user has already seen.
            #tooltips_in_cookie.append(tooltip_notification_id)

    if tooltips_list:
        # Hooray! There are some tooltips to display!
        tooltips_dict['tooltips'] = tooltips_list
        tooltips_dict['story_id'] = str(story_id)
        tooltips_dict['ln'] = ln

        # Create and set the updated cookie.
        #cookie_value = ",".join(tooltips_in_cookie)
        #cookie = _create_tooltip_cookie(cookie_name,
        #                                cookie_value)
        #req.set_cookie(cookie)
        ## INFO: Old API, ignore
        ##add_cookies(req, [cookie])

    # JSON-ify and return the tooltips.
    tooltips_json = json.dumps(tooltips_dict)
    return tooltips_json

def perform_request_dismiss(req = None,
                            uid = 0,
                            story_id = 0,
                            tooltip_notification_id = None):
    """
    Dismisses the given tooltip for the current user.
    """

    try:

        if not CFG_JSON_AVAILABLE or not CFG_WEBNEWS_TOOLTIPS_DISPLAY or req is None:
            raise Exception("Tooltips are not currently available.")

        # Retrieve the story_id
        if story_id == 0:
            if tooltip_notification_id is None:
                raise Exception("No tooltip_notification_id has been given.")
            else:
                story_id = tooltip_notification_id.split("_")[1]

        # Generate the cookie name out of the story_id
        cookie_name = "%s_%s" % (CFG_WEBNEWS_TOOLTIPS_COOKIE_NAME, str(story_id))

        # Get the existing tooltip_notification_ids from the cookie
        try:
            # Get the cookie
            cookie = get_cookie(req, cookie_name)
            # Get the tooltip IDs that have already been displayed
            tooltips_in_cookie = filter(None, str(cookie.value).split(","))
        except:
            # TODO: Maybe set a cookie with an emptry string as value?
            tooltips_in_cookie = []

        # Append the tooltip_notification_id to the existing tooltip_notification_ids
        # (only if it's not there already ; but normally it shouldn't be)
        if tooltip_notification_id not in tooltips_in_cookie:
            tooltips_in_cookie.append(tooltip_notification_id)

        # Create and set the cookie with the updated cookie value
        cookie_value = ",".join(tooltips_in_cookie)
        cookie = _create_tooltip_cookie(cookie_name, cookie_value)
        req.set_cookie(cookie)
        # INFO: Old API, ignore
        #add_cookies(req, [cookie])

    except:
        # Something went wrong..
        # TODO: what went wrong?
        dismissed_p_dict = { "success" : 0 }
        dismissed_p_json = json.dumps(dismissed_p_dict)
        return dismissed_p_json
    else:
        # Everything went great!
        dismissed_p_dict = { "success" : 1 }
        dismissed_p_json = json.dumps(dismissed_p_dict)
        return dismissed_p_json
    # enable for python >= 2.5
    #finally:
    #    # JSON-ify and return the result
    #    dismissed_p_json = json.dumps(dismissed_p_dict)
    #    return dismissed_p_json
