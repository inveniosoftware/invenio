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

"""Web Baskets features."""

__revision__ = "$Id$"

import cgi
from zlib import decompress

from invenio.config import CFG_SITE_LANG, CFG_SITE_URL, \
     CFG_WEBBASKET_MAX_NUMBER_OF_DISPLAYED_BASKETS
from invenio.messages import gettext_set_language
from invenio.dateutils import convert_datetext_to_dategui, \
                              convert_datetext_to_datestruct,\
                              convert_datestruct_to_dategui
from invenio.bibformat import format_record
from invenio.webbasket_config import CFG_WEBBASKET_SHARE_LEVELS, \
                                     CFG_WEBBASKET_SHARE_LEVELS_ORDERED, \
                                     CFG_WEBBASKET_CATEGORIES, \
                                     CFG_WEBBASKET_WARNING_MESSAGES
from invenio.webuser import isGuestUser, collect_user_info
from invenio.search_engine import \
     record_exists, \
     check_user_can_view_record
from invenio.webcomment import check_user_can_attach_file_to_comments
import invenio.webbasket_dblayer as db
try:
    import invenio.template
    webbasket_templates = invenio.template.load('webbasket')
except ImportError:
    pass

def perform_request_display(uid,
                            category=CFG_WEBBASKET_CATEGORIES['PRIVATE'],
                            selected_topic=0,
                            selected_group_id=0,
                            ln=CFG_SITE_LANG):
    """Display all the baskets of given category, topic or group.
    @param uid: user id
    @param category: selected category (see webbasket_config.py)
    @param selected_topic: # of selected topic to display baskets
    @param selected_group_id: id of group to display baskets
    @param ln: language"""
    warnings = []
    errors = []
    baskets_html = []
    baskets = []

    _ = gettext_set_language(ln)
    nb_groups = db.count_groups_user_member_of(uid)
    nb_external_baskets = db.count_external_baskets(uid)
    selectionbox = ''
    infobox = ''
    if category == CFG_WEBBASKET_CATEGORIES['EXTERNAL']:
        baskets = db.get_external_baskets_infos(uid)
        if len(baskets):
            map(list, baskets)
        else:
            category = CFG_WEBBASKET_CATEGORIES['PRIVATE']
    if category == CFG_WEBBASKET_CATEGORIES['GROUP']:
        groups = db.get_group_infos(uid)
        if len(groups):
            if selected_group_id == 0 and len(groups):
                selected_group_id = groups[0][0]
            selectionbox = webbasket_templates.tmpl_group_selection(groups,
                                                                    selected_group_id,
                                                                    ln)
            baskets = db.get_group_baskets_infos(selected_group_id)
            def adapt_group_rights(item):
                """Suppress unused element in tuple."""
                out = list(item)
                if out[-1] == uid:
                    out[-2] = CFG_WEBBASKET_SHARE_LEVELS['MANAGE']
                return out[:-1]
            baskets = map(adapt_group_rights, baskets)
        else:
            category = CFG_WEBBASKET_CATEGORIES['PRIVATE']
    if category == CFG_WEBBASKET_CATEGORIES['PRIVATE']:
        topics_list = db.get_personal_topics_infos(uid)
        if not selected_topic and len(topics_list):
            selected_topic = 0
        selectionbox = webbasket_templates.tmpl_topic_selection(topics_list,
                                                                selected_topic,
                                                                ln)
        if selected_topic >= len(topics_list):
            selected_topic = len(topics_list) - 1
        if len(topics_list) > 0:
            baskets = db.get_personal_baskets_infos(uid, topics_list[selected_topic][0])
        else:
            baskets = []
        def add_manage_rights(item):
            """ Convert a tuple to a list and add rights"""
            out = list(item)
            out.append(CFG_WEBBASKET_SHARE_LEVELS['MANAGE'])
            return out
        baskets = map(add_manage_rights, baskets)

    bskids = []
    for basket in baskets:
        bskids.append(basket[0])
    levels = dict(db.is_shared_to(bskids))
    create_link = ''
    if category == CFG_WEBBASKET_CATEGORIES['PRIVATE']:
        create_link = webbasket_templates.tmpl_create_basket_link(selected_topic, ln)
    infobox = webbasket_templates.tmpl_baskets_infobox(map(lambda x: (x[0], x[1], x[2]),
                                                           baskets),
                                                       create_link,
                                                       ln)
    for (bskid, name, date_modification,
         nb_views, nb_items, last_added, share_level) in baskets:
        (bsk_html, bsk_e, bsk_w) = __display_basket(bskid,
                                                    name,
                                                    date_modification,
                                                    nb_views,
                                                    nb_items,
                                                    last_added,
                                                    share_level,
                                                    levels[bskid],
                                                    category,
                                                    selected_topic,
                                                    selected_group_id,
                                                    ln)
        baskets_html.append(bsk_html)
        errors.extend(bsk_e)
        warnings.extend(bsk_w)

    body = webbasket_templates.tmpl_display(selectionbox,
                                            infobox,
                                            baskets_html,
                                            category,
                                            nb_groups,
                                            nb_external_baskets,
                                            ln)
    return (body, errors, warnings)


def __display_basket(bskid, name, date_modification, nb_views,
                     nb_items, last_added,
                     share_level, group_sharing_level,
                     category=CFG_WEBBASKET_CATEGORIES['PRIVATE'],
                     selected_topic=0, selected_group_id=0,
                     ln=CFG_SITE_LANG):
    """Private function. Display a basket giving its category and topic or group.
    @param share_level: rights user has on basket
    @param group_sharing_level: None if basket is not shared,
                                0 if public basket,
                                > 0 if shared to usergroups but not public.
    @param category: selected category (see webbasket_config.py)
    @param selected_topic: # of selected topic to display baskets
    @param selected_group_id: id of group to display baskets
    @param ln: language"""

    _ = gettext_set_language(ln)
    errors = []
    warnings = []

    nb_bsk_cmts = 0
    last_cmt = _("N/A")
    records = []
    cmt_dates = []
    date_modification = convert_datetext_to_dategui(date_modification, ln)

    items = db.get_basket_content(bskid, 'hb')

    for (recid, nb_cmt, last_cmt, ext_val, int_val, score) in items:
        cmt_dates.append(convert_datetext_to_datestruct(last_cmt))
        last_cmt = convert_datetext_to_dategui(last_cmt, ln)
        val = ''
        nb_bsk_cmts += nb_cmt
        if recid < 0:
            if ext_val:
                val = decompress(ext_val)
        else:
            if int_val:
                val = decompress(int_val)
            else:
                val = format_record(recid, 'hb', on_the_fly=True)
        records.append((recid, nb_cmt, last_cmt, val, score))

    if len(cmt_dates) > 0:
        last_cmt = convert_datestruct_to_dategui(max(cmt_dates), ln)

    body = webbasket_templates.tmpl_basket(bskid,
                                           name,
                                           date_modification,
                                           nb_views,
                                           nb_items, last_added,
                                           (check_sufficient_rights(share_level, CFG_WEBBASKET_SHARE_LEVELS['READITM']),
                                            check_sufficient_rights(share_level, CFG_WEBBASKET_SHARE_LEVELS['MANAGE']),
                                            check_sufficient_rights(share_level, CFG_WEBBASKET_SHARE_LEVELS['READCMT']),
                                            check_sufficient_rights(share_level, CFG_WEBBASKET_SHARE_LEVELS['ADDITM']),
                                            check_sufficient_rights(share_level, CFG_WEBBASKET_SHARE_LEVELS['DELITM'])),
                                           nb_bsk_cmts, last_cmt,
                                           group_sharing_level,
                                           category, selected_topic, selected_group_id,
                                           records,
                                           ln)
    return (body, errors, warnings)

def perform_request_display_item(uid, bskid, recid, format='hb',
                                 category=CFG_WEBBASKET_CATEGORIES['PRIVATE'],
                                 topic=0, group_id=0, ln=CFG_SITE_LANG):
    """Display an item of a basket of given category, topic or group.
    @param uid: user id
    @param bskid: basket_id
    @param recid: record id
    @param format: format of the record (hb, hd, etc.)
    @param category: selected category (see webbasket_config.py)
    @param topic: # of selected topic to display baskets
    @param group_id: id of group to display baskets
    @param ln: language"""
    body = ''
    errors = []
    warnings = []

    rights = db.get_max_user_rights_on_basket(uid, bskid)
    if not(check_sufficient_rights(rights, CFG_WEBBASKET_SHARE_LEVELS['READITM'])):
        errors.append('ERR_WEBBASKET_NO_RIGHTS')
        return (body, errors, warnings)
    if category == CFG_WEBBASKET_CATEGORIES['PRIVATE']:
        topics_list = db.get_personal_topics_infos(uid)
        if not topic and len(topics_list):
            topic = 0
        topicsbox = webbasket_templates.tmpl_topic_selection(topics_list, topic, ln)
    elif category == CFG_WEBBASKET_CATEGORIES['GROUP']:
        groups = db.get_group_infos(uid)
        if group_id == 0 and len(groups):
            group_id = groups[0][0]
        topicsbox = webbasket_templates.tmpl_group_selection(groups, group_id, ln)
    else:
        topicsbox = ''
    record = db.get_basket_record(bskid, recid, format)
    comments = db.get_comments(bskid, recid)
    group_sharing_level = None
    levels = db.is_shared_to(bskid)
    if len(levels):
        group_sharing_level = levels[0][1]
    basket = db.get_basket_general_infos(bskid)
    if not(len(basket)):
        errors.append('ERR_WEBBASKET_DB_ERROR')
        return (body, errors, warnings)
    item_html = webbasket_templates.tmpl_item(basket,
                                              recid, record, comments,
                                              group_sharing_level,
                                              (check_sufficient_rights(rights, CFG_WEBBASKET_SHARE_LEVELS['READCMT']),
                                               check_sufficient_rights(rights, CFG_WEBBASKET_SHARE_LEVELS['ADDCMT']),
                                               check_sufficient_rights(rights, CFG_WEBBASKET_SHARE_LEVELS['DELCMT'])),
                                              selected_category=category, selected_topic=topic, selected_group_id=group_id,
                                              ln=ln)
    body = webbasket_templates.tmpl_display(topicsbox=topicsbox, baskets=[item_html],
                                            selected_category=category,
                                            nb_groups=db.count_groups_user_member_of(uid),
                                            nb_external_baskets=db.count_external_baskets(uid),
                                            ln=ln)
    return (body, errors, warnings)

def perform_request_write_comment(uid, bskid, recid, cmtid=0,
                                  category=CFG_WEBBASKET_CATEGORIES['PRIVATE'],
                                  topic=0, group_id=0,
                                  ln=CFG_SITE_LANG):
    """Display a comment writing form
    @param uid: user id
    @param bskid: basket id
    @param recid: record id (comments are on a specific record in a specific basket)
    @param cmtid: if provided this comment is a reply to comment cmtid.
    @param category: selected category
    @param topic: selected topic
    @param group_id: selected group id
    @param ln: language
    """
    body = ''
    warnings = []
    errors = []
    textual_msg = '' # initial value in replies
    html_msg = '' # initial value  in replies (if FCKeditor)
    title = '' # initial title in replies
    if not check_user_can_comment(uid, bskid):
        errors.append(('ERR_WEBBASKET_CANNOT_COMMENT'))
        return (body, errors, warnings)
    if cmtid:
        # this is a reply to another comment
        comment = db.get_comment(cmtid)
        if comment:
            # Title
            if comment[2]:
                title = 'Re: ' + comment[2]

            # Build two msg: one mostly textual, the other one with HTML markup, for the FCKeditor.
            textual_msg = webbasket_templates.tmpl_quote_comment_textual(comment[2], # title
                                                                         uid,
                                                                         comment[0], # nickname
                                                                         comment[4], # date
                                                                         comment[3],
                                                                         ln)
            html_msg = webbasket_templates.tmpl_quote_comment_html(comment[2], # title
                                                                   uid,
                                                                   comment[0], # nickname
                                                                   comment[4], # date
                                                                   comment[3],
                                                                   ln)
        else:
            warning = (CFG_WEBBASKET_WARNING_MESSAGES['ERR_WEBBASKET_cmtid_INVALID'], cmtid)
            warnings.append(warning)
    record = db.get_basket_record(bskid, recid, 'hb')
    # Check that user can attach file. To simplify we use the same
    # checking as in WebComment, though it is not completely adequate.
    user_info = collect_user_info(uid)
    can_attach_files = check_user_can_attach_file_to_comments(user_info, recid)
    body = webbasket_templates.tmpl_write_comment(bskid=bskid,
                                                  recid=recid,
                                                  cmt_title=title,
                                                  cmt_body_textual=textual_msg,
                                                  cmt_body_html=html_msg,
                                                  record = record,
                                                  selected_category=category,
                                                  selected_topic=topic,
                                                  selected_group_id=group_id,
                                                  warnings=warnings,
                                                  can_attach_files=can_attach_files)
    if category == CFG_WEBBASKET_CATEGORIES['PRIVATE']:
        topics_list = db.get_personal_topics_infos(uid)
        if not topic and len(topics_list):
            topic = 0
        topicsbox = webbasket_templates.tmpl_topic_selection(topics_list, topic, ln)
    elif category == CFG_WEBBASKET_CATEGORIES['GROUP']:
        groups = db.get_group_infos(uid)
        if group_id == 0 and len(groups):
            group_id = groups[0][0]
        topicsbox = webbasket_templates.tmpl_group_selection(groups, group_id, ln)
    else:
        topicsbox = ''
    body = webbasket_templates.tmpl_display(topicsbox, '', [ body ], category, ln)
    return (body, errors, warnings)

def perform_request_save_comment(uid, bskid, recid, title='', text='',
                                 ln=CFG_SITE_LANG,
                                 editor_type='textarea'):
    """ Save a given comment if able to.
    @param uid: user id (int)
    @param bskid: basket id (int)
    @param recid: record id (int)
    @param title: title of comment (string)
    @param text: comment's body (string)
    @param ln: language (string)
    @param editor_type: the kind of editor/input used for the comment: 'textarea', 'fckeditor'
    @return: (errors, infos) where errors: list of errors while saving
                                  infos: list of informations to display"""
    _ = gettext_set_language(ln)
    errors = []
    infos = []
    if not check_user_can_comment(uid, bskid):
        errors.append(('ERR_WEBBASKET_CANNOT_COMMENT'))
        return (errors, infos)

    if editor_type == 'fckeditor':
        # Here we remove the line feeds introduced by FCKeditor (they
        # have no meaning for the user) and replace the HTML line
        # breaks by linefeeds, so that we are close to an input that
        # would be done without the FCKeditor. That's much better if a
        # reply to a comment is made with a browser that does not
        # support FCKeditor.
        text = text.replace('\n', '').replace('\r', '').replace('<br />', '\n')

    if not(db.save_comment(uid, bskid, recid, title, text)):
        errors.append(('ERR_WEBBASKET_DB_ERROR'))
    else:
        infos.append(_('Your comment has been successfully posted'))
    return (errors, infos)

def perform_request_delete_comment(uid, bskid, recid, cmtid):
    """Delete comment cmtid on record recid for basket bskid."""
    errors = []
    if __check_user_can_perform_action(uid, bskid, CFG_WEBBASKET_SHARE_LEVELS['DELCMT']):
        db.delete_comment(bskid, recid, cmtid)
    else:
        errors.append('ERR_WEBBASKET_NO_RIGHTS')
    return errors

def perform_request_add(uid, recids=[], bskids=[], referer='',
                        new_basket_name='', new_topic_name='', create_in_topic='',
                        ln=CFG_SITE_LANG):
    """Add records to baskets
    @param uid: user id
    @param recids: list of records to add
    @param bskids: list of baskets to add records to. if not provided, will return a
                   page where user can select baskets
    @param referer: URL of the referring page
    @param new_basket_name: add record to new basket
    @param new_topic_name: new basket goes into new topic
    @param create_in_topic: # of topic to put basket into
    @param ln: language
    @return: (body, errors, warnings) tuple
    """
    body = ''
    errors = []
    warnings = []
    if not(type(recids) == list):
        recids = [recids]

    validated_recids = []
    for recid in recids:
        recid = int(recid)
        if record_exists(recid) == 1:
            validated_recids.append(recid)

    user_info = collect_user_info(uid)
    for recid in validated_recids:
        (auth_code, auth_msg) = check_user_can_view_record(user_info, recid)
        if auth_code:
            # User not authorized to view record
            validated_recids.remove(recid)
            warnings.append(('WRN_WEBBASKET_NO_RIGHTS_TO_ADD_THIS_RECORD', recid))

    if not(len(validated_recids)):
        warnings.append('WRN_WEBBASKET_NO_RECORD')
        body += webbasket_templates.tmpl_warnings(warnings, ln)
        if referer and not(referer.find(CFG_SITE_URL) == -1):
            body += webbasket_templates.tmpl_back_link(referer, ln)
        return (body, errors, warnings)

    if new_basket_name != '':
        new_topic_name = new_topic_name.strip()
        if new_topic_name:
            topic = new_topic_name
        elif create_in_topic != -1:
            topics = map(lambda x: x[0], db.get_personal_topics_infos(uid))
            try:
                topic = topics[create_in_topic]
            except IndexError:
                topic = ''
        else:
            topic = ''
            warnings.append('WRN_WEBBASKET_NO_GIVEN_TOPIC')
            body += webbasket_templates.tmpl_warnings(warnings, ln)
            bskids = []
        if topic:
            id_bsk = db.create_basket(uid, new_basket_name, topic)
            bskids.append(id_bsk)

    if bskids:
        bskids = [int(bskid) for bskid in bskids if int(bskid) > 0]
        if bskids:
            for bskid in bskids:
                if not(__check_user_can_perform_action(uid,
                                        bskid,
                                        CFG_WEBBASKET_SHARE_LEVELS['ADDITM'])):
                    errors.append('ERR_WEBBASKET_NO_RIGHTS')
                    return (body, errors, warnings)
            nb_modified_baskets = db.add_to_basket(uid, validated_recids, bskids)
            body = webbasket_templates.tmpl_added_to_basket(nb_modified_baskets, ln)
            body_tmp, warnings_temp, errors_tmp = perform_request_display(uid,
                            category=CFG_WEBBASKET_CATEGORIES['PRIVATE'],
                            selected_topic=create_in_topic != -1 and create_in_topic or 0,
                            selected_group_id=0,
                            ln=CFG_SITE_LANG)
            body += body_tmp
            warnings += warnings_temp
            errors += errors_tmp
            body += webbasket_templates.tmpl_back_link(referer, ln)
            return (body, warnings, errors)
        else:
            warnings.append('WRN_WEBBASKET_NO_BASKET_SELECTED')
            body += webbasket_templates.tmpl_warnings(warnings, ln)

    # Display basket_selection
    personal_baskets = db.get_all_personal_baskets_names(uid)
    group_baskets = db.get_all_group_baskets_names(uid)
    external_baskets = db.get_all_external_baskets_names(uid)
    topics = map(lambda x: x[0], db.get_personal_topics_infos(uid))
    body += webbasket_templates.tmpl_add(recids=validated_recids,
                                        personal_baskets=personal_baskets,
                                        group_baskets=group_baskets,
                                        external_baskets=external_baskets,
                                        topics=topics,
                                        referer=referer,
                                        ln=ln)
    body += webbasket_templates.tmpl_back_link(referer, ln)
    return (body, errors, warnings)

def perform_request_delete(uid, bskid, confirmed=0,
                           category=CFG_WEBBASKET_CATEGORIES['PRIVATE'],
                           selected_topic=0, selected_group_id=0,
                           ln=CFG_SITE_LANG):
    """Delete a given basket.
    @param uid: user id (user has to be owner of this basket)
    @param bskid: basket id
    @param confirmed: if 0 will return a confirmation page; if 1 will delete basket.
    @param category: category currently displayed
    @param selected_topic: topic currently displayed
    @param selected_group_id: if category is group, id of the group currently displayed
    @param ln: language"""
    body = ''
    errors = []
    warnings = []
    if not(db.check_user_owns_baskets(uid, [bskid])):
        errors.append(('ERR_WEBBASKET_NO_RIGHTS',))
        return (body, errors, warnings)
    if confirmed:
        success = db.delete_basket(bskid)
        if not success:
            errors.append(('ERR_WEBBASKET_DB_ERROR',))
    else:
        body = webbasket_templates.tmpl_confirm_delete(bskid,
                                                       db.count_subscribers(uid, bskid),
                                                       category,
                                                       selected_topic, selected_group_id,
                                                       ln)
    return (body, errors, warnings)

def delete_record(uid, bskid, recid):
    """Delete a given record in a given basket.
    @param uid: user id (user has to have sufficient rights on basket
    @param bskid: basket id
    @param recid: record id
    """
    if __check_user_can_perform_action(uid,
                                       bskid,
                                       CFG_WEBBASKET_SHARE_LEVELS['DELITM']):
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
                                       CFG_WEBBASKET_SHARE_LEVELS['MANAGE']):
        db.move_item(bskid, recid, direction)

def perform_request_edit(uid, bskid, topic=0, new_name='',
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
    errors = []
    warnings = []

    rights = db.get_max_user_rights_on_basket(uid, bskid)
    if rights != CFG_WEBBASKET_SHARE_LEVELS['MANAGE']:
        errors.append(('ERR_WEBBASKET_NO_RIGHTS',))
        return (body, errors, warnings)
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
        elif new_topic != -1:
            if db.check_user_owns_baskets(uid, bskid):
                topics = map(lambda x: x[0], db.get_personal_topics_infos(uid))
                try:
                    new_topic_name = topics[new_topic]
                    db.move_baskets_to_topic(uid, bskid, new_topic_name)
                except:
                    errors.append(('ERR_WEBBASKET_DB_ERROR'))
            else:
                topic = 0
            errors.append(('ERR_WEBBASKET_NOT_OWNER'))
    return (body, errors, warnings)

def perform_request_add_group(uid, bskid, topic=0, group_id=0, ln=CFG_SITE_LANG):
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
                                   CFG_WEBBASKET_SHARE_LEVELS['READITM'])
    else:
        groups = db.get_groups_user_member_of(uid)
        body = webbasket_templates.tmpl_add_group(bskid, topic, groups, ln)
        return body

def perform_request_create_basket(uid,
                                  new_basket_name='',
                                  new_topic_name='', create_in_topic=-1,
                                  topic_number=-1,
                                  ln=CFG_SITE_LANG):
    """if new_basket_name and topic infos are given create a basket and return topic number,
    else return (body, errors, warnings) tuple of basket creation form.
    @param uid: user id (int)
    @param new_basket_name: name of the basket to create (str)
    @param new_topic_name: name of new topic to create new basket in (str)
    @param create_in_topic: identification number of topic to create new basket in (int)
    @param topic_number: number of topic to preselect on the creation form.
    @pram ln: language
    """
    if new_basket_name and (new_topic_name or create_in_topic != -1):
        topics_infos = map(lambda x: x[0], db.get_personal_topics_infos(uid))
        new_topic_name = new_topic_name.strip()
        if new_topic_name:
            topic = new_topic_name
        else:
            try:
                topic = topics_infos[create_in_topic]
            except IndexError:
                return 0
        db.create_basket(uid, new_basket_name, topic)
        topics = map(lambda x: x[0], topics_infos)
        try:
            return topics.index(topic)
        except ValueError:
            return 0
    else:
        topics = map(lambda x: x[0], db.get_personal_topics_infos(uid))
        if topic_number in range (0, len(topics)):
            create_in_topic = topics[topic_number]
        body = webbasket_templates.tmpl_create_basket(new_basket_name,
                                                      new_topic_name,
                                                      create_in_topic,
                                                      topics,
                                                      ln)
        return (body, [], [])

def perform_request_display_public(bskid=0, of='hb', ln=CFG_SITE_LANG):
    """return html representation of a public basket
    @param bskid: basket id
    @param of: format
    @param ln: language"""
    _ = gettext_set_language(ln)
    body = ''
    errors = []
    warnings = []
    basket = db.get_public_basket_infos(bskid)
    if of[0] == 'x':
        items = []
        if len(basket) == 7:
            content = db.get_basket_content(bskid)
            for item in content:
                items.append(format_record(item[0], of))
        return webbasket_templates.tmpl_xml_basket(items)

    if len(basket) == 7:
        items = db.get_basket_content(bskid)
        last_cmt = _("N/A")
        records = []
        cmt_dates = []
        for (recid, nb_cmt, last_cmt, ext_val, int_val, score) in items:
            cmt_dates.append(convert_datetext_to_datestruct(last_cmt))
            last_cmt = convert_datetext_to_dategui(last_cmt, ln)
            val = ''
            if recid < 0:
                if ext_val:
                    val = decompress(ext_val)
            else:
                if int_val:
                    val = format_record(recid, 'hb')
            records.append((recid, nb_cmt, last_cmt, val, score))
        body = webbasket_templates.tmpl_display_public(basket, records, ln)
    else:
        errors.append('ERR_WEBBASKET_RESTRICTED_ACCESS')
    return (body, errors, warnings)

def perform_request_list_public_baskets(inf_limit=0, order=1, asc=1, ln=CFG_SITE_LANG):
    """Display list of public baskets.
    @param inf_limit: display baskets from inf_limit
    @param order: 1: order by name of basket, 2: number of views, 3: owner
    @param asc: ascending order if 1, descending if 0
    @param ln: language
    """
    errors = []
    warnings = []
    total_baskets = db.count_public_baskets()
    baskets = db.get_public_baskets_list(inf_limit, CFG_WEBBASKET_MAX_NUMBER_OF_DISPLAYED_BASKETS, order, asc)
    body = webbasket_templates.tmpl_display_list_public_baskets(baskets, inf_limit, total_baskets, order, asc, ln)
    return (body, errors, warnings)

def perform_request_subscribe(uid, bskid):
    """subscribe to external basket bskid"""
    errors = []
    if db.is_public(bskid):
        db.subscribe(uid, bskid)
    else:
        errors.append('ERR_WEBBASKET_RESTRICTED_ACCESS')
    return errors

def perform_request_unsubscribe(uid, bskid):
    """unsubscribe from external basket bskid"""
    db.unsubscribe(uid, bskid)

def check_user_can_comment(uid, bskid):
    """ Private function. check if a user can comment """
    min_right = CFG_WEBBASKET_SHARE_LEVELS['ADDCMT']
    rights = db.get_max_user_rights_on_basket(uid, bskid)
    if rights:
        if CFG_WEBBASKET_SHARE_LEVELS_ORDERED.index(rights) >= CFG_WEBBASKET_SHARE_LEVELS_ORDERED.index(min_right):
            return 1
    return 0

def __check_user_can_perform_action(uid, bskid, rights):
    """ Private function, check if a user has sufficient rights"""
    min_right = rights
    rights = db.get_max_user_rights_on_basket(uid, bskid)
    if rights:
        if CFG_WEBBASKET_SHARE_LEVELS_ORDERED.index(rights) >= CFG_WEBBASKET_SHARE_LEVELS_ORDERED.index(min_right):
            return 1
    return 0

def check_sufficient_rights(rights_user_has, rights_needed):
    """Private function, check if the rights are sufficient."""
    try:
        out = CFG_WEBBASKET_SHARE_LEVELS_ORDERED.index(rights_user_has) >= \
              CFG_WEBBASKET_SHARE_LEVELS_ORDERED.index(rights_needed)
    except ValueError:
        out = 0
    return out

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
                           category=CFG_WEBBASKET_CATEGORIES['PRIVATE'],
                           topic=0, group=0,
                           bskid=0, ln=CFG_SITE_LANG):
    """display navtrail for basket navigation.
    @param uid: user id (int)
    @param category: selected category (see CFG_WEBBASKET_CATEGORIES)
    @param topic: selected topic # if personal baskets
    @param group: selected group id for displaying (int)
    @param bskid: basket id (int)
    @param ln: language"""
    _ = gettext_set_language(ln)
    out = ''
    if category == CFG_WEBBASKET_CATEGORIES['PRIVATE']:
        out += ' &gt; <a class="navtrail" href="%s/yourbaskets/display?%s">'\
               '%s</a>'
        out %= (CFG_SITE_URL,
                'category=' + category + '&amp;ln=' + ln,
                _("Personal baskets"))
        topics = map(lambda x: x[0], db.get_personal_topics_infos(uid))
        if topic in range(0, len(topics)):
            out += ' &gt; '
            out += '<a class="navtrail" href="%s/yourbaskets/display?%s">'\
                   '%s</a>'
            out %= (CFG_SITE_URL,
                    'category=' + category + '&amp;topic=' + \
                                  str(topic) + '&amp;ln=' + ln,
                    cgi.escape(topics[topic]))
            if bskid:
                basket = db.get_public_basket_infos(bskid)
                if basket:
                    out += ' &gt; '
                    out += '<a class="navtrail" href="%s/yourbaskets/display'\
                           '?%s">%s</a>'
                    out %= (CFG_SITE_URL,
                            'category=' + category + '&amp;topic=' + \
                            str(topic) + '&amp;ln=' + ln + '#bsk' + str(bskid),
                            cgi.escape(basket[1]))

    elif category == CFG_WEBBASKET_CATEGORIES['GROUP']:
        out += ' &gt; <a class="navtrail" href="%s/yourbaskets/display?%s">'\
               '%s</a>'
        out %= (CFG_SITE_URL, 'category=' + category + '&amp;ln=' + ln, _("Group baskets"))
        groups = db.get_group_infos(uid)
        if group:
            groups = filter(lambda x: x[0] == group, groups)
        if len(groups):
            out += ' &gt; '
            out += '<a class="navtrail" href="%s/yourbaskets/display?%s">%s</a>'
            out %= (CFG_SITE_URL,
                    'category=' + category + '&amp;group=' + \
                              str(group) + '&amp;ln=' + ln,
                    cgi.escape(groups[0][1]))
            if bskid:
                basket = db.get_public_basket_infos(bskid)
                if basket:
                    out += ' &gt; '
                    out += '<a class="navtrail" href="%s/yourbaskets/display?'\
                           '%s">%s</a>'
                    out %= (CFG_SITE_URL,
                            'category=' + category + '&amp;group=' + \
                            str(group) + '&amp;ln=' + ln + '#bsk' + str(bskid),
                            cgi.escape(basket[1]))
    elif category == CFG_WEBBASKET_CATEGORIES['EXTERNAL']:
        out += ' &gt; <a class="navtrail" href="%s/yourbaskets/display?%s">'\
               '%s</a>'
        out %= (CFG_SITE_URL,
                'category=' + category + '&amp;ln=' + ln,
                _("Others' baskets"))
        if bskid:
            basket = db.get_public_basket_infos(bskid)
            if basket:
                out += ' &gt; '
                out += '<a class="navtrail" href="%s/yourbaskets/display?%s">'\
                       '%s</a>'
                out %= (CFG_SITE_URL,
                        'category=' + category + '&amp;ln=' + ln + \
                        '#bsk' + str(bskid),
                        cgi.escape(basket[1]))
    return out

def create_infobox(infos=[]):
    """Create an infos box. infos param should be a list of strings.
    Return formatted infos"""
    return webbasket_templates.tmpl_create_infobox(infos)

def account_list_baskets(uid, ln=CFG_SITE_LANG):
    """Display baskets informations on account page"""
    _ = gettext_set_language(ln)
    (personal, group, external) = db.count_baskets(uid)
    link = '<a href="%s">%s</a>'
    base_url = CFG_SITE_URL + '/yourbaskets/display?category=%s&amp;ln=' + ln
    personal_text = personal
    if personal:
        url = base_url % CFG_WEBBASKET_CATEGORIES['PRIVATE']
        personal_text = link % (url, personal_text)
    group_text = group
    if group:
        url = base_url % CFG_WEBBASKET_CATEGORIES['GROUP']
        group_text = link % (url, group_text)
    external_text = external
    if external:
        url = base_url % CFG_WEBBASKET_CATEGORIES['EXTERNAL']
    else:
        url = CFG_SITE_URL + '/yourbaskets/list_public_baskets?ln=' + ln
    external_text = link % (url, external_text)
    out = _("You have %(x_nb_perso)s personal baskets and are subscribed to %(x_nb_group)s group baskets and %(x_nb_public)s other users public baskets.") %\
        {'x_nb_perso': personal_text,
         'x_nb_group': group_text,
         'x_nb_public': external_text}
    return out
