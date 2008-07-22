## $Id$
##
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

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

from invenio.access_control_engine import acc_authorize_action
from invenio.bibedit_engine import perform_request_index, \
    perform_request_edit, perform_request_submit, perform_request_history
from invenio.config import CFG_SITE_LANG, CFG_SITE_URL
from invenio.messages import gettext_set_language, wash_language
from invenio.search_engine import record_exists, \
    guess_primary_collection_of_a_record
from invenio.urlutils import wash_url_argument, redirect_to_url
from invenio.webpage import page
from invenio.webuser import getUid, page_not_authorized, collect_user_info

navtrail = (' <a class="navtrail" href=\"%s/help/admin\">Admin Area</a> '
            ) % CFG_SITE_URL

def index(req, ln=CFG_SITE_LANG, recid=None, temp="false", format_tag='marc',
          edit_tag=None, delete_tag=None, num_field=None, add=0, cancel=0,
          delete=0, confirm_delete=0, **args):
    """BibEdit Admin interface."""
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    recid          = wash_url_argument(recid,          "int")
    add            = wash_url_argument(add,            "int")
    cancel         = wash_url_argument(cancel,         "int")
    delete         = wash_url_argument(delete,         "int")
    confirm_delete = wash_url_argument(confirm_delete, "int")
    if recid == 0:
        # do not display the introductory recID selection box to guest
        # users (as it used to be with v0.99.0):
        user_info = collect_user_info(req)
        if user_info['email'] == 'guest':
            (auth_code, auth_message) = acc_authorize_action(req, 'runbibedit')
            return page_not_authorized(req=req, text=auth_message,
                                       navtrail=navtrail)
        else:
            # the user is logged in, so display the box:
            (body, errors, warnings) = perform_request_index(ln, recid,
                cancel, delete, confirm_delete, uid, temp, format_tag,
                edit_tag, delete_tag, num_field, add, args)
    else:
        (auth_code, auth_message) = acc_authorize_action(req, 'runbibedit',
            collection=guess_primary_collection_of_a_record(recid))
        if auth_code != 0:
            (auth_code, auth_message) = acc_authorize_action(req,
                                                             'runbibedit')
        if auth_code == 0:
            (body, errors, warnings) = perform_request_index(ln, recid,
                cancel, delete, confirm_delete, uid, temp, format_tag,
                edit_tag, delete_tag, num_field, add, args)
        else:
            return page_not_authorized(req=req, text=auth_message,
                                       navtrail=navtrail)

    if recid != 0:
        title = _("Record") + " #" + str(recid)
        if add == 3:
            title = _("Record %s - Add a field") % ('#' + str(recid))
    else:
        title = _("BibEdit Admin Interface")

    return page(title       = title,
                body        = body,
                errors      = errors,
                warnings    = warnings,
                uid         = getUid(req),
                language    = ln,
                navtrail    = navtrail,
                lastupdated = __lastupdated__,
                req         = req)

def edit(req, recid=None, tag=None, num_field='0', num_subfield=0,
         format_tag='marc', act_subfield=None, temp="false", add=0,
         ln=CFG_SITE_LANG, **args):
    """Edit Field page."""
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid       = getUid(req)

    recid     = wash_url_argument(recid,     "int")
    num_field = wash_url_argument(num_field, "int")
    add       = wash_url_argument(add,       "int")
    num_subfield = wash_url_argument(num_subfield, "int")
    if (recid and tag and (record_exists(recid)>0)):
        (auth_code, auth_message) = acc_authorize_action(req, 'runbibedit',
            collection=guess_primary_collection_of_a_record(recid))
        if auth_code != 0:
            (auth_code, auth_message) = acc_authorize_action(req, 'runbibedit')
        if auth_code == 0:
            (body, errors, warnings) = perform_request_edit(ln, recid, uid,
                tag, num_field, num_subfield, format_tag, temp, act_subfield,
                add, args)
        else:
            return page_not_authorized(req=req, text=auth_message,
                                       navtrail=navtrail)
    else:
        redirect_to_url(req, 'index?ln=' + ln)

    title = _("Edit record %(x_recid)s, field %(x_field)s") % {
        'x_recid': '#' + str(recid),
        'x_field':  '#' + str(tag[:3])}
    if add == 1:
        title = _("Edit record %(x_recid)s, field %(x_field)s - Add a "
                  "subfield") % {'x_recid': '#' + str(recid),
                                 'x_field':  '#' + str(tag[:3])}
    return page(title       = title,
                body        = body,
                errors      = errors,
                warnings    = warnings,
                uid         = getUid(req),
                language    = ln,
                navtrail    = navtrail,
                lastupdated = __lastupdated__,
                req         = req)

def submit(req, recid='', ln=CFG_SITE_LANG):
    """Submit temp record to database."""
    ln = wash_language(ln)
    _ = gettext_set_language(ln)

    recid = wash_url_argument(recid, "int")
    if (recid and (record_exists(recid)>0)):
        (auth_code, auth_message) = acc_authorize_action(req, 'runbibedit',
            collection=guess_primary_collection_of_a_record(recid))
        if auth_code != 0:
            (auth_code, auth_message) = acc_authorize_action(req, 'runbibedit')
        if auth_code == 0:
            (body, errors, warnings) = perform_request_submit(ln, recid)
        else:
            return page_not_authorized(req=req, text=auth_message,
                                       navtrail=navtrail)
    else:
        redirect_to_url(req, 'index?ln=' + ln)

    return page(title       = _("Submit and save record %s") % (
                                '#' + str(recid)),
                body        = body,
                errors      = errors,
                warnings    = warnings,
                uid         = getUid(req),
                language    = ln,
                navtrail    = navtrail,
                lastupdated = __lastupdated__,
                req         = req)

def history(req, ln=CFG_SITE_LANG, recid=None, revid=None, revid_cmp=None,
             action=None, format_tag=None):
    """ Bibedit history interface. """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)

    recid = wash_url_argument(recid, "int")
    if (recid and (record_exists(recid)>0)):
        (auth_code, auth_message) = acc_authorize_action(req, 'runbibedit',
            collection=guess_primary_collection_of_a_record(recid))
        if auth_code != 0:
            (auth_code, auth_message) = acc_authorize_action(req,
                                                             'runbibedit')
        if auth_code == 0:
            (body, errors, warnings) = perform_request_history(ln, recid,
                revid, revid_cmp, action, uid, format_tag)
        else:
            return page_not_authorized(req=req, text=auth_message,
                                       navtrail=navtrail)
    else:
        redirect_to_url(req, 'index')

    title = _("Record") + " #" + str(recid)
    return page(title   = title,
                body        = body,
                errors      = errors,
                warnings    = warnings,
                uid         = getUid(req),
                language    = ln,
                navtrail    = navtrail,
                lastupdated = __lastupdated__,
                req         = req)