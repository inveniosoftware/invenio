# This file is part of Invenio.
# Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013 CERN.
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

"""Web Baskets features."""

__revision__ = "$Id$"

import sys


if sys.hexversion < 0x2040000:
    # pylint: disable=W0622
    from sets import Set as set
    # pylint: enable=W0622

from intbitset import intbitset

import cgi
import urllib
from httplib import urlsplit, HTTPConnection
#from socket import getdefaulttimeout, setdefaulttimeout
from zlib import decompress
import re

from invenio.config import CFG_SITE_LANG, CFG_SITE_URL, \
     CFG_WEBBASKET_MAX_NUMBER_OF_DISPLAYED_BASKETS
from invenio.base.i18n import gettext_set_language
from invenio.base.globals import cfg
from invenio.utils.date import convert_datetext_to_dategui, \
                              convert_datetext_to_datestruct,\
                              convert_datestruct_to_dategui
from invenio.modules.formatter import format_record
from invenio.utils.url import get_referer
from invenio.legacy.webuser import isGuestUser, collect_user_info
from invenio.legacy.search_engine import \
     record_exists, \
     get_merged_recid, \
     check_user_can_view_record
#from invenio.webcomment import check_user_can_attach_file_to_comments
import invenio.legacy.webbasket.db_layer as db
try:
    import invenio.legacy.template
    webbasket_templates = invenio.legacy.template.load('webbasket')
except ImportError:
    pass
from invenio.legacy.websearch_external_collections.utils import get_collection_name_by_id
from invenio.legacy.websearch_external_collections import select_hosted_search_engines
from invenio.legacy.websearch_external_collections.config import CFG_EXTERNAL_COLLECTION_TIMEOUT
from invenio.legacy.websearch_external_collections.getter import HTTPAsyncPageGetter, async_download
from invenio.ext.logging import register_exception
from invenio.legacy.search_engine import search_unit
from invenio.utils.html import remove_html_markup, unescape

from .errors import InvenioWebBasketWarning
########################################
### Display public baskets and notes ###
########################################

def perform_request_display_public(uid,
                                   selected_bskid=0,
                                   selected_recid=0,
                                   optional_params={},
                                   of='hb',
                                   ln=CFG_SITE_LANG):
    """Engine for the display of a public interface. Calls the template and returns HTML.
    @param selected_bskid: The id of the basket to be displayed (optional)
    @param selected_recid: The id of the item to be displayed (optional)
    @param optional_params: optional parameters to be passed, used for notes
    @param of: display format
    @param ln: language"""

    _ = gettext_set_language(ln)

    warnings_item = []
    warnings_basket = []

    (of, of_warnings) = wash_of(of)
    if of_warnings:
        navtrail = create_webbasket_navtrail(uid, ln=ln)
        body = webbasket_templates.tmpl_warnings(of_warnings, ln)
        return (body, of_warnings, navtrail)

    basket = db.get_public_basket_info(selected_bskid)
    if not basket:
        if of != 'hb':
            return ("", None, None)
        try:
            raise InvenioWebBasketWarning(_('The selected public basket does not exist or you do not have access to it.'))
        except InvenioWebBasketWarning as exc:
            register_exception(stream='warning')
        warnings_html = webbasket_templates.tmpl_warnings(exc.message, ln)
            #warnings.append(exc.message)
        #warnings = ['WRN_WEBBASKET_INVALID_OR_RESTRICTED_PUBLIC_BASKET']
        (body, navtrail) = perform_request_list_public_baskets(uid)
        try:
            raise InvenioWebBasketWarning(_('Please select a valid public basket from the list of public baskets.'))
        except InvenioWebBasketWarning as exc:
            register_exception(stream='warning')
            #warnings.append(exc.message)
        #warnings.append('WRN_WEBBASKET_SHOW_LIST_PUBLIC_BASKETS')
        warnings_html += webbasket_templates.tmpl_warnings(exc.message, ln)
        body = warnings_html + body
        return (body, None, navtrail)
    else:
        (bskid, basket_name, id_owner, last_update, dummy, nb_items, recids, share_rights) = basket[0]
        if selected_recid:
            valid_recids = tuple(map(int, recids.split(',')))
            if selected_recid in valid_recids:
                (content, warnings_item) = __display_public_basket_single_item(bskid,
                                                                          basket_name,
                                                                          selected_recid,
                                                                          nb_items,
                                                                          share_rights,
                                                                          optional_params,
                                                                          of,
                                                                          ln)
            else:
                try:
                    raise InvenioWebBasketWarning(_('The selected item does not exist or you do not have access to it.'))
                except InvenioWebBasketWarning as exc:
                    register_exception(stream='warning')
                    warnings_item.append(exc.message)
                #warnings_item.append('WRN_WEBBASKET_INVALID_OR_RESTRICTED_ITEM')
                try:
                    raise InvenioWebBasketWarning(_('Returning to the public basket view.'))
                except InvenioWebBasketWarning as exc:
                    register_exception(stream='warning')
                    warnings_item.append(exc.message)
                #warnings_item.append('WRN_WEBBASKET_RETURN_TO_PUBLIC_BASKET')
                selected_recid = 0
        if not selected_recid:
            if uid == id_owner:
                subscription_status = 0
            else:
                if db.is_user_subscribed_to_basket(uid,bskid):
                    subscription_status = 1
                else:
                    subscription_status = -1
            (content, warnings_basket) = __display_public_basket(bskid,
                                                          basket_name,
                                                          last_update,
                                                          nb_items,
                                                          share_rights,
                                                          id_owner,
                                                          subscription_status,
                                                          of,
                                                          ln)

    if of == 'hb':
        body = webbasket_templates.tmpl_display(content=content)
        warnings = warnings_item + warnings_basket
        warnings_html = webbasket_templates.tmpl_warnings(warnings, ln)
        body = warnings_html + body
    else:
        body = content

    if of == 'hb':
        navtrail = create_webbasket_navtrail(uid,
                                             bskid=selected_bskid,
                                             public_basket=True,
                                             ln=ln)

    if of == 'hb':
        return (body, warnings, navtrail)
    else:
        return (body, None, None)

def __display_public_basket(bskid,
                            basket_name,
                            last_update,
                            nb_items,
                            share_rights,
                            id_owner,
                            subscription_status,
                            of='hb',
                            ln=CFG_SITE_LANG):
    """Private function. Display a basket giving its category and topic or group.
    @param share_rights: rights user has on basket
    @param group_sharing_level: None if basket is not shared,
                                0 if public basket,
                                > 0 if shared to usergroups but not public.
    @param category: selected category (see webbasket_config.py)
    @param selected_topic: # of selected topic to display baskets
    @param selected_group_id: id of group to display baskets
    @param ln: language"""

    _ = gettext_set_language(ln)

    warnings = []

    nb_total_notes = 0
    last_note = _("N/A")
    records = []
    notes_dates = []
    last_update = convert_datetext_to_dategui(last_update, ln)

    items = db.get_basket_content(bskid, of)
    external_recids = []

    for (recid, collection_id, nb_notes, last_note, ext_val, int_val, score) in items:
        notes_dates.append(convert_datetext_to_datestruct(last_note))
        last_note = convert_datetext_to_dategui(last_note, ln)
        colid = collection_id and collection_id or collection_id == 0 and -1 or 0
        val = ""
        nb_total_notes += nb_notes
        if recid < 0:
            if ext_val:
                val = decompress(ext_val)
            else:
                external_recids.append(recid)
        else:
            if int_val:
                val = decompress(int_val)
            else:
                val = format_record(recid, of, on_the_fly=True)
        records.append((recid, colid, nb_notes, last_note, val, score))

    if external_recids:
        external_records = format_external_records(external_recids, of)

        for external_record in external_records:
            for record in records:
                if record[0] == -external_record[0]:
                    idx = records.index(record)
                    tuple_to_list = list(records.pop(idx))
                    tuple_to_list[4] = external_record[1]
                    records.insert(idx, tuple(tuple_to_list))
                    break

    if notes_dates:
        last_note = convert_datestruct_to_dategui(max(notes_dates), ln)

    body = webbasket_templates.tmpl_public_basket(bskid,
                                                  basket_name,
                                                  last_update,
                                                  nb_items,
                                                  (check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['READCMT'],),),
                                                  nb_total_notes,
                                                  records,
                                                  id_owner,
                                                  subscription_status,
                                                  of,
                                                  ln)
    return (body, warnings)

def __display_public_basket_single_item(bskid,
                                        basket_name,
                                        recid,
                                        nb_items,
                                        share_rights,
                                        optional_params={},
                                        of='hb',
                                        ln=CFG_SITE_LANG):
    """Private function. Display a basket giving its category and topic or group.
    @param share_rights: rights user has on basket
    @param group_sharing_level: None if basket is not shared,
                                0 if public basket,
                                > 0 if shared to usergroups but not public.
    @param category: selected category (see webbasket_config.py)
    @param selected_topic: # of selected topic to display baskets
    @param selected_group_id: id of group to display baskets
    @param ln: language"""

    _ = gettext_set_language(ln)

    warnings = []

    item = db.get_basket_item(bskid, recid, of)

    if item:
        (recid, collection_id, nb_notes, last_note, ext_val, int_val, score) = item[0]
        previous_item_recid = item[1]
        next_item_recid = item[2]
        item_index = item[3]
    else:
        # The validity of the recid and hence the item is already checked by the
        # previous function and the appropriate warning is returned.
        # This is just an extra check just in case we missed something.
        # An empty body is returned.
        body = ""
        try:
            raise InvenioWebBasketWarning(_('The selected item does not exist or you do not have access to it.'))
        except InvenioWebBasketWarning as exc:
            register_exception(stream='warning')
            warnings.append(exc.message)
        #warnings.append('WRN_WEBBASKET_INVALID_OR_RESTRICTED_ITEM')
        return (body, warnings)
    last_note = convert_datetext_to_dategui(last_note, ln)
    colid = collection_id and collection_id or collection_id == 0 and -1 or 0
    val = ""
    if recid < 0:
        if ext_val:
            val = decompress(ext_val)
        else:
            external_record = format_external_records([recid], of)
            val = external_record and external_record[0][1] or ""
    else:
        if int_val:
            val = decompress(int_val)
        else:
            val = format_record(recid, of, on_the_fly=True)
    item = (recid, colid, nb_notes, last_note, val, score)

    notes = db.get_notes(bskid, recid)

    body = webbasket_templates.tmpl_public_basket_single_item(bskid,
                                                              basket_name,
                                                              nb_items,
                                                              (check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['READCMT']),
                                                               check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['ADDCMT'])),
                                                              item,
                                                              notes,
                                                              previous_item_recid,
                                                              next_item_recid,
                                                              item_index,
                                                              optional_params,
                                                              of,
                                                              ln)
    return (body, warnings)

def perform_request_list_public_baskets(uid,
                                        limit=1,
                                        sort='name',
                                        asc=1,
                                        nb_views_show_p=False,
                                        ln=CFG_SITE_LANG):

    """Display list of public baskets.
    @param limit: display baskets from the incrementally numbered 'limit' and on
    @param sort: sort by 'name' or 'views' or 'owner' or 'date' or 'items'
    @param asc: ascending sort or not
    @param ln: language"""

    warnings_html = ""

    number_of_all_public_baskets = db.count_all_public_baskets()

    limit -= 1
    if limit < 0:
        limit = 0
    elif limit >= number_of_all_public_baskets:
        limit = number_of_all_public_baskets - 1

    if not nb_views_show_p and sort == 'views':
        # TODO: Add a 'sort by views' restriction warning
        #warnings.append('...')
        #warnings_html += webbasket_templates.tmpl_warnings(warnings, ln)
        sort = "name"

    all_public_baskets = db.get_list_public_baskets(limit,
                                                    CFG_WEBBASKET_MAX_NUMBER_OF_DISPLAYED_BASKETS,
                                                    sort,
                                                    asc)

    body = webbasket_templates.tmpl_display_list_public_baskets(all_public_baskets,
                                                                limit,
                                                                number_of_all_public_baskets,
                                                                sort,
                                                                asc,
                                                                nb_views_show_p,
                                                                ln)

    search_box = __create_search_box(uid=uid,
                                     category=cfg['CFG_WEBBASKET_CATEGORIES']['ALLPUBLIC'],
                                     ln=ln)

    body = webbasket_templates.tmpl_display(content=body, search_box=search_box)

    body = warnings_html + body

    navtrail = create_webbasket_navtrail(uid,
                                         public_basket=True,
                                         ln=ln)

    return (body, navtrail)

def perform_request_write_public_note(uid,
                                      bskid=0,
                                      recid=0,
                                      cmtid=0,
                                      ln=CFG_SITE_LANG):
    """Display a note writing form
    @param uid: user id
    @param bskid: basket id
    @param recid: record id (comments are on a specific record in a specific basket)
    @param cmtid: if provided this comment is a reply to comment cmtid.
    @param category: selected category
    @param topic: selected topic
    @param group_id: selected group id
    @param ln: language
    """
    _ = gettext_set_language(ln)

    optional_params = {}
    warnings_rights = []
    warnings_html = ""

    if not can_add_notes_to_public_basket_p(bskid):
        try:
            raise InvenioWebBasketWarning(_('You do not have permission to write notes to this item.'))
        except InvenioWebBasketWarning as exc:
            register_exception(stream='warning')
#            warnings_rights = exc.message
        #warnings_rights = ['WRN_WEBBASKET_RESTRICTED_WRITE_NOTES']
        warnings_html += webbasket_templates.tmpl_warnings(warnings_rights, ln)
    else:
        if cmtid and db.note_belongs_to_item_in_basket_p(cmtid, recid, bskid):
            optional_params["Add note"] = db.get_note(cmtid)
            optional_params["Reply to"] = cmtid
        elif cmtid:
            optional_params["Add note"] = ()
            try:
                raise InvenioWebBasketWarning(_('The note you are quoting does not exist or you do not have access to it.'))
            except InvenioWebBasketWarning as exc:
                register_exception(stream='warning')
                optional_params["Warnings"] = exc.message
        else:
            optional_params["Add note"] = ()

    (body, warnings, navtrail) = perform_request_display_public(uid=uid,
                                                                selected_bskid=bskid,
                                                                selected_recid=recid,
                                                                optional_params=optional_params,
                                                                of='hb',
                                                                ln=CFG_SITE_LANG)

    if not warnings:
        body = warnings_html + body
#        warnings = warnings_rights

    return (body, navtrail)

def perform_request_save_public_note(uid,
                                     bskid=0,
                                     recid=0,
                                     note_title="",
                                     note_body="",
                                     date_creation="",
                                     editor_type='textarea',
                                     ln=CFG_SITE_LANG,
                                     reply_to=None):
    """ Save a given comment if able to.
    @param uid: user id (int)
    @param bskid: basket id (int)
    @param recid: record id (int)
    @param title: title of comment (string)
    @param text: comment's body (string)
    @param ln: language (string)
    @param editor_type: the kind of editor/input used for the comment: 'textarea', 'ckeditor'
    @param reply_to: the id of the comment we are replying to
    """
    optional_params = {}
    warnings_rights = []
    warnings_html = ""
    _ = gettext_set_language(ln)

    if not can_add_notes_to_public_basket_p(bskid):
        try:
            raise InvenioWebBasketWarning(_('You do not have permission to write notes to this item.'))
        except InvenioWebBasketWarning as exc:
            register_exception(stream='warning')
#            warnings_rights = exc.message
        #warnings_rights = ['WRN_WEBBASKET_RESTRICTED_WRITE_NOTES']
        warnings_html += webbasket_templates.tmpl_warnings(warnings_rights, ln)
    else:
        if not note_title or not note_body: # FIXME: improve check when ckeditor
            optional_params["Incomplete note"] = (note_title, note_body)
            try:
                raise InvenioWebBasketWarning(_('You must fill in both the subject and the body of the note.'))
            except InvenioWebBasketWarning as exc:
                register_exception(stream='warning')
                optional_params["Warnings"] = exc.message
        else:
            if editor_type == 'ckeditor':
                # Here we remove the line feeds introduced by CKEditor (they
                # have no meaning for the user) and replace the HTML line
                # breaks by linefeeds, so that we are close to an input that
                # would be done without the CKEditor. That's much better if a
                # reply to a comment is made with a browser that does not
                # support CKEditor.
                note_body = note_body.replace('\n', '').replace('\r', '').replace('<br />', '\n')
            if not(db.save_note(uid, bskid, recid, note_title, note_body, date_creation, reply_to)):
                # TODO: The note could not be saved. DB problem?
                pass
            else:
                # TODO: inform about successful annotating.
                pass

    (body, warnings, navtrail) = perform_request_display_public(uid=uid,
                                                                selected_bskid=bskid,
                                                                selected_recid=recid,
                                                                optional_params=optional_params,
                                                                of='hb',
                                                                ln=CFG_SITE_LANG)

    if not warnings:
        body = warnings_html + body
#        warnings = warnings_rights

    return (body, navtrail)

#################################
### Display baskets and notes ###
#################################
def perform_request_display(uid,
                            selected_category=cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'],
                            selected_topic="",
                            selected_group_id=0,
                            selected_bskid=0,
                            selected_recid=0,
                            optional_params={},
                            of='hb',
                            ln=CFG_SITE_LANG):
    """Display all the baskets of given category, topic or group.
    @param uid: user id
    @param selected_category: selected category (see webbasket_config.py)
    @param selected_topic: # of selected topic to display baskets
    @param selected_group_id: id of group to display baskets
    @param ln: language"""

    _ = gettext_set_language(ln)

    warnings = []
    warnings_html = ""

    valid_category_choice = False
    selected_basket_info = []
    content = ""
    search_box = ""

    (of, of_warnings) = wash_of(of)
    if of_warnings:
        navtrail = create_webbasket_navtrail(uid, ln=ln)
        body = webbasket_templates.tmpl_warnings(of_warnings, ln)
        return (body, of_warnings, navtrail)


    (selected_category, category_warnings) = wash_category(selected_category)
    if not selected_category and category_warnings:
        if of == 'xm':
            return ("", None. None)
        navtrail = create_webbasket_navtrail(uid, ln=ln)
        body = webbasket_templates.tmpl_warnings(category_warnings, ln)
        return (body, category_warnings, navtrail)

    if selected_category == cfg['CFG_WEBBASKET_CATEGORIES']['ALLPUBLIC']:
        if of == 'xm':
            return ("", None. None)
        # TODO: Send the correct title of the page as well.
        return perform_request_list_public_baskets(uid)

    personal_info = db.get_all_user_personal_basket_ids_by_topic(uid)
    personal_baskets_info = ()

    if personal_info and selected_category == cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE']:
        # Create a dictionary that has the valid topics for keys and the basket
        # ids in each topic (string, ids separated by commas) as values.
        personal_info_dict = {}
        for personal_info_topic_and_bskids in personal_info:
            personal_info_dict[personal_info_topic_and_bskids[0]] = map(int, personal_info_topic_and_bskids[1].split(','))
        valid_category_choice = True
        if selected_topic:
            valid_selected_topic_p = False
            # Validate the topic. Check if the selected topic is one of the keys
            # in the dictionary. If it is valid then get some more info for that
            # topic from the DB.
            if selected_topic in personal_info_dict.keys():
                personal_baskets_info = db.get_personal_baskets_info_for_topic(uid, selected_topic)
                valid_selected_topic_p = True
            if not valid_selected_topic_p:
                try:
                    raise InvenioWebBasketWarning(_('The selected topic does not exist or you do not have access to it.'))
                except InvenioWebBasketWarning as exc:
                    register_exception(stream='warning')
                    warnings.append(exc.message)
                #warnings.append('WRN_WEBBASKET_INVALID_OR_RESTRICTED_TOPIC')
                warnings_html += webbasket_templates.tmpl_warnings(exc.message, ln)
                valid_selected_topic_p = False
                selected_topic = ""
        else:
            valid_selected_topic_p = True

        if valid_selected_topic_p and selected_bskid:
            if selected_topic:
                valid_bskids = personal_info_dict[selected_topic]
            else:
                valid_bskids = []
                for valid_bskids_per_topic in personal_info_dict.values():
                    valid_bskids.extend(valid_bskids_per_topic)
            if selected_bskid in valid_bskids:
                if not selected_topic:
                    for valid_topic in personal_info_dict.iterkeys():
                        if selected_bskid in personal_info_dict[valid_topic]:
                            selected_topic = valid_topic
                            break
                personal_baskets_info = db.get_personal_baskets_info_for_topic(uid, selected_topic)
                for personal_basket_info in personal_baskets_info:
                    if personal_basket_info[0] == selected_bskid:
                        selected_basket_info = list(personal_basket_info)
                        selected_basket_info.append(cfg['CFG_WEBBASKET_SHARE_LEVELS']['MANAGE'])
                        break
            else:
                try:
                    raise InvenioWebBasketWarning(_('The selected basket does not exist or you do not have access to it.'))
                except InvenioWebBasketWarning as exc:
                    register_exception(stream='warning')
                    warnings.append(exc.message)
                #warnings.append('WRN_WEBBASKET_INVALID_OR_RESTRICTED_BASKET')
                warnings_html += webbasket_templates.tmpl_warnings(exc.message, ln)
                selected_bskid = 0
        else:
            selected_bskid = 0

    group_info = db.get_all_user_group_basket_ids_by_group(uid)
    group_baskets_info = ()
    selected_group_name = ""

    if group_info and selected_category == cfg['CFG_WEBBASKET_CATEGORIES']['GROUP']:
        # Create a dictionary that has the valid group as keys and the basket
        # ids in each group (string, ids separated by commas) as values.
        group_info_dict = {}
        for group_info_group_and_bskids in group_info:
            group_info_dict[group_info_group_and_bskids[0]] = (group_info_group_and_bskids[1], \
                                                               map(int, group_info_group_and_bskids[2].split(',')))
        valid_category_choice = True
        if selected_group_id:
            valid_selected_group_p = False
            # Validate the group. Check if the selected group is one of the keys
            # in the dictionary. If it is valid then get some more info for that
            # group from the DB.
            if selected_group_id in group_info_dict.keys():
                selected_group_name = group_info_dict[selected_group_id][0]
                group_baskets_info = db.get_group_baskets_info_for_group(selected_group_id)
                valid_selected_group_p = True
            if not valid_selected_group_p:
                try:
                    raise InvenioWebBasketWarning(_('The selected topic does not exist or you do not have access to it.'))
                except InvenioWebBasketWarning as exc:
                    register_exception(stream='warning')
                    warnings.append(exc.message)
                #warnings.append('WRN_WEBBASKET_INVALID_OR_RESTRICTED_GROUP')
                warnings_html += webbasket_templates.tmpl_warnings(exc.message, ln)
                selected_group_id = ""
                valid_selected_group_p = False
        else:
            valid_selected_group_p = True

        if valid_selected_group_p and selected_bskid:
            if selected_group_id:
                valid_bskids = group_info_dict[selected_group_id][1]
            else:
                valid_bskids = []
                for group_and_valid_bskids_per_group in group_info_dict.values():
                    valid_bskids_per_group = group_and_valid_bskids_per_group[1]
                    valid_bskids.extend(valid_bskids_per_group)
            if selected_bskid in valid_bskids:
                if not selected_group_id:
                    for valid_group_id in group_info_dict.iterkeys():
                        if selected_bskid in group_info_dict[valid_group_id][1]:
                            selected_group_id = valid_group_id
                            break
                selected_group_name = group_info_dict[selected_group_id][0]
                group_baskets_info = db.get_group_baskets_info_for_group(selected_group_id)
                for group_basket_info in group_baskets_info:
                    if group_basket_info[0] == selected_bskid:
                        selected_basket_info = list(group_basket_info)
                        # INFO: uncomment the two following lines to give MANAGE
                        # rights to the owner of the basket even when through
                        # the group view of the basket.
                        #if group_basket_info[7] == uid:
                        #    selected_basket_info[6] = cfg['CFG_WEBBASKET_SHARE_LEVELS']['MANAGE']
                        selected_basket_info.pop(7)
                        break
            else:
                try:
                    raise InvenioWebBasketWarning(_('The selected topic does not exist or you do not have access to it.'))
                except InvenioWebBasketWarning as exc:
                    register_exception(stream='warning')
                    warnings.append(exc.message)
                #warnings.append('WRN_WEBBASKET_INVALID_OR_RESTRICTED_BASKET')
                warnings_html += webbasket_templates.tmpl_warnings(exc.message, ln)
                selected_bskid = 0
        else:
            selected_bskid = 0

    public_info = db.get_all_external_basket_ids_and_names(uid)
    if public_info and selected_category == cfg['CFG_WEBBASKET_CATEGORIES']['EXTERNAL']:
        valid_category_choice = True
        if selected_bskid:
            valid_bskids = [(valid_basket[0], valid_basket[3]) for valid_basket in public_info]
            if (selected_bskid, 0) in valid_bskids:
                public_basket_info = db.get_external_basket_info(selected_bskid)
                if public_basket_info:
                    selected_basket_info = list(public_basket_info[0])
            elif (selected_bskid, None) in valid_bskids:
                try:
                    raise InvenioWebBasketWarning(_('The selected basket is no longer public.'))
                except InvenioWebBasketWarning as exc:
                    register_exception(stream='warning')
                    warnings.append(exc.message)
                #warnings.append('WRN_WEBBASKET_FORMER_PUBLIC_BASKET')
                warnings_html += webbasket_templates.tmpl_warnings(exc.message, ln)
                selected_bskid = 0
            else:
                try:
                    raise InvenioWebBasketWarning(_('The selected basket does not exist or you do not have access to it.'))
                except InvenioWebBasketWarning as exc:
                    register_exception(stream='warning')
                    warnings.append(exc.message)
                #warnings.append('WRN_WEBBASKET_INVALID_OR_RESTRICTED_BASKET')
                warnings_html += webbasket_templates.tmpl_warnings(exc.message, ln)
                selected_bskid = 0

    if not valid_category_choice:
        if personal_info:
            selected_category = cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE']
        elif group_info:
            selected_category = cfg['CFG_WEBBASKET_CATEGORIES']['GROUP']
        elif public_info:
            selected_category = cfg['CFG_WEBBASKET_CATEGORIES']['EXTERNAL']
        else:
            selected_category = cfg['CFG_WEBBASKET_CATEGORIES']['ALLPUBLIC']

    if not of.startswith('x'):
        directory_box = webbasket_templates.tmpl_create_directory_box(selected_category,
                                                                      selected_topic,
                                                                      (selected_group_id, selected_group_name),
                                                                      selected_bskid,
                                                                      (personal_info, personal_baskets_info),
                                                                      (group_info, group_baskets_info),
                                                                      public_info,
                                                                      ln)

    if selected_basket_info:
        if selected_recid:
            (bskid, basket_name, last_update, dummy, nb_items, dummy, share_rights) = selected_basket_info
            (content, bsk_warnings) = __display_basket_single_item(uid, bskid,
                                                                   basket_name,
                                                                   selected_recid,
                                                                   last_update,
                                                                   nb_items,
                                                                   share_rights,
                                                                   selected_category,
                                                                   selected_topic,
                                                                   selected_group_id,
                                                                   optional_params,
                                                                   of,
                                                                   ln)
        else:
            (bskid, basket_name, last_update, dummy, nb_items, dummy, share_rights) = selected_basket_info
            share_level = db.get_basket_share_level(bskid)
            if share_level:
                share_level = share_level[0][0]
            else:
                share_level = None
            if share_level == 0:
                nb_subscribers = db.count_public_basket_subscribers(bskid)
            else:
                nb_subscribers = None

            (content, bsk_warnings) = __display_basket(uid, bskid,
                                                       basket_name,
                                                       last_update,
                                                       nb_items,
                                                       nb_subscribers,
                                                       share_rights,
                                                       share_level,
                                                       selected_category,
                                                       selected_topic,
                                                       selected_group_id,
                                                       of,
                                                       ln)
            warnings.extend(bsk_warnings)

        if not of.startswith('x'):
            warnings_html += webbasket_templates.tmpl_warnings(bsk_warnings, ln)
    else:
        if not of.startswith('x'):
            search_box = __create_search_box(uid=uid,
                                             category=selected_category,
                                             topic=selected_topic,
                                             grpid=selected_group_id,
                                             p="",
                                             n=1,
                                             ln=ln)

    if not of.startswith('x'):
        body = webbasket_templates.tmpl_display(directory_box, content, search_box)
        body = warnings_html + body
    else:
        body = content

    if not of.startswith('x'):
        navtrail = create_webbasket_navtrail(uid,
                                             category=selected_category,
                                             topic=selected_topic,
                                             group=selected_group_id,
                                             bskid=selected_bskid,
                                             ln=ln)

    if not of.startswith('x'):
        return (body, warnings, navtrail)
    else:
        return (body, None, None)

def __display_basket(uid, bskid,
                     basket_name,
                     last_update,
                     nb_items,
                     nb_subscribers,
                     share_rights,
                     share_level,
                     selected_category=cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'],
                     selected_topic="",
                     selected_group_id=0,
                     of="hb",
                     ln=CFG_SITE_LANG):
    """Private function. Display a basket giving its category and topic or group.
    @param share_rights: rights user has on basket
    @param share_level: None if basket is not shared,
                                0 if public basket,
                                > 0 if shared to usergroups but not public.
    @param selected_category: selected category (see webbasket_config.py)
    @param selected_topic: # of selected topic to display baskets
    @param selected_group_id: id of group to display baskets
    @param ln: language"""

    _ = gettext_set_language(ln)

    warnings = []

    nb_total_notes = 0
    last_note = _("N/A")
    records = []
    notes_dates = []
    #date_modification = convert_datetext_to_dategui(date_modification, ln)
    last_update = convert_datetext_to_dategui(last_update, ln)

    items = db.get_basket_content(bskid, of)
    external_recids = []

    for (recid, collection_id, nb_notes, last_note, ext_val, int_val, score) in items:
        notes_dates.append(convert_datetext_to_datestruct(last_note))
        last_note = convert_datetext_to_dategui(last_note, ln)
        colid = collection_id and collection_id or collection_id == 0 and -1 or 0
        val = ""
        nb_total_notes += nb_notes

        # check if the current recid has been deleted and has been merged,
        # in that case obtain the recid of the new record and redirect to it
        merged_recid = get_merged_recid(recid)
        record_status = record_exists(recid)
        if record_status == -1 and merged_recid: # the record has been deleted and has been merged
            # keep notes about the deleted record to store them in the merged record
            deleted_record_notes = db.get_notes(bskid, recid)
            # remove the deleted record recid from the basket bskid
            db.delete_item(bskid, recid)
            recid = merged_recid
            # add the merged record recid in the basket bskid
            db.add_to_basket(uid, [recid], 0, bskid)
            # save the notes in the merged record recid
            for note in deleted_record_notes:
                note_title = note[2]
                note_body = note[3]
                date_creation= note[4]
                reply_to = note[-1]
                db.save_note(uid, bskid, recid, note_title, note_body, date_creation, reply_to)
            int_val = ""

        if recid < 0:
            if ext_val:
                val = decompress(ext_val)
            else:
                external_recids.append(recid)
        else:
            if int_val:
                val = decompress(int_val)
            else:
                val = format_record(recid, of, on_the_fly=True)
        ## external item (record): colid = positive integet
        ## external item (url): colid = -1
        ## local item (record): colid = 0
        records.append((recid, colid, nb_notes, last_note, val, score))

    if external_recids:
        external_records = format_external_records(external_recids, of)

        for external_record in external_records:
            for record in records:
                if record[0] == -external_record[0]:
                    idx = records.index(record)
                    tuple_to_list = list(records.pop(idx))
                    tuple_to_list[4] = external_record[1]
                    records.insert(idx, tuple(tuple_to_list))
                    break

    if notes_dates:
        last_note = convert_datestruct_to_dategui(max(notes_dates), ln)

    if of == 'hb' or of.startswith('x'):

        body = webbasket_templates.tmpl_basket(bskid,
                                               basket_name,
                                               last_update,
                                               nb_items,
                                               nb_subscribers,
                                               (check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['READITM']),
                                                check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['MANAGE']),
                                                check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['READCMT']),
                                                check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['ADDCMT']),
                                                check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['ADDITM']),
                                                check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['DELITM'])),
                                               nb_total_notes,
                                               share_level,
                                               selected_category,
                                               selected_topic,
                                               selected_group_id,
                                               records,
                                               of,
                                               ln)
    else:
        body = ""
        for rec in records:
            body +=  rec[4]
    return (body, warnings)

def __display_basket_single_item(uid, bskid,
                                 basket_name,
                                 recid,
                                 last_update,
                                 nb_items,
                                 share_rights,
                                 selected_category=cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'],
                                 selected_topic="",
                                 selected_group_id=0,
                                 optional_params={},
                                 of='hb',
                                 ln=CFG_SITE_LANG):
    """Private function. Display a basket giving its category and topic or group.
    @param share_rights: rights user has on basket
    @param selected_category: selected category (see webbasket_config.py)
    @param selected_topic: # of selected topic to display baskets
    @param selected_group_id: id of group to display baskets
    @param ln: language"""

    _ = gettext_set_language(ln)

    warnings = []

    last_note = _("N/A")
    notes_dates = []
    #date_modification = convert_datetext_to_dategui(date_modification, ln)
    last_update = convert_datetext_to_dategui(last_update, ln)

    item = db.get_basket_item(bskid, recid, of)

    if item:
        (recid, collection_id, nb_notes, last_note, ext_val, int_val, score) = item[0]
        previous_item_recid = item[1]
        next_item_recid = item[2]
        item_index = item[3]
    else:
        share_level = db.get_basket_share_level(bskid)
        if share_level:
            share_level = share_level[0][0]
        else:
            share_level = None
        if share_level == 0:
            nb_subscribers = db.count_public_basket_subscribers(bskid)
        else:
            nb_subscribers = None
        (content, bsk_warnings) = __display_basket(uid, bskid,
                                                   basket_name,
                                                   last_update,
                                                   nb_items,
                                                   nb_subscribers,
                                                   share_rights,
                                                   share_level,
                                                   selected_category,
                                                   selected_topic,
                                                   selected_group_id,
                                                   of,
                                                   ln)
        try:
            raise InvenioWebBasketWarning(_('The selected item does not exist or you do not have access to it.'))
        except InvenioWebBasketWarning as exc:
            register_exception(stream='warning')
            bsk_warnings.append(exc.message)
        #bsk_warnings.append('WRN_WEBBASKET_INVALID_OR_RESTRICTED_ITEM')
        return (content, bsk_warnings)

    notes_dates.append(convert_datetext_to_datestruct(last_note))
    last_note = convert_datetext_to_dategui(last_note, ln)
    colid = collection_id and collection_id or collection_id == 0 and -1 or 0
    val = ""
    if recid < 0:
        if ext_val:
            val = decompress(ext_val)
        else:
            external_record = format_external_records([recid], of)
            val = external_record and external_record[0][1] or ""
    else:
        if int_val:
            val = decompress(int_val)
        else:
            val = format_record(recid, of, on_the_fly=True)
    item = (recid, colid, nb_notes, last_note, val, score)

    comments = db.get_notes(bskid, recid)

    if notes_dates:
        last_note = convert_datestruct_to_dategui(max(notes_dates), ln)

    body = webbasket_templates.tmpl_basket_single_item(bskid,
                                               basket_name,
                                               nb_items,
                                               (check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['READITM']),
                                                check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['READCMT']),
                                                check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['ADDCMT']),
                                                check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['DELCMT'])),
                                               selected_category,
                                               selected_topic,
                                               selected_group_id,
                                               item, comments,
                                               previous_item_recid, next_item_recid, item_index,
                                               optional_params,
                                               of,
                                               ln)
    return (body, warnings)

def perform_request_search(uid,
                           selected_category="",
                           selected_topic="",
                           selected_group_id=0,
                           p="",
                           b="",
                           n=0,
                           #format='xm',
                           ln=CFG_SITE_LANG):
    """Search the baskets...
    @param uid: user id
    @param category: selected category (see webbasket_config.py)
    @param selected_topic: # of selected topic to display baskets
    @param selected_group_id: id of group to display baskets
    @param ln: language"""

    _ = gettext_set_language(ln)

    body = ""
    #warnings = []
    warnings_html = ""

    (b_category, b_topic_or_grpid, b_warnings) = wash_b_search(b)
    # we extract the category from the washed b GET variable.
    # if a valid category was returned we use it as the selected category.
    if b_category:
        selected_category = b_category
        if selected_category == cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE']:
            selected_topic = b_topic_or_grpid
        elif selected_category == cfg['CFG_WEBBASKET_CATEGORIES']['GROUP']:
            selected_group_id = b_topic_or_grpid
    # if no category was returned and there were warnings it means there was a
    # bad input, send the warning to the user and return the page.
    elif b_warnings:
        navtrail = create_webbasket_navtrail(uid, search_baskets=True, ln=ln)
        body = webbasket_templates.tmpl_warnings(b_warnings, ln)
        return (body, navtrail)
    # if no category was returned and there were no warnings it means no category
    # was defined in the b GET variable. If the user has not defined a category
    # either using the category GET variable it means there is no category defined
    # whatsoever.
    elif not selected_category:
        selected_category = ""
    # finally, if no category was returned but the user has defined a category
    # using the category GET variable we extract the category after washing the
    # variable.
    else:
        (selected_category, category_warnings) = wash_category(selected_category)
        if not selected_category and category_warnings:
            navtrail = create_webbasket_navtrail(uid, search_baskets=True, ln=ln)
            body = webbasket_templates.tmpl_warnings(category_warnings, ln)
            return (body, navtrail)

    if selected_category == cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'] and selected_topic:
        (selected_topic, topic_warnings) = wash_topic(uid, selected_topic)
        if not selected_topic and topic_warnings:
            navtrail = create_webbasket_navtrail(uid, search_baskets=True, ln=ln)
            body = webbasket_templates.tmpl_warnings(topic_warnings, ln)
            return (body, navtrail)

    if selected_category == cfg['CFG_WEBBASKET_CATEGORIES']['GROUP'] and selected_group_id:
        (selected_group_id, group_warnings) = wash_group(uid, selected_group_id)
        if not selected_group_id and group_warnings:
            navtrail = create_webbasket_navtrail(uid, search_baskets=True, ln=ln)
            body = webbasket_templates.tmpl_warnings(group_warnings, ln)
            return (body, navtrail)

    # IDEA: in case we pass an "action=search" GET variable we can use the
    # following bit to warn the user he's searching for an empty search pattern.
    #if action == "search" and not p:
    #    warnings_html += webbasket_templates.tmpl_warnings('WRN_WEBBASKET_NO_SEARCH_PATTERN', ln)
    #    perform_search = 0

    if p:
        # Let's set some initial values
        personal_search_results = None
        total_no_personal_search_results = 0
        group_search_results = None
        total_no_group_search_results = 0
        public_search_results = None
        total_no_public_search_results = 0
        all_public_search_results = None
        total_no_all_public_search_results = 0
        # Let's precalculate the local search resutls
        # and the pattern for the external search results
        local_search_results = search_unit(p)

        # How strict should the pattern be? Look for the exact word
        # (using word boundaries: \b) or is any substring enough?

        # not that strict:
        # since we remove the html markup before searching for the pattern we
        # can use a rather simple pattern here.
        # INFO: we choose a not so strict pattern, since there are issues with
        # word bounderies and utf-8 strings (ex. with greek that was tested)
        pattern = re.compile(r'%s' % (re.escape(p),), re.DOTALL + re.MULTILINE + re.IGNORECASE + re.UNICODE)
        #pattern = re.compile(r'%s(?!([^<]+)?>)' % (p,), re.DOTALL + re.MULTILINE + re.IGNORECASE + re.UNICODE)

        # strict:
        # since we remove the html markup before searching for the pattern we
        # can use a rather simple pattern here.
        #pattern = re.compile(r'\b%s\b' % (re.escape(p),), re.DOTALL + re.MULTILINE + re.IGNORECASE + re.UNICODE)
        #pattern = re.compile(r'%s\b(?!([^<]+)?>)' % (p,), re.DOTALL + re.MULTILINE + re.IGNORECASE + re.UNICODE)

        # TODO: All the external records are now saved automatically first in xml.
        # So, the search should be done on the "xm" formatted records in the database
        # and not the "hb" ones. (That is not the case for their comments though).
        # Records in xml in the database are stored escaped. It's then suggested
        # that the pattern is also escaped before we performed the search for more
        # consistent resutls. We could also use .replace("\n", "") to clean the
        # content (after the removal of html markup) from all the newline characters.

        # The search format for external records. This means in which format will
        # the external records be fetched from the database to be searched then.
        format = 'xm'

        ### Calculate the search results for the user's personal baskets ###
        if b.startswith("P") or not b:
            personal_search_results = {}
            personal_items = db.get_all_items_in_user_personal_baskets(uid, selected_topic, format)
            personal_local_items = personal_items[0]
            personal_external_items = personal_items[1]
            personal_external_items_xml_records = {}

            for local_info_per_basket in personal_local_items:
                bskid       = local_info_per_basket[0]
                basket_name = local_info_per_basket[1]
                topic       = local_info_per_basket[2]
                recid_list  = local_info_per_basket[3]
                local_recids_per_basket = intbitset(map(int, recid_list.strip(',').split(',')))
                intsec = local_search_results.intersection(local_recids_per_basket)
                if intsec:
                    personal_search_results[bskid] = [basket_name, topic, len(intsec), list(intsec)]
                    total_no_personal_search_results += len(intsec)

            for external_info_per_basket in personal_external_items:
                bskid       = external_info_per_basket[0]
                basket_name = external_info_per_basket[1]
                topic       = external_info_per_basket[2]
                recid       = external_info_per_basket[3]
                value       = external_info_per_basket[4]
                xml_record  = decompress(value)
                personal_external_items_xml_records[recid] = xml_record
                text = remove_html_markup(xml_record, remove_escaped_chars_p=False)
                text = unescape(text)
                #text = text.replace('\n', '')
                result = pattern.search(text)
                if result:
                    if bskid in personal_search_results:
                        personal_search_results[bskid][2] += 1
                        personal_search_results[bskid][3].append(recid)
                    else:
                        personal_search_results[bskid] = [basket_name, topic, 1, [recid]]
                    total_no_personal_search_results += 1

            if n:
                personal_items_by_matching_notes = db.get_all_items_in_user_personal_baskets_by_matching_notes(uid, selected_topic, p)
                for info_per_basket_by_matching_notes in personal_items_by_matching_notes:
                    bskid       = info_per_basket_by_matching_notes[0]
                    basket_name = info_per_basket_by_matching_notes[1]
                    topic       = info_per_basket_by_matching_notes[2]
                    recid_list  = info_per_basket_by_matching_notes[3]
                    recids_per_basket_by_matching_notes = set(map(int, recid_list.strip(',').split(',')))
                    if bskid in personal_search_results:
                        no_personal_search_results_per_basket_so_far = personal_search_results[bskid][2]
                        personal_search_results[bskid][3] = list(set(personal_search_results[bskid][3]).union(recids_per_basket_by_matching_notes))
                        personal_search_results[bskid][2] = len(personal_search_results[bskid][3])
                        total_no_personal_search_results += ( personal_search_results[bskid][2] - no_personal_search_results_per_basket_so_far )
                    else:
                        personal_search_results[bskid] = [basket_name, topic, len(recids_per_basket_by_matching_notes), list(recids_per_basket_by_matching_notes)]
                        total_no_personal_search_results += len(recids_per_basket_by_matching_notes)

            # For every found record: calculate the number of notes
            # and the HTML representation of the record.
            for bskid in personal_search_results.keys():
                recids = personal_search_results[bskid][3]
                number_of_notes_per_record = db.get_number_of_notes_per_record_in_basket(bskid, recids)
                records = []
                for recid_and_notes in number_of_notes_per_record:
                    recid = recid_and_notes[0]
                    number_of_notes = recid_and_notes[1]
                    if recid < 0:
                        xml_record = personal_external_items_xml_records[recid]
                        record_html = format_record(None, of='bsr', xml_record=xml_record)
                        records.append((recid, number_of_notes, record_html))
                    else:
                        record_html = format_record(recid, of='bsr', on_the_fly=True)
                        records.append((recid, number_of_notes, record_html))
                personal_search_results[bskid][3] = records

        ### Calculate the search results for the user's group baskets ###
        if b.startswith("G") or not b:
            group_search_results = {}
            group_items = db.get_all_items_in_user_group_baskets(uid, selected_group_id, format)
            group_local_items = group_items[0]
            group_external_items = group_items[1]
            group_external_items_xml_records = {}

            for local_info_per_basket in group_local_items:
                bskid       = local_info_per_basket[0]
                basket_name = local_info_per_basket[1]
                grpid       = local_info_per_basket[2]
                group_name  = local_info_per_basket[3]
                share_rights = local_info_per_basket[4]
                recid_list  = local_info_per_basket[5]
                local_recids_per_basket = intbitset(map(int, recid_list.strip(',').split(',')))
                intsec = local_search_results.intersection(local_recids_per_basket)
                if intsec:
                    share_rights_view_notes = check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['READCMT'])
                    share_rights_add_notes  = check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['ADDCMT'])
                    share_rights_notes = (share_rights_view_notes, share_rights_add_notes)
                    group_search_results[bskid] = [basket_name, grpid, group_name, share_rights_notes, len(intsec), list(intsec)]
                    total_no_group_search_results += len(intsec)

            for external_info_per_basket in group_external_items:
                bskid       = external_info_per_basket[0]
                basket_name = external_info_per_basket[1]
                grpid       = external_info_per_basket[2]
                group_name  = external_info_per_basket[3]
                share_rights = external_info_per_basket[4]
                recid       = external_info_per_basket[5]
                value       = external_info_per_basket[6]
                xml_record  = decompress(value)
                group_external_items_xml_records[recid] = xml_record
                text = remove_html_markup(xml_record, remove_escaped_chars_p=False)
                text = unescape(text)
                #text = text.replace('\n', '')
                result = pattern.search(text)
                if result:
                    if bskid in group_search_results:
                        group_search_results[bskid][4] += 1
                        group_search_results[bskid][5].append(recid)
                    else:
                        share_rights_view_notes = check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['READCMT'])
                        share_rights_add_notes  = check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['ADDCMT'])
                        share_rights_notes = (share_rights_view_notes, share_rights_add_notes)
                        group_search_results[bskid] = [basket_name, grpid, group_name, share_rights_notes, 1, [recid]]
                    total_no_group_search_results += 1

            if n:
                group_items_by_matching_notes = db.get_all_items_in_user_group_baskets_by_matching_notes(uid, selected_group_id, p)
                for info_per_basket_by_matching_notes in group_items_by_matching_notes:
                    bskid       = info_per_basket_by_matching_notes[0]
                    basket_name = info_per_basket_by_matching_notes[1]
                    grpid       = info_per_basket_by_matching_notes[2]
                    group_name  = info_per_basket_by_matching_notes[3]
                    share_rights = info_per_basket_by_matching_notes[4]
                    recid_list  = info_per_basket_by_matching_notes[5]
                    recids_per_basket_by_matching_notes = set(map(int, recid_list.strip(',').split(',')))
                    if bskid in group_search_results:
                        no_group_search_results_per_basket_so_far = group_search_results[bskid][4]
                        group_search_results[bskid][5] = list(set(group_search_results[bskid][5]).union(recids_per_basket_by_matching_notes))
                        group_search_results[bskid][4] = len(group_search_results[bskid][5])
                        total_no_group_search_results += ( group_search_results[bskid][4] - no_group_search_results_per_basket_so_far )
                    else:
                        share_rights_view_notes = check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['READCMT'])
                        share_rights_add_notes  = check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['ADDCMT'])
                        share_rights_notes = (share_rights_view_notes, share_rights_add_notes)
                        group_search_results[bskid] = [basket_name, grpid, group_name, share_rights_notes, len(recids_per_basket_by_matching_notes), list(recids_per_basket_by_matching_notes)]
                        total_no_group_search_results += len(recids_per_basket_by_matching_notes)

            # For every found record: calculate the number of notes
            # and the HTML representation of the record.
            for bskid in group_search_results.keys():
                recids = group_search_results[bskid][5]
                number_of_notes_per_record = db.get_number_of_notes_per_record_in_basket(bskid, recids)
                records = []
                for recid_and_notes in number_of_notes_per_record:
                    recid = recid_and_notes[0]
                    number_of_notes = recid_and_notes[1]
                    if recid < 0:
                        xml_record = group_external_items_xml_records[recid]
                        record_html = format_record(None, of='bsr', xml_record=xml_record)
                        records.append((recid, number_of_notes, record_html))
                    else:
                        record_html = format_record(recid, of='bsr', on_the_fly=True)
                        records.append((recid, number_of_notes, record_html))
                group_search_results[bskid][5] = records

        ### Calculate the search results for the user's public baskets ###
        if b.startswith("E") or not b:
            public_search_results = {}
            public_items = db.get_all_items_in_user_public_baskets(uid, format)
            public_local_items = public_items[0]
            public_external_items = public_items[1]
            public_external_items_xml_records = {}

            for local_info_per_basket in public_local_items:
                bskid       = local_info_per_basket[0]
                basket_name = local_info_per_basket[1]
                share_rights = local_info_per_basket[2]
                recid_list  = local_info_per_basket[3]
                local_recids_per_basket = intbitset(map(int, recid_list.strip(',').split(',')))
                intsec = local_search_results.intersection(local_recids_per_basket)
                if intsec:
                    share_rights_view_notes = check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['READCMT'])
                    share_rights_add_notes  = check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['ADDCMT'])
                    share_rights_notes = (share_rights_view_notes, share_rights_add_notes)
                    public_search_results[bskid] = [basket_name, share_rights_notes, len(intsec), list(intsec)]
                    total_no_public_search_results += len(intsec)

            for external_info_per_basket in public_external_items:
                bskid       = external_info_per_basket[0]
                basket_name = external_info_per_basket[1]
                share_rights = external_info_per_basket[2]
                recid       = external_info_per_basket[3]
                value       = external_info_per_basket[4]
                xml_record  = decompress(value)
                public_external_items_xml_records[recid] = xml_record
                text = remove_html_markup(xml_record, remove_escaped_chars_p=False)
                text = unescape(text)
                #text = text.replace('\n', '')
                result = pattern.search(text)
                if result:
                    if bskid in public_search_results:
                        public_search_results[bskid][2] += 1
                        public_search_results[bskid][3].append(recid)
                    else:
                        share_rights_view_notes = check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['READCMT'])
                        share_rights_add_notes  = check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['ADDCMT'])
                        share_rights_notes = (share_rights_view_notes, share_rights_add_notes)
                        public_search_results[bskid] = [basket_name, share_rights_notes, 1, [recid]]
                    total_no_public_search_results += 1

            if n:
                public_items_by_matching_notes = db.get_all_items_in_user_public_baskets_by_matching_notes(uid, p)
                for info_per_basket_by_matching_notes in public_items_by_matching_notes:
                    bskid       = info_per_basket_by_matching_notes[0]
                    basket_name = info_per_basket_by_matching_notes[1]
                    share_rights = info_per_basket_by_matching_notes[2]
                    recid_list  = info_per_basket_by_matching_notes[3]
                    recids_per_basket_by_matching_notes = set(map(int, recid_list.strip(',').split(',')))
                    if bskid in public_search_results:
                        no_public_search_results_per_basket_so_far = public_search_results[bskid][2]
                        public_search_results[bskid][3] = list(set(public_search_results[bskid][3]).union(recids_per_basket_by_matching_notes))
                        public_search_results[bskid][2] = len(public_search_results[bskid][3])
                        total_no_public_search_results += ( public_search_results[bskid][2] - no_public_search_results_per_basket_so_far )
                    else:
                        share_rights_view_notes = check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['READCMT'])
                        share_rights_add_notes  = check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['ADDCMT'])
                        share_rights_notes = (share_rights_view_notes, share_rights_add_notes)
                        public_search_results[bskid] = [basket_name, share_rights_notes, len(recids_per_basket_by_matching_notes), list(recids_per_basket_by_matching_notes)]
                        total_no_public_search_results += len(recids_per_basket_by_matching_notes)

            # For every found record: calculate the number of notes
            # and the HTML representation of the record.
            for bskid in public_search_results.keys():
                recids = public_search_results[bskid][3]
                number_of_notes_per_record = db.get_number_of_notes_per_record_in_basket(bskid, recids)
                records = []
                for recid_and_notes in number_of_notes_per_record:
                    recid = recid_and_notes[0]
                    number_of_notes = recid_and_notes[1]
                    if recid < 0:
                        xml_record = public_external_items_xml_records[recid]
                        record_html = format_record(None, of='bsr', xml_record=xml_record)
                        records.append((recid, number_of_notes, record_html))
                    else:
                        record_html = format_record(recid, of='bsr', on_the_fly=True)
                        records.append((recid, number_of_notes, record_html))
                public_search_results[bskid][3] = records

        ### Calculate the search results for all the public baskets ###
        if b.startswith("A"):
            all_public_search_results = {}
            all_public_items = db.get_all_items_in_all_public_baskets(format)
            all_public_local_items = all_public_items[0]
            all_public_external_items = all_public_items[1]
            all_public_external_items_xml_records = {}

            for local_info_per_basket in all_public_local_items:
                bskid       = local_info_per_basket[0]
                basket_name = local_info_per_basket[1]
                share_rights = local_info_per_basket[2]
                recid_list  = local_info_per_basket[3]
                local_recids_per_basket = intbitset(map(int, recid_list.strip(',').split(',')))
                intsec = local_search_results.intersection(local_recids_per_basket)
                if intsec:
                    share_rights_view_notes = check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['READCMT'])
                    share_rights_add_notes  = check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['ADDCMT'])
                    share_rights_notes = (share_rights_view_notes, share_rights_add_notes)
                    all_public_search_results[bskid] = [basket_name, share_rights_notes, len(intsec), list(intsec)]
                    total_no_all_public_search_results += len(intsec)

            for external_info_per_basket in all_public_external_items:
                bskid       = external_info_per_basket[0]
                basket_name = external_info_per_basket[1]
                share_rights = external_info_per_basket[2]
                recid       = external_info_per_basket[3]
                value       = external_info_per_basket[4]
                xml_record  = decompress(value)
                all_public_external_items_xml_records[recid] = xml_record
                text = remove_html_markup(xml_record, remove_escaped_chars_p=False)
                text = unescape(text)
                #text = text.replace('\n', '')
                result = pattern.search(text)
                if result:
                    if bskid in all_public_search_results:
                        all_public_search_results[bskid][2] += 1
                        all_public_search_results[bskid][3].append(recid)
                    else:
                        share_rights_view_notes = check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['READCMT'])
                        share_rights_add_notes  = check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['ADDCMT'])
                        share_rights_notes = (share_rights_view_notes, share_rights_add_notes)
                        all_public_search_results[bskid] = [basket_name, share_rights_notes, 1, [recid]]
                    total_no_all_public_search_results += 1

            if n:
                all_public_items_by_matching_notes = db.get_all_items_in_all_public_baskets_by_matching_notes(p)
                for info_per_basket_by_matching_notes in all_public_items_by_matching_notes:
                    bskid       = info_per_basket_by_matching_notes[0]
                    basket_name = info_per_basket_by_matching_notes[1]
                    share_rights = info_per_basket_by_matching_notes[2]
                    recid_list  = info_per_basket_by_matching_notes[3]
                    recids_per_basket_by_matching_notes = set(map(int, recid_list.strip(',').split(',')))
                    if bskid in all_public_search_results:
                        no_all_public_search_results_per_basket_so_far = all_public_search_results[bskid][2]
                        all_public_search_results[bskid][3] = list(set(all_public_search_results[bskid][3]).union(recids_per_basket_by_matching_notes))
                        all_public_search_results[bskid][2] = len(all_public_search_results[bskid][3])
                        total_no_all_public_search_results += ( all_public_search_results[bskid][2] - no_all_public_search_results_per_basket_so_far )
                    else:
                        share_rights_view_notes = check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['READCMT'])
                        share_rights_add_notes  = check_sufficient_rights(share_rights, cfg['CFG_WEBBASKET_SHARE_LEVELS']['ADDCMT'])
                        share_rights_notes = (share_rights_view_notes, share_rights_add_notes)
                        all_public_search_results[bskid] = [basket_name, share_rights_notes, len(recids_per_basket_by_matching_notes), list(recids_per_basket_by_matching_notes)]
                        total_no_all_public_search_results += len(recids_per_basket_by_matching_notes)

            # For every found record: calculate the number of notes
            # and the HTML representation of the record.
            for bskid in all_public_search_results.keys():
                recids = all_public_search_results[bskid][3]
                number_of_notes_per_record = db.get_number_of_notes_per_record_in_basket(bskid, recids)
                records = []
                for recid_and_notes in number_of_notes_per_record:
                    recid = recid_and_notes[0]
                    number_of_notes = recid_and_notes[1]
                    if recid < 0:
                        xml_record = all_public_external_items_xml_records[recid]
                        record_html = format_record(None, of='bsr', xml_record=xml_record)
                        records.append((recid, number_of_notes, record_html))
                    else:
                        record_html = format_record(recid, of='bsr', on_the_fly=True)
                        records.append((recid, number_of_notes, record_html))
                all_public_search_results[bskid][3] = records

        search_results_html = webbasket_templates.tmpl_search_results(personal_search_results,
                                                                      total_no_personal_search_results,
                                                                      group_search_results,
                                                                      total_no_group_search_results,
                                                                      public_search_results,
                                                                      total_no_public_search_results,
                                                                      all_public_search_results,
                                                                      total_no_all_public_search_results,
                                                                      ln)
    else:
        search_results_html = None

    search_box = __create_search_box(uid=uid,
                                     category=selected_category,
                                     topic=selected_topic,
                                     grpid=selected_group_id,
                                     p=p,
                                     n=n,
                                     ln=ln)

    body = webbasket_templates.tmpl_display(search_box=search_box,
                                            search_results=search_results_html)
    body = warnings_html + body

    navtrail = create_webbasket_navtrail(uid,
                                         search_baskets=True,
                                         ln=ln)

    return (body, navtrail)

def perform_request_write_note(uid,
                               category=cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'],
                               topic="",
                               group_id=0,
                               bskid=0,
                               recid=0,
                               cmtid=0,
                               ln=CFG_SITE_LANG):
    """Display a note writing form
    @param uid: user id
    @param bskid: basket id
    @param recid: record id (comments are on a specific record in a specific basket)
    @param cmtid: if provided this comment is a reply to comment cmtid.
    @param category: selected category
    @param topic: selected topic
    @param group_id: selected group id
    @param ln: language
    """
    _ = gettext_set_language(ln)

    optional_params = {}
    #warnings_rights = []
    warnings_html = ""

    if not check_user_can_comment(uid, bskid):
        try:
            raise InvenioWebBasketWarning(_('You do not have permission to write notes to this item.'))
        except InvenioWebBasketWarning as exc:
            register_exception(stream='warning')
        #warnings_rights = ['WRN_WEBBASKET_RESTRICTED_WRITE_NOTES']
        warnings_html += webbasket_templates.tmpl_warnings(exc.message, ln)
    else:
        if cmtid and db.note_belongs_to_item_in_basket_p(cmtid, recid, bskid):
            optional_params["Add note"] = db.get_note(cmtid)
            optional_params["Reply to"] = cmtid
        elif cmtid:
            optional_params["Add note"] = ()
            try:
                raise InvenioWebBasketWarning(_('The note you are quoting does not exist or you do not have access to it.'))
            except InvenioWebBasketWarning as exc:
                register_exception(stream='warning')
                optional_params["Warnings"] = exc.message
        else:
            optional_params["Add note"] = ()

    (body, warnings, navtrail) = perform_request_display(uid=uid,
                                                         selected_category=category,
                                                         selected_topic=topic,
                                                         selected_group_id=group_id,
                                                         selected_bskid=bskid,
                                                         selected_recid=recid,
                                                         optional_params=optional_params,
                                                         of='hb',
                                                         ln=CFG_SITE_LANG)

    if not warnings:
        body = warnings_html + body
        #warnings = warnings_rights

    return (body, navtrail)

def perform_request_save_note(uid,
                              category=cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'],
                              topic="",
                              group_id=0,
                              bskid=0,
                              recid=0,
                              note_title="",
                              note_body="",
                              editor_type='textarea',
                              date_creation="",
                              ln=CFG_SITE_LANG,
                              reply_to=None):
    """ Save a given comment if able to.
    @param uid: user id (int)
    @param bskid: basket id (int)
    @param recid: record id (int)
    @param title: title of comment (string)
    @param text: comment's body (string)
    @param ln: language (string)
    @param editor_type: the kind of editor/input used for the comment: 'textarea', 'ckeditor'
    @param reply_to: the id of the comment we are replying to
    """
    _ = gettext_set_language(ln)

    optional_params = {}
    #warnings_rights = []
    warnings_html = ""

    if not check_user_can_comment(uid, bskid):
        try:
            raise InvenioWebBasketWarning(_('You do not have permission to write notes to this item.'))
        except InvenioWebBasketWarning as exc:
            register_exception(stream='warning')
            #warnings_rights = exc.message
        #warnings_rights = ['WRN_WEBBASKET_RESTRICTED_WRITE_NOTES']
        warnings_html += webbasket_templates.tmpl_warnings(exc.message, ln)
    else:
        if not note_title or \
           ((not note_body and editor_type != 'ckeditor') or \
            (not remove_html_markup(note_body, '').replace('\n', '').replace('\r', '').strip() and editor_type == 'ckeditor')):
            optional_params["Incomplete note"] = (note_title, note_body)
            try:
                raise InvenioWebBasketWarning(_('You must fill in both the subject and the body of the note.'))
            except InvenioWebBasketWarning as exc:
                register_exception(stream='warning')
                optional_params["Warnings"] = exc.message
        else:
            if editor_type == 'ckeditor':
                # Here we remove the line feeds introduced by CKEditor (they
                # have no meaning for the user) and replace the HTML line
                # breaks by linefeeds, so that we are close to an input that
                # would be done without the CKEditor. That's much better if a
                # reply to a comment is made with a browser that does not
                # support CKEditor.
                note_body = note_body.replace('\n', '').replace('\r', '').replace('<br />', '\n')
            if not(db.save_note(uid, bskid, recid, note_title, note_body, date_creation, reply_to)):
                # TODO: The note could not be saved. DB problem?
                pass
            else:
                # TODO: inform about successful annotating.
                pass

    (body, warnings, navtrail) = perform_request_display(uid=uid,
                                                         selected_category=category,
                                                         selected_topic=topic,
                                                         selected_group_id=group_id,
                                                         selected_bskid=bskid,
                                                         selected_recid=recid,
                                                         optional_params=optional_params,
                                                         of='hb',
                                                         ln=CFG_SITE_LANG)

    if not warnings:
        body = warnings_html + body
        #warnings = warnings_rights

    return (body, navtrail)

def perform_request_delete_note(uid,
                                category=cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'],
                                topic="",
                                group_id=0,
                                bskid=0,
                                recid=0,
                                cmtid=0,
                                ln=CFG_SITE_LANG):
    """Delete comment cmtid on record recid for basket bskid."""

    _ = gettext_set_language(ln)

    #warnings_notes = []
    warnings_html = ""

    if not __check_user_can_perform_action(uid, bskid, cfg['CFG_WEBBASKET_SHARE_LEVELS']['DELCMT']):
        try:
            raise InvenioWebBasketWarning(_('You do not have permission to delete this note.'))
        except InvenioWebBasketWarning as exc:
            register_exception(stream='warning')
            #warnings_notes.append(exc.message)
        #warnings_notes.append('WRN_WEBBASKET_RESTRICTED_DELETE_NOTES')
        warnings_html += webbasket_templates.tmpl_warnings(exc.message, ln)
    else:
        if cmtid and db.note_belongs_to_item_in_basket_p(cmtid, recid, bskid):
            db.delete_note(bskid, recid, cmtid)
        else:
            try:
                raise InvenioWebBasketWarning(_('The note you are deleting does not exist or you do not have access to it.'))
            except InvenioWebBasketWarning as exc:
                register_exception(stream='warning')
                #warnings_notes.append(exc.message)
            #warnings_notes.append('WRN_WEBBASKET_DELETE_INVALID_NOTE')
            warnings_html += webbasket_templates.tmpl_warnings(exc.message, ln)

    (body, warnings, navtrail) = perform_request_display(uid=uid,
                                                         selected_category=category,
                                                         selected_topic=topic,
                                                         selected_group_id=group_id,
                                                         selected_bskid=bskid,
                                                         selected_recid=recid,
                                                         of='hb',
                                                         ln=CFG_SITE_LANG)

    body = warnings_html + body
    #warnings.extend(warnings_notes)

    return (body, navtrail)

def perform_request_add(uid,
                        recids=[],
                        category='',
                        bskid=0,
                        colid=0,
                        es_title='',
                        es_desc='',
                        es_url='',
                        note_body='',
                        date_creation='',
                        editor_type='',
                        b='',
                        successful_add=False,
                        copy=False,
                        wait=False,
                        move_from_basket=0,
                        referer='',
                        ln=CFG_SITE_LANG):
    """Add records to baskets
    @param uid: user id
    @param recids: list of records to add
    @param colid: in case of external collections, the id of the collection the records belong to
    @param bskids: list of baskets to add records to. if not provided, will return a
                   page where user can select baskets
    @param es_title: the title of the external source
    @param es_desc: the description of the external source
    @param es_url: the url of the external source
    @param move_from_basket: instead of creating a new item, move the item with
                             the specified recid from another basket

    @param referer: URL of the referring page
    @param ln: language"""

    _ = gettext_set_language(ln)

    if successful_add:
        body = webbasket_templates.tmpl_add(recids=recids,
                                            category=category,
                                            bskid=bskid,
                                            colid=colid,
                                            successful_add=True,
                                            copy=copy,
                                            referer=referer,
                                            ln=ln)
        #warnings = []
        navtrail = create_webbasket_navtrail(uid,
                                             add_to_basket=True,
                                             ln=ln)
        return (body, navtrail)

    #warnings = []
    warnings_html = ""

    if type(recids) is not list:
        recids = [recids]

    validated_recids = []

    if colid == 0:
        # Local records
        for recid in recids:
            recid = int(recid)
            if recid > 0 and record_exists(recid) == 1:
                validated_recids.append(recid)
            elif recid < 0 and copy:
                # if we are copying a record, colid will always be 0 but we may
                # still get negative recids when it comes to external items.
                # In that case, we just skip the checking and add them directly
                # to the validated_recids.
                validated_recids.append(recid)
        user_info = collect_user_info(uid)
        recids_to_remove = []
        for recid in validated_recids:
            (auth_code, dummy) = check_user_can_view_record(user_info, recid)
            if auth_code:
                # User is not authorized to view record.
                # We should not remove items from the list while we parse it.
                # Better store them in another list and in the end remove them.
                #validated_recids.remove(recid)
                recids_to_remove.append(recid)
                try:
                    raise InvenioWebBasketWarning(_('Sorry, you do not have sufficient rights to add record #%(x_id)i.', x_id=recid))
                except InvenioWebBasketWarning as exc:
                    register_exception(stream='warning')
                    #warnings.append(exc.message)
                #warnings.append(('WRN_WEBBASKET_NO_RIGHTS_TO_ADD_THIS_RECORD', recid))
                try:
                    raise InvenioWebBasketWarning(_('Some of the items were not added due to lack of sufficient rights.'))
                except InvenioWebBasketWarning as exc:
                    register_exception(stream='warning')
                    warnings_html = webbasket_templates.tmpl_warnings(exc.message, ln)
                    #warnings_html = webbasket_templates.tmpl_warnings('WRN_WEBBASKET_NO_RIGHTS_TO_ADD_RECORDS', ln)
        for recid in recids_to_remove:
            validated_recids.remove(recid)

    elif colid > 0:
        # External records, no need to validate.
        validated_recids.extend(recids)

    elif colid == -1:
        # External source.
        es_warnings = []
        if not es_title:
            try:
                raise InvenioWebBasketWarning(_('Please provide a title for the external source.'))
            except InvenioWebBasketWarning as exc:
                register_exception(stream='warning')
                es_warnings.append(exc.message)
        if not es_desc:
            try:
                raise InvenioWebBasketWarning(_('Please provide a description for the external source.'))
            except InvenioWebBasketWarning as exc:
                register_exception(stream='warning')
                es_warnings.append(exc.message)
        if not es_url:
            try:
                raise InvenioWebBasketWarning(_('Please provide a url for the external source.'))
            except InvenioWebBasketWarning as exc:
                register_exception(stream='warning')
                es_warnings.append(exc.message)
        else:
            (is_valid, status, dummy) = url_is_valid(es_url)
            if not is_valid:
                if str(status).startswith('0'):
                    try:
                        raise InvenioWebBasketWarning(_('The url you have provided is not valid.'))
                    except InvenioWebBasketWarning as exc:
                        register_exception(stream='warning')
                        es_warnings.append(exc.message)
                    #es_warnings.append('WRN_WEBBASKET_NO_VALID_URL_0')
                elif str(status).startswith('4'):
                    try:
                        raise InvenioWebBasketWarning(_('The url you have provided is not valid: The request contains bad syntax or cannot be fulfilled.'))
                    except InvenioWebBasketWarning as exc:
                        register_exception(stream='warning')
                        es_warnings.append(exc.message)
                    #es_warnings.append('WRN_WEBBASKET_NO_VALID_URL_4')
                elif str(status).startswith('5'):
                    try:
                        raise InvenioWebBasketWarning(_('The url you have provided is not valid: The server failed to fulfil an apparently valid request.'))
                    except InvenioWebBasketWarning as exc:
                        register_exception(stream='warning')
                        es_warnings.append(exc.message)
                    #es_warnings.append('WRN_WEBBASKET_NO_VALID_URL_5')
            elif not (es_url.startswith("http://") or es_url.startswith("https://")):
                es_url = "http://" + es_url
        if es_warnings:
            #warnings.extend(es_warnings)
            warnings_html += webbasket_templates.tmpl_warnings(es_warnings, ln)

    if not validated_recids:
        # in case there are no record ids select assume we want to add an
        # external source.
        colid = -1

    # This part of code is under the current circumstances never ran,
    # since if there no validated_recids, colid is set to -1.
    # IDEA: colid should by default (i.e. when not set) be -2 and when local
    # recids are added we should use the 0 value.
    #if not validated_recids and colid >= 0:
    #    warnings.append('WRN_WEBBASKET_NO_RECORD')
    #    body += webbasket_templates.tmpl_warnings(warnings, ln)
    #    if referer and not(referer.find(CFG_SITE_URL) == -1):
    #        body += webbasket_templates.tmpl_back_link(referer, ln)
    #    return (body, warnings)

    if b or (category and bskid):
        # if b was not defined we use category and bskid to construct it.
        if not b:
            b = category + "_" + str(bskid)
        # we extract the category and  the bskid from the washed b POST variable
        # or the constracted b variable from category and bskid.
        (category, b_bskid, b_warnings) = wash_b_add(b)
        # if there were warnings it means there was a bad input.
        # Send the warning to the user and return the page.
        if b_warnings:
            #warnings.extend(b_warnings)
            warnings_html += webbasket_templates.tmpl_warnings(b_warnings, ln)
        if not b_warnings:
            (bskid, b_warnings) = wash_bskid(uid, category, b_bskid)
            if b_warnings:
                #warnings.extend(b_warnings)
                warnings_html += webbasket_templates.tmpl_warnings(b_warnings, ln)
                if not b_warnings:
                    if not(__check_user_can_perform_action(uid,
                                                           bskid,
                                                           cfg['CFG_WEBBASKET_SHARE_LEVELS']['ADDITM'])):
                        try:
                            raise InvenioWebBasketWarning(_('Sorry, you do not have sufficient rights on this basket.'))
                        except InvenioWebBasketWarning as exc:
                            register_exception(stream='warning')
                            #warnings.append(exc.message)
                        #warnings.append('WRN_WEBBASKET_NO_RIGHTS')
                        warnings_html += webbasket_templates.tmpl_warnings(exc.message, ln)

                    # To move an item, user needs add and delete permissions
                    if move_from_basket > 0 and not(__check_user_can_perform_action(uid,
                                                    move_from_basket,
                                                    cfg['CFG_WEBBASKET_SHARE_LEVELS']['DELITM'])):
                        try:
                            raise InvenioWebBasketWarning(_('Sorry, you do not have sufficient rights on this basket.'))
                        except InvenioWebBasketWarning as exc:
                            register_exception(stream='warning')
                            #warnings.append(exc.message)
                        #warnings.append('WRN_WEBBASKET_NO_RIGHTS')
                        warnings_html += webbasket_templates.tmpl_warnings(exc.message, ln)

        if not warnings_html:
            if ( colid >= 0 and not validated_recids ) or ( colid == -1 and ( not es_title or not es_desc or not es_url ) ):
                try:
                    raise InvenioWebBasketWarning(_('No records to add.'))
                except InvenioWebBasketWarning as exc:
                    register_exception(stream='warning')
                    #warnings.append(exc.message)
            if not warnings_html and not wait:
                if colid == -1:
                    es_title = es_title
                    es_desc = nl2br(es_desc)

                if move_from_basket > 0:
                    added_items = db.move_to_basket(uid, validated_recids, move_from_basket, bskid)
                else:
                    added_items = db.add_to_basket(uid, validated_recids, colid, bskid, es_title, es_desc, es_url)

                if added_items:

                    if (note_body and editor_type != 'ckeditor') or \
                           (editor_type == 'ckeditor' and \
                            remove_html_markup(note_body, '').replace('\n', '').replace('\r', '').strip()):
                        if editor_type == 'ckeditor':
                            # Here we remove the line feeds introduced by CKEditor (they
                            # have no meaning for the user) and replace the HTML line
                            # breaks by linefeeds, so that we are close to an input that
                            # would be done without the CKEditor. That's much better if a
                            # reply to a comment is made with a browser that does not
                            # support CKEditor.
                            note_title = ''
                            note_body = note_body.replace('\n', '').replace('\r', '').replace('<br />', '\n')
                        else:
                            note_title = ''
                        for recid in added_items:
                            if not(db.save_note(uid, bskid, recid, note_title, note_body, date_creation, reply_to=None)):
                                # TODO: The note could not be saved. DB problem?
                                pass
                    if colid > 0:
                        format_external_records(added_items, of="xm")
                    return perform_request_add(uid=uid,
                                               recids=recids,
                                               category=category,
                                               bskid=bskid,
                                               colid=colid,
                                               successful_add=True,
                                               copy=copy,
                                               referer=referer)
                else:
                    try:
                        if move_from_basket > 0 and len(validated_recids) > len(added_items):
                            raise InvenioWebBasketWarning(_('Some items could not be moved. The destination basket already contains those items.'))
                        else:
                            raise InvenioWebBasketWarning(_('Cannot add items to the selected basket. Invalid parameters.'))
                    except InvenioWebBasketWarning as exc:
                        register_exception(stream='warning')
                        #warnings.append(exc.message)
                    #warnings.append('WRN_WEBBASKET_INVALID_ADD_TO_PARAMETERS')
                    warnings_html += webbasket_templates.tmpl_warnings(exc.message, ln)

    personal_basket_list = db.get_all_user_personal_basket_ids_by_topic(uid)
    group_basket_list = db.get_all_user_group_basket_ids_by_group_with_add_rights(uid)
    if not personal_basket_list and not group_basket_list:
        bskid = db.create_basket(uid=uid, basket_name=_('Untitled basket'), topic=_('Untitled topic'))
        try:
            raise InvenioWebBasketWarning(_('A default topic and basket have been automatically created. Edit them to rename them as you see fit.'))
        except InvenioWebBasketWarning as exc:
            register_exception(stream='warning')
            #warnings.append(exc.message)
        #warnings.append('WRN_WEBBASKET_DEFAULT_TOPIC_AND_BASKET')
        warnings_html += webbasket_templates.tmpl_warnings(exc.message, ln)
        if colid >= 0 and validated_recids:
            (body, navtrail) = perform_request_add(uid=uid,
                                                   recids=validated_recids,
                                                   category=cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'],
                                                   bskid=bskid,
                                                   colid=colid,
                                                   referer=referer,
                                                   ln=ln)
            body = warnings_html + body
            return (body, navtrail)
        else:
            personal_basket_list = db.get_all_user_personal_basket_ids_by_topic(uid)

    body = webbasket_templates.tmpl_add(recids=recids,
                                        category=category,
                                        bskid=bskid,
                                        colid=colid,
                                        es_title=es_title,
                                        es_desc=es_desc,
                                        es_url=es_url,
                                        note_body=note_body,
                                        personal_basket_list=personal_basket_list,
                                        group_basket_list=group_basket_list,
                                        copy=copy,
                                        move_from_basket=move_from_basket,
                                        referer=referer,
                                        ln=ln)

    body = warnings_html + body

    navtrail = create_webbasket_navtrail(uid,
                                         add_to_basket=True,
                                         ln=ln)

    return (body, navtrail)

def perform_request_delete(uid, bskid, confirmed=0,
                           category=cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'],
                           selected_topic="", selected_group_id=0,
                           ln=CFG_SITE_LANG):
    """Delete a given basket.
    @param uid: user id (user has to be owner of this basket)
    @param bskid: basket id
    @param confirmed: if 0 will return a confirmation page; if 1 will delete basket.
    @param category: category currently displayed
    @param selected_topic: topic currently displayed
    @param selected_group_id: if category is group, id of the group currently displayed
    @param ln: language"""

    _ = gettext_set_language(ln)

    body = ''
    #warnings = []
    if not(db.check_user_owns_baskets(uid, [bskid])):
        try:
            raise InvenioWebBasketWarning(_('Sorry, you do not have sufficient rights on this basket.'))
        except InvenioWebBasketWarning as exc:
            register_exception(stream='warning')
            #warnings.append(exc.message)
        #warnings.append(('WRN_WEBBASKET_NO_RIGHTS',))
        return body
    if confirmed:
        if not db.delete_basket(bskid):
            # TODO: The item was not deleted. DB problem?
            pass
    else:
        body = webbasket_templates.tmpl_confirm_delete(bskid,
                                                       db.count_subscribers(uid, bskid),
                                                       category,
                                                       selected_topic, selected_group_id,
                                                       ln)
    return body

def delete_record(uid, bskid, recid):
    """Delete a given record in a given basket.
    @param uid: user id (user has to have sufficient rights on basket
    @param bskid: basket id
    @param recid: record id
    """
    if __check_user_can_perform_action(uid,
                                       bskid,
                                       cfg['CFG_WEBBASKET_SHARE_LEVELS']['DELITM']):
        db.delete_item(bskid, recid)

def move_record(uid, bskid, recid, direction):
    """Move a record up or down in a basket (change score).
    @param uid: user id (user has to have manage rights over this basket)
    @param bskid: basket id
    @param recid: record we want to move
    @param direction: CFG_WEBBASKET_ACTIONS['UP'] or CFG_WEBBASKET_ACTIONS['DOWN']
    """
    if __check_user_can_perform_action(uid,
                                       bskid,
                                       cfg['CFG_WEBBASKET_SHARE_LEVELS']['MANAGE']):
        db.move_item(bskid, recid, direction)

def perform_request_edit(uid, bskid, topic="", new_name='',
                         new_topic = '', new_topic_name='',
                         groups=[], external='',
                         ln=CFG_SITE_LANG):
    """Interface for management of basket. If names, groups or external is
     provided, will save new rights into database, else will provide interface.
    @param uid: user id (user has to have sufficient rights on this basket
    @param bskid: basket id to change rights on
    @param topic: topic currently used (int)
    @param new_name: new name of basket
    @param new_topic: topic in which to move basket (int),
                      new_topic_name must be left blank
    @param new_topic_name: new topic in which to move basket
                           (will overwrite param new_topic)
    @param groups: list of strings formed in this way: group_id + '_' + rights
    @param external: rights for everybody (can be 'NO')
    @param ln: language
    """
    body = ''
    #warnings = []

    # TODO: external rights must be washed, it can only be one of the following:
    # NO, READITM, READCMT, ADDCMT
    _ = gettext_set_language(ln)

    rights = db.get_max_user_rights_on_basket(uid, bskid)
    if rights != cfg['CFG_WEBBASKET_SHARE_LEVELS']['MANAGE']:
        try:
            raise InvenioWebBasketWarning(_('Sorry, you do not have sufficient rights on this basket.'))
        except InvenioWebBasketWarning as exc:
            register_exception(stream='warning')
            #warnings.append(exc.message)
        #warnings.append(('WRN_WEBBASKET_NO_RIGHTS',))
        return body
    bsk_name = db.get_basket_name(bskid)
    if not(groups) and not(external) and not(new_name) and not(new_topic) and not(new_topic_name):
        # display interface
        topics = map(lambda x: x[0], db.get_personal_topics_infos(uid))
        groups_rights = db.get_groups_subscribing_to_basket(bskid)
        external_rights = ''
        if groups_rights and groups_rights[0][0] == 0:
            external_rights = groups_rights[0][2]
            groups_rights = groups_rights[1:]
        display_delete = db.check_user_owns_baskets(uid, bskid)
        display_general = display_delete
        if isGuestUser(uid):
            display_sharing = 0
        else:
            display_sharing = 1
        body = webbasket_templates.tmpl_edit(bskid=bskid, bsk_name=bsk_name,
                                             display_general=display_general,
                                             topics=topics, topic=topic,
                                             display_delete=display_delete,
                                             display_sharing=display_sharing,
                                             groups_rights=groups_rights,
                                             external_rights=external_rights,
                                             ln=ln)
    else:
        out_groups = {}
        if len(groups):
            for group in groups:
                (group_id, group_rights) = group.split('_')
                out_groups[group_id] = group_rights
        out_groups['0'] = external
        if not(isGuestUser(uid)):
            db.update_rights(bskid, out_groups)
        if new_name != bsk_name:
            db.rename_basket(bskid, new_name)
        if new_topic_name:
            db.move_baskets_to_topic(uid, bskid, new_topic_name)
        elif not (new_topic == "-1" or new_topic == topic):
            if db.check_user_owns_baskets(uid, bskid):
                topics = map(lambda x: x[0], db.get_personal_topics_infos(uid))
                if new_topic in topics:
                    new_topic_name = new_topic
                    db.move_baskets_to_topic(uid, bskid, new_topic_name)
                else:
                    # TODO: inform the admin
                    #errors.append(('ERR_WEBBASKET_DB_ERROR'))
                    pass
            else:
                topic = ""
            #warnings.append(('ERR_WEBBASKET_NOT_OWNER'))
    return body

def perform_request_edit_topic(uid, topic='', new_name='', ln=CFG_SITE_LANG):
    """Interface for editing of topic.
    @param uid: user id (user has to have sufficient rights on this basket
    @param topic: topic to be edited
    @param new_name: new name of topic
    @param ln: language
    """
    body = ''
    #warnings = []

    #rights = db.get_max_user_rights_on_basket(uid, bskid)
    #if rights != cfg['CFG_WEBBASKET_SHARE_LEVELS']['MANAGE']:
    #    errors.append(('ERR_WEBBASKET_NO_RIGHTS',))
    #    return (body, errors, warnings)
    if not(new_name):
        # display interface
        #display_delete = db.check_user_owns_baskets(uid, bskid)
        #display_general = display_delete
        #if isGuestUser(uid):
            #display_sharing = 0
        #else:
            #display_sharing = 1
        display_general = True
        display_delete = True
        body = webbasket_templates.tmpl_edit_topic(display_general=display_general, topic=topic,
                                                   display_delete=display_delete, ln=ln)
    else:
        if cgi.escape(new_name, True) != cgi.escape(topic, True):
            db.rename_topic(uid, topic, new_name)
    return body

def perform_request_add_group(uid, bskid, topic="", group_id=0, ln=CFG_SITE_LANG):
    """If group id is specified, share basket bskid to this group with
    READITM rights;
    else return a page for selection of a group.
    @param uid: user id (selection only of groups user is member of)
    @param bskid: basket id
    @param topic: topic currently displayed
    @param group_id: id of group to share basket to
    @param ln: language
    """
    if group_id:
        db.share_basket_with_group(bskid,
                                   group_id,
                                   cfg['CFG_WEBBASKET_SHARE_LEVELS']['READITM'])
    else:
        groups = db.get_groups_user_member_of(uid)
        body = webbasket_templates.tmpl_add_group(bskid, topic, groups, ln)
        return body

def perform_request_create_basket(req, uid,
                                  new_basket_name='',
                                  new_topic_name='', create_in_topic="-1",
                                  topic="-1",
                                  recids=[],
                                  colid=-1,
                                  es_title='',
                                  es_desc='',
                                  es_url='',
                                  copy = False,
                                  move_from_basket=0,
                                  referer = '',
                                  ln=CFG_SITE_LANG):
    """if new_basket_name and topic infos are given create a basket and return topic number,
    else return body with warnings of basket creation form.
    @param req: request object for obtaining URL of the referring page
    @param uid: user id (int)
    @param new_basket_name: name of the basket to create (str)
    @param new_topic_name: name of new topic to create new basket in (str)
    @param create_in_topic: identification number of topic to create new basket in (int)
    @param topic: topic to preselect on the creation form.
    @pram ln: language
    """
    warnings = []
    warnings_html = ""
    _ = gettext_set_language(ln)

    if new_basket_name and (new_topic_name or create_in_topic != "-1"):
        #topics_infos = map(lambda x: x[0], db.get_personal_topics_infos(uid))
        new_topic_name = new_topic_name.strip()
        if new_topic_name:
            topic = new_topic_name
        else:
            topic = create_in_topic
        bskid = db.create_basket(uid, new_basket_name, topic)
        #topics = map(lambda x: x[0], topics_infos)
        return (bskid, topic)
    else:
        local_referer = get_referer(req) # URL of the referring page
        url = CFG_SITE_URL + '/yourbaskets/create_basket'
        import string
        if string.find(local_referer, url) == 0:
            if not new_basket_name:
                try:
                    raise InvenioWebBasketWarning(_('Please provide a name for the new basket.'))
                except InvenioWebBasketWarning as exc:
                    register_exception(stream='warning', req=req)
                    warnings.append(exc.message)
            if (not new_topic_name and create_in_topic == "-1"):
                try:
                    raise InvenioWebBasketWarning(_('Please select an existing topic or create a new one.'))
                except InvenioWebBasketWarning as exc:
                    register_exception(stream='warning', req=req)
                    warnings.append(exc.message)

        topics = map(lambda x: x[0], db.get_personal_topics_infos(uid))
        if topic in topics:
            create_in_topic = topic
        body = webbasket_templates.tmpl_create_basket(new_basket_name,
                                                      new_topic_name,
                                                      create_in_topic,
                                                      topics,
                                                      recids,
                                                      colid,
                                                      es_title,
                                                      es_desc,
                                                      es_url,
                                                      copy,
                                                      move_from_basket,
                                                      referer,
                                                      ln)
        if warnings:
            warnings_html += webbasket_templates.tmpl_warnings(warnings, ln)
            body = warnings_html + body
        return body

def perform_request_subscribe(uid,
                              bskid,
                              ln=CFG_SITE_LANG):
    """Subscribes user to the given public basket.
    Returns warnings if there were any."""
    _ = gettext_set_language(ln)

    #warnings = []
    warnings_html = ""

    if db.is_basket_public(bskid):
        if not db.subscribe(uid, bskid):
            try:
                raise InvenioWebBasketWarning(_('You cannot subscribe to this basket, you are the either owner or you have already subscribed.'))
            except InvenioWebBasketWarning as exc:
                register_exception(stream='warning')
                #warnings.append(exc.message)
            #warnings.append('WRN_WEBBASKET_CAN_NOT_SUBSCRIBE')
            warnings_html += webbasket_templates.tmpl_warnings(exc.message, ln)
    else:
        try:
            raise InvenioWebBasketWarning(_('The selected public basket does not exist or you do not have access to it.'))
        except InvenioWebBasketWarning as exc:
            register_exception(stream='warning')
            #warnings.append(exc.message)
        #warnings.append('WRN_WEBBASKET_INVALID_OR_RESTRICTED_PUBLIC_BASKET')
        warnings_html += webbasket_templates.tmpl_warnings(exc.message, ln)

    return warnings_html

def perform_request_unsubscribe(uid,
                                bskid,
                                ln=CFG_SITE_LANG):
    """Unsubscribes user from the given public basket.
    Returns warnings if there were any."""
    _ = gettext_set_language(ln)

    #warnings = []
    warnings_html = ""

    if db.is_basket_public(bskid):
        if not db.unsubscribe(uid, bskid):
            try:
                raise InvenioWebBasketWarning(_('You cannot unsubscribe from this basket, you are the either owner or you have already unsubscribed.'))
            except InvenioWebBasketWarning as exc:
                register_exception(stream='warning')
                #warnings.append(exc.message)
            #warnings.append('WRN_WEBBASKET_CAN_NOT_UNSUBSCRIBE')
            warnings_html += webbasket_templates.tmpl_warnings(exc.message, ln)
    else:
        try:
            raise InvenioWebBasketWarning(_('The selected public basket does not exist or you do not have access to it.'))
        except InvenioWebBasketWarning as exc:
            register_exception(stream='warning')
            #warnings.append(exc.message)
        #warnings.append('WRN_WEBBASKET_INVALID_OR_RESTRICTED_PUBLIC_BASKET')
        warnings_html += webbasket_templates.tmpl_warnings(exc.message, ln)

    return warnings_html

def check_user_can_comment(uid, bskid):
    """ Private function. check if a user can comment """
    min_right = cfg['CFG_WEBBASKET_SHARE_LEVELS']['ADDCMT']
    rights = db.get_max_user_rights_on_basket(uid, bskid)
    if rights:
        if cfg['CFG_WEBBASKET_SHARE_LEVELS_ORDERED'].index(rights) >= cfg['CFG_WEBBASKET_SHARE_LEVELS_ORDERED'].index(min_right):
            return 1
    return 0

def __check_user_can_perform_action(uid, bskid, rights):
    """ Private function, check if a user has sufficient rights"""
    min_right = rights
    rights = db.get_max_user_rights_on_basket(uid, bskid)
    if rights:
        if cfg['CFG_WEBBASKET_SHARE_LEVELS_ORDERED'].index(rights) >= cfg['CFG_WEBBASKET_SHARE_LEVELS_ORDERED'].index(min_right):
            return 1
    return 0

def check_sufficient_rights(rights_user_has, rights_needed):
    """Private function, check if the rights are sufficient."""
    try:
        out = cfg['CFG_WEBBASKET_SHARE_LEVELS_ORDERED'].index(rights_user_has) >= \
              cfg['CFG_WEBBASKET_SHARE_LEVELS_ORDERED'].index(rights_needed)
    except ValueError:
        out = 0
    return out

def can_add_notes_to_public_basket_p(bskid):
    """ Private function. Checks if notes can be added to the given public basket."""

    min_right = cfg['CFG_WEBBASKET_SHARE_LEVELS']['ADDCMT']
    rights = db.get_rights_on_public_basket(bskid)
    if rights:
        if cfg['CFG_WEBBASKET_SHARE_LEVELS_ORDERED'].index(rights[0][0]) >= cfg['CFG_WEBBASKET_SHARE_LEVELS_ORDERED'].index(min_right):
            return True
    return False

def create_guest_warning_box(ln=CFG_SITE_LANG):
    """return a warning message about logging into system"""
    return webbasket_templates.tmpl_create_guest_warning_box(ln)

def create_personal_baskets_selection_box(uid,
                                          html_select_box_name='baskets',
                                          selected_bskid=None,
                                          ln=CFG_SITE_LANG):
    """Return HTML box for basket selection. Only for personal baskets.
    @param uid: user id
    @param html_select_box_name: name used in html form
    @param selected_bskid: basket currently selected
    @param ln: language
    """
    baskets = db.get_all_personal_baskets_names(uid)
    return webbasket_templates.tmpl_personal_baskets_selection_box(
                                        baskets,
                                        html_select_box_name,
                                        selected_bskid,
                                        ln)

def create_basket_navtrail(uid,
                           category=cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'],
                           topic="", group=0,
                           bskid=0, ln=CFG_SITE_LANG):
    """display navtrail for basket navigation.
    @param uid: user id (int)
    @param category: selected category (see cfg['CFG_WEBBASKET_CATEGORIES'])
    @param topic: selected topic if personal baskets
    @param group: selected group id for displaying (int)
    @param bskid: basket id (int)
    @param ln: language"""
    _ = gettext_set_language(ln)
    out = ''
    if category == cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE']:
        category_html = """ &gt; <a class="navtrail" href="%s/yourbaskets/display?%s">%s</a>""" % \
                        (CFG_SITE_URL,
                         'category=' + category + '&amp;ln=' + ln,
                         _("Personal baskets"))
        out += category_html

        topics = map(lambda x: x[0], db.get_personal_topics_infos(uid))
        if topic in topics:
            topic_html = """ &gt; <a class="navtrail" href="%s/yourbaskets/display?%s">%s</a>""" % \
                         (CFG_SITE_URL,
                          'category=' + category + '&amp;topic=' + \
                                    urllib.quote(topic) + '&amp;ln=' + ln,
                          cgi.escape(topic))
            out += topic_html

            if bskid:
                basket = db.get_public_basket_infos(bskid)
                if basket:
                    basket_html = """ &gt; <a class="navtrail" href="%s/yourbaskets/display?%s">%s</a>""" % \
                                  (CFG_SITE_URL,
                                   'category=' + category + '&amp;topic=' + \
                                             urllib.quote(topic) + '&amp;ln=' + ln + '#bsk' + str(bskid),
                                   cgi.escape(basket[1]))
                    out += basket_html

    elif category == cfg['CFG_WEBBASKET_CATEGORIES']['GROUP']:
        category_html = """ &gt; <a class="navtrail" href="%s/yourbaskets/display?%s">%s</a>""" % \
                        (CFG_SITE_URL,
                         'category=' + category + '&amp;ln=' + ln,
                         _("Group baskets"))
        out += category_html

        groups = db.get_group_infos(uid)
        if group:
            groups = filter(lambda x: x[0] == group, groups)
        if len(groups):
            group_html = """ &gt; <a class="navtrail" href="%s/yourbaskets/display?%s">%s</a>""" % \
                         (CFG_SITE_URL,
                          'category=' + category + '&amp;group=' + \
                                    str(group) + '&amp;ln=' + ln,
                          cgi.escape(groups[0][1]))
            out += group_html

            if bskid:
                basket = db.get_public_basket_infos(bskid)
                if basket:
                    basket_html = """ &gt; <a class="navtrail" href="%s/yourbaskets/display?%s">%s</a>""" % \
                                  (CFG_SITE_URL,
                                   'category=' + category + '&amp;group=' + \
                                             str(group) + '&amp;ln=' + ln + '#bsk' + str(bskid),
                                   cgi.escape(basket[1]))
                    out += basket_html

    elif category == cfg['CFG_WEBBASKET_CATEGORIES']['EXTERNAL']:
        category_html = """ &gt; <a class="navtrail" href="%s/yourbaskets/display?%s">%s</a>""" % \
                        (CFG_SITE_URL,
                         'category=' + category + '&amp;ln=' + ln,
                         _("Others' baskets"))
        out += category_html
        if bskid:
            basket = db.get_public_basket_infos(bskid)
            if basket:
                basket_html = """ &gt; <a class="navtrail" href="%s/yourbaskets/display?%s">""" % \
                              (CFG_SITE_URL,
                               'category=' + category + '&amp;ln=' + ln + \
                                         '#bsk' + str(bskid),
                               cgi.escape(basket[1]))
                out += basket_html

    return out

def create_webbasket_navtrail(uid,
                              category="",
                              topic="",
                              group=0,
                              bskid=0,
                              public_basket=False,
                              search_baskets=False,
                              add_to_basket=False,
                              ln=CFG_SITE_LANG):
    """Create the navtrail for navigation withing WebBasket.
    @param uid: user id (int)
    @param category: selected category (see cfg['CFG_WEBBASKET_CATEGORIES'])
    @param topic: selected topic (str)
    @param group: selected group (int)
    @param bskid: selected basket id (int)
    @param ln: language"""

    _ = gettext_set_language(ln)

    out = """<a class="navtrail" href="%s/youraccount/display?ln=%s">%s</a>""" % \
          (CFG_SITE_URL, ln, _("Your Account"))
    out += " &gt; "
    out += """<a class="navtrail" href="%s/yourbaskets/display?ln=%s">%s</a>""" % \
           (CFG_SITE_URL, ln, _("Your Baskets"))

    if public_basket:
        out += " &gt; "
        out += """<a class="navtrail" href="%s/yourbaskets/list_public_baskets?ln=%s">%s</a>""" % \
               (CFG_SITE_URL, ln, _("List of public baskets"))
        if bskid:
            basket = db.get_basket_name(bskid)
            if basket:
                out += " &gt; "
                out += """<a class="navtrail" href="%s/yourbaskets/display_public?bskid=%i&amp;ln=%s">%s</a>""" % \
                       (CFG_SITE_URL, bskid, ln, cgi.escape(basket, True))

    elif search_baskets:
        out += " &gt; "
        out += """<a class="navtrail" href="%s/yourbaskets/search?ln=%s">%s</a>""" % \
               (CFG_SITE_URL, ln, _("Search baskets"))

    elif add_to_basket:
        out += " &gt; "
        out += """<a class="navtrail" href="%s/yourbaskets/add?ln=%s">%s</a>""" % \
               (CFG_SITE_URL, ln, _("Add to basket"))

    else:
        if category == cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE']:
            out += " &gt; "
            out += """<a class="navtrail" href="%s/yourbaskets/display?category=%s&amp;ln=%s">%s</a>""" % \
                   (CFG_SITE_URL, cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'], ln, _("Personal baskets"))
            if topic:
                topic_names = map(lambda x: x[0], db.get_personal_topics_infos(uid))
                if topic in topic_names:
                    out += " &gt; "
                    out += """<a class="navtrail" href="%s/yourbaskets/display?category=%s&amp;topic=%s&amp;ln=%s">%s</a>""" % \
                           (CFG_SITE_URL, cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'], urllib.quote(topic), ln, cgi.escape(topic, True))
                    if bskid:
                        basket = db.get_basket_name(bskid)
                        if basket:
                            out += " &gt; "
                            out += """<a class="navtrail" href="%s/yourbaskets/display?category=%s&amp;topic=%s&amp;bskid=%i&amp;ln=%s">%s</a>""" % \
                                   (CFG_SITE_URL, cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'], urllib.quote(topic), bskid, ln, cgi.escape(basket, True))

        elif category == cfg['CFG_WEBBASKET_CATEGORIES']['GROUP']:
            out += " &gt; "
            out += """<a class="navtrail" href="%s/yourbaskets/display?category=%s&amp;ln=%s">%s</a>""" % \
                   (CFG_SITE_URL, cfg['CFG_WEBBASKET_CATEGORIES']['GROUP'], ln, _("Group baskets"))
            if group:
                group_names = map(lambda x: x[0] == group and x[1], db.get_group_infos(uid))
                if group_names and group_names[0]:
                    out += " &gt; "
                    out += """<a class="navtrail" href="%s/yourbaskets/display?category=%s&amp;group=%i&amp;ln=%s">%s</a>""" % \
                           (CFG_SITE_URL, cfg['CFG_WEBBASKET_CATEGORIES']['GROUP'], group, ln, cgi.escape(group_names[0], True))
                    if bskid:
                        basket = db.get_basket_name(bskid)
                        if basket:
                            out += " &gt; "
                            out += """<a class="navtrail" href="%s/yourbaskets/display?category=%s&amp;topic=%s&amp;bskid=%i&amp;ln=%s">%s</a>""" % \
                                   (CFG_SITE_URL, cfg['CFG_WEBBASKET_CATEGORIES']['GROUP'], group, bskid, ln, cgi.escape(basket, True))

        elif category == cfg['CFG_WEBBASKET_CATEGORIES']['EXTERNAL']:
            out += " &gt; "
            out += """<a class="navtrail" href="%s/yourbaskets/display?category=%s&amp;ln=%s">%s</a>""" % \
                   (CFG_SITE_URL, category, ln, _("Public baskets"))
            if bskid:
                basket = db.get_basket_name(bskid)
                if basket:
                    out += " &gt; "
                    out += """<a class="navtrail" href="%s/yourbaskets/display?category=%s&amp;topic=%s&amp;bskid=%i&amp;ln=%s">%s</a>""" % \
                           (CFG_SITE_URL, category, group, bskid, ln, cgi.escape(basket, True))

    return out

def account_list_baskets(uid, ln=CFG_SITE_LANG):
    """Display baskets informations on account page"""
    _ = gettext_set_language(ln)
    (personal, group, external) = db.count_baskets(uid)
    link = '<a href="%s">%s</a>'
    base_url = CFG_SITE_URL + '/yourbaskets/display?category=%s&amp;ln=' + ln
    personal_text = personal
    if personal:
        url = base_url % cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE']
        personal_text = link % (url, personal_text)
    group_text = group
    if group:
        url = base_url % cfg['CFG_WEBBASKET_CATEGORIES']['GROUP']
        group_text = link % (url, group_text)
    external_text = external
    if external:
        url = base_url % cfg['CFG_WEBBASKET_CATEGORIES']['EXTERNAL']
    else:
        url = CFG_SITE_URL + '/yourbaskets/list_public_baskets?ln=' + ln
    external_text = link % (url, external_text)
    out = _("You have %(x_nb_perso)s personal baskets and are subscribed to %(x_nb_group)s group baskets and %(x_nb_public)s other users public baskets.") %\
        {'x_nb_perso': personal_text,
         'x_nb_group': group_text,
         'x_nb_public': external_text}
    return out

def page_start(req, of='xm'):
    """Set the content type and send the headers for the page."""
    from invenio.legacy.search_engine import print_records_prologue

    if of.startswith('x'):
        req.content_type = "text/xml"
        if of == 'xr':
            req.content_type = "application/rss+xml"
        req.send_http_header()
        req.write("""<?xml version="1.0" encoding="UTF-8"?>\n""")
        print_records_prologue(req, of)
    else: # assuming HTML by default
        req.content_type = "text/html"
        req.send_http_header()

def page_end(req, of='xm'):
    """Print page footer"""
    from invenio.legacy.search_engine import print_records_epilogue
    if of.startswith('x'):
        print_records_epilogue(req, of)

def perform_request_export_xml(body):
    """Export an xml representation of the selected baskets/items."""
    return webbasket_templates.tmpl_export_xml(body)

################################
### External items functions ###
################################

def format_external_records(recids, of='hb'):
    """Given a list of external records' recids, this function returns a list of tuples
    with each recid and the actual formatted record using the selected output format.
    It also stores the formatted record in the database for future use."""

    # TODO: add a returnp variable to control whether we actually want anything
    # to be returned or not. For example when we just want to store the xml
    # formatted records for newly added items.
    # TODO: take care of external urls. Invent an xml format for them.

    # NOTE: this function is meant to format external records from other
    # libraries. It's not meant to handle custom external sources like urls
    # submitted manually by the user. These items are directly formatted and
    # stored by the add_to_basket database function.

    formatted_records = []

    if type(recids) is not list:
        recids = [recids]

    existing_xml_formatted_records = db.get_external_records(recids, "xm")
    for existing_xml_formatted_record in existing_xml_formatted_records:
        xml_record = decompress(existing_xml_formatted_record[2])
        xml_record_id = existing_xml_formatted_record[1]
        xml_record_colid = existing_xml_formatted_record[0]
        recids.remove(-xml_record_id)
        if of == "hb":
            if xml_record_colid > 0:
                htmlbrief_record = format_record(None, of, xml_record=xml_record)
            formatted_records.append((xml_record_id, htmlbrief_record))
        elif of != "hb":
            #formatted_records.append((xml_record_id, xml_record))
            formatted_records.append((xml_record_id, format_record([], of, xml_record=xml_record, on_the_fly=True)))
#            formatted_records.append((xml_record_id, repr(xml_record)))

    if formatted_records and of == "hb":
        db.store_external_records(formatted_records, of)

    records_grouped_by_collection = db.get_external_records_by_collection(recids)

    if records_grouped_by_collection:
        for records in records_grouped_by_collection:
            colid = records[2]
            if colid:
                external_records = fetch_and_store_external_records(records, of)
                formatted_records.extend(external_records)

    return formatted_records

def fetch_and_store_external_records(records, of="hb"):
    """Function that fetches the formatted records for one collection and stores them
    into the database. It also calculates and stores the original external url for each
    record."""

    results = []
    formatted_records = []

    if of == 'xm':
        re_controlfield = re.compile(r'<controlfield\b[^>]*>.*?</controlfield>', re.DOTALL + re.MULTILINE + re.IGNORECASE)
        re_blankline = re.compile(r'\s*\n', re.DOTALL + re.MULTILINE + re.IGNORECASE)

    # the locally saved external ids
    local_ext_ids = records[0].split(",")
    # the locally saved original external ids
    external_ids = records[1].split(",")
    collection_name = get_collection_name_by_id(records[2])
    collection_engine_set = select_hosted_search_engines(collection_name)
    collection_engine = collection_engine_set.pop()

    external_ids_urls = collection_engine.build_record_urls(external_ids)
    external_urls = [external_id_url[1] for external_id_url in external_ids_urls]
    #external_urls_dict = {}
    #for (local_id, url) in zip(local_ext_ids, external_urls):
        #external_urls_dict[local_id] = url
    #db.store_external_urls(external_urls_dict)
    db.store_external_urls(zip(local_ext_ids, external_urls))

    url = collection_engine.build_search_url(None, req_args=external_ids)
    pagegetters = [HTTPAsyncPageGetter(url)]

    def finished(pagegetter, dummy_data, dummy_time):
        """Function to be called when a page has been downloaded."""
        results.append(pagegetter)

    finished_list = async_download(pagegetters, finish_function=finished, timeout=CFG_EXTERNAL_COLLECTION_TIMEOUT)

    if finished_list[0]:
        collection_engine.parser.parse_and_get_results(results[0].data, feedonly=True)
        (dummy, parsed_results_dict) = collection_engine.parser.parse_and_extract_records(of=of)
        for (local_ext_id, external_id) in zip(local_ext_ids, external_ids):
            formatted_record = parsed_results_dict[external_id]
            if of == 'xm':
                formatted_record = re_controlfield.sub('', formatted_record)
                formatted_record = re_blankline.sub('\n', formatted_record)
            formatted_records.append((int(local_ext_id), formatted_record))
        db.store_external_records(formatted_records, of)
    else:
        for (local_ext_id, external_id) in zip(local_ext_ids, external_ids):
            formatted_records.append((int(local_ext_id), "There was a timeout when fetching the record."))

    return formatted_records

###############################
### Miscellaneous functions ###
###############################

def url_is_valid(url):
    """Returns (True, status, reason) if the url is valid or (False, status, reason) if different."""

    common_errors_list = [400, 404, 500]
    url_tuple = urlsplit(url)
    if not url_tuple[0]:
        url = "http://" + url
        url_tuple =  urlsplit(url)
    if not url_tuple[0] and not url_tuple[1]:
        return (False, 000, "Not Valid")
    # HTTPConnection had the timeout parameter introduced in python 2.6
    # for the older versions we have to get and set the default timeout
    # In order to use a custom timeout pass it as an extra argument to this function
    #old_timeout = getdefaulttimeout()
    #setdefaulttimeout(timeout)
    conn = HTTPConnection(url_tuple[1])
    #setdefaulttimeout(old_timeout)
    try:
        conn.request("GET", url_tuple[2])
    except:
        return (False, 000, "Not Valid")
    response = conn.getresponse()
    status = response.status
    reason = response.reason
    if str(status).startswith('1') or str(status).startswith('2') or str(status).startswith('3'):
        return (True, status, reason)
    elif str(status).startswith('4') or str(status).startswith('5'):
        if status in common_errors_list:
            return (False, status, reason)
        else:
            return (True, status, reason)

def nl2br(text):
    """Replace newlines (\n) found in text with line breaks (<br />)."""

    return '<br />'.join(text.split('\n'))

def wash_b_search(b):
    """Wash the b GET variable for the search interface."""
    _ = gettext_set_language(CFG_SITE_LANG)

    b = b.split('_', 1)
    b_category = b[0].upper()
    valid_categories = cfg['CFG_WEBBASKET_CATEGORIES'].values()
    valid_categories.append('')
    if b_category not in valid_categories:
        try:
            raise InvenioWebBasketWarning(_('The category you have selected does not exist. Please select a valid category.'))
        except InvenioWebBasketWarning as exc:
            register_exception(stream='warning')
            return ("", "", exc.message)
        #return ("", "", ['WRN_WEBBASKET_INVALID_CATEGORY'])
    if len(b) == 2:
        if b_category == cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'] or b_category == cfg['CFG_WEBBASKET_CATEGORIES']['GROUP']:
            return (b_category, b[1], None)
        # TODO: send a warning when the user has sent a second argument
        # specifying a category other than PRIVATE or GROUP
        #else:
            #return (b_category, "", ['WRN_WEBBASKET_'])
    return (b_category, "", None)

def wash_b_add(b):
    """Wash the b POST variable for the add interface."""
    _ = gettext_set_language(CFG_SITE_LANG)

    b = b.split('_', 1)
    b_category = b[0].upper()
    valid_categories = (cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'], cfg['CFG_WEBBASKET_CATEGORIES']['GROUP'])
    if b_category not in valid_categories or len(b) != 2 or not b[1]:
        try:
            raise InvenioWebBasketWarning(_('Cannot add items to the selected basket. Invalid parameters.'))
        except InvenioWebBasketWarning as exc:
            register_exception(stream='warning')
            return ("", "", exc.message)
    return (b_category, b[1], None)

def wash_category(category):
    """Wash the category."""
    _ = gettext_set_language(CFG_SITE_LANG)

    category = category.upper()
    valid_categories = cfg['CFG_WEBBASKET_CATEGORIES'].values()
    valid_categories.append('')
    if category not in valid_categories:
        try:
            raise InvenioWebBasketWarning(_('The category you have selected does not exist. Please select a valid category.'))
        except InvenioWebBasketWarning as exc:
            register_exception(stream='warning')
            return ("", "", exc.message)
        #return ("", ['WRN_WEBBASKET_INVALID_CATEGORY'])
    return (category, None)

def wash_topic(uid, topic):
    """Wash the topic."""
    _ = gettext_set_language(CFG_SITE_LANG)

    if not db.is_topic_valid(uid, topic):
        try:
            raise InvenioWebBasketWarning(_('The selected topic does not exist or you do not have access to it.'))
        except InvenioWebBasketWarning as exc:
            register_exception(stream='warning')
            return ("", "", exc.message)
        #return ("", ['WRN_WEBBASKET_INVALID_OR_RESTRICTED_TOPIC'])
    return (topic, None)

def wash_group(uid, group):
    """Wash the topic."""
    _ = gettext_set_language(ln=CFG_SITE_LANG)

    if not group.isdigit() or not db.is_group_valid(uid, group):
        try:
            raise InvenioWebBasketWarning(_('The selected group does not exist or you do not have access to it.'))
        except InvenioWebBasketWarning as exc:
            register_exception(stream='warning')
            return (0, exc.message)
        #return (0, ['WRN_WEBBASKET_INVALID_OR_RESTRICTED_GROUP'])
    return (int(group), None)

def wash_bskid(uid, category, bskid):
    """Wash the bskid based on its category. This function expectes a washed
    category, either for personal or for group baskets."""
    _ = gettext_set_language(CFG_SITE_LANG)

    if not bskid.isdigit():
        try:
            raise InvenioWebBasketWarning(_('The selected basket does not exist or you do not have access to it.'))
        except InvenioWebBasketWarning as exc:
            register_exception(stream='warning')
            return (0, exc.message)
        #return (0, ['WRN_WEBBASKET_INVALID_OR_RESTRICTED_BASKET'])
    bskid = int(bskid)
    if category == cfg['CFG_WEBBASKET_CATEGORIES']['PRIVATE'] and not db.is_personal_basket_valid(uid, bskid):
        try:
            raise InvenioWebBasketWarning(_('The selected basket does not exist or you do not have access to it.'))
        except InvenioWebBasketWarning as exc:
            register_exception(stream='warning')
            return (0, exc.message)
        #return (0, ['WRN_WEBBASKET_INVALID_OR_RESTRICTED_BASKET'])
    if category == cfg['CFG_WEBBASKET_CATEGORIES']['GROUP'] and not db.is_group_basket_valid(uid, bskid):
        try:
            raise InvenioWebBasketWarning(_('The selected basket does not exist or you do not have access to it.'))
        except InvenioWebBasketWarning as exc:
            register_exception(stream='warning')
            return (0, exc.message)
        #return (0, ['WRN_WEBBASKET_INVALID_OR_RESTRICTED_BASKET'])
    return (bskid, None)

def wash_of(of):
    """Wash the output format"""
    _ = gettext_set_language(CFG_SITE_LANG)

    list_of_accepted_formats = ['hb',
                                'xm',
                                'hx',
                                'xd',
                                'xe',
                                'xn',
                                'xw',
                                'xr',
                                'xp']

    if of in list_of_accepted_formats:
        return (of, None)
    try:
        raise InvenioWebBasketWarning(_('The selected output format is not available or is invalid.'))
    except InvenioWebBasketWarning as exc:
        register_exception(stream='warning')
    return ('hb', exc.message)

def __create_search_box(uid,
                        category="",
                        topic="",
                        grpid=0,
                        p="",
                        n=0,
                        ln=CFG_SITE_LANG):
    """Private function.
    Creates the search box and returns html code."""

    topic_list = db.get_all_user_topics(uid)
    group_list = db.get_all_user_groups(uid)
    number_of_public_baskets = db.count_external_baskets(uid)

    search_box = webbasket_templates.tmpl_create_search_box(category,
                                                            topic,
                                                            grpid,
                                                            topic_list,
                                                            group_list,
                                                            number_of_public_baskets,
                                                            p,
                                                            n,
                                                            ln=ln)

    return search_box
