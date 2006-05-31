## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

from zlib import decompress

from invenio.config import cdslang, weburl
from invenio.messages import gettext_set_language, wash_language
from invenio.dateutils import convert_datetext_to_dategui, \
                              convert_datetext_to_datestruct,\
                              convert_datestruct_to_dategui
from invenio.urlutils import wash_url_argument
from invenio.search_engine import print_record
from invenio.webbasket_config import cfg_webbasket_share_levels, \
                                     cfg_webbasket_share_levels_ordered, \
                                     cfg_webbasket_categories, \
                                     cfg_webbasket_actions, \
                                     cfg_webbasket_warning_messages, \
                                     cfg_webbasket_error_messages, \
                                     cfg_webbasket_max_number_of_displayed_baskets
import invenio.webbasket_dblayer as db
try:
    import invenio.template
    webbasket_templates = invenio.template.load('webbasket')
except ImportError:
    pass
    
def perform_request_display(uid,
                            category=cfg_webbasket_categories['PRIVATE'],
                            selected_topic=0,
                            selected_group_id=0,
                            ln=cdslang):
    """Display all the baskets of given category, topic or group.
    @param uid: user id
    @param category: selected category (see webbasket_config.py)
    @param selected_topic: # of selected topic to display baskets
    @param selected_group_id: id of group to display baskets
    @param ln: language"""
    warnings = []
    errors = []
    baskets_html = []

    _ = gettext_set_language(ln)
    
    selected_topic = wash_url_argument(selected_topic, 'int')
    selected_group_id = wash_url_argument(selected_group_id, 'int')
    nb_groups = db.count_groups_user_member_of(uid)
    nb_external_baskets = db.count_external_baskets(uid)
    selectionbox = ''
    infobox = ''
    if category == cfg_webbasket_categories['EXTERNAL']:
        baskets = db.get_external_baskets_infos(uid)
        if len(baskets):
            map(list, baskets)
        else:
            category = cfg_webbasket_categories['PRIVATE']
    if category == cfg_webbasket_categories['GROUP']:
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
                    out[-2] = cfg_webbasket_share_levels['MANAGE']
                return out[:-1]
            baskets = map(adapt_group_rights, baskets)
        else:
            category = cfg_webbasket_categories['PRIVATE']
    if category == cfg_webbasket_categories['PRIVATE']:
        topics_list = db.get_personal_topics(uid)
        if not selected_topic and len(topics_list):
            selected_topic = 0
        selectionbox = webbasket_templates.tmpl_topic_selection(topics_list,
                                                                selected_topic,
                                                                ln)
        if len(topics_list) > 0:
            baskets = db.get_personal_baskets_infos(uid, topics_list[selected_topic][0])
        else:
            baskets = []
        def add_manage_rights(item):
            """ Convert a tuple to a list and add rights"""
            out = list(item)
            out.append(cfg_webbasket_share_levels['MANAGE'])
            return out
        baskets = map(add_manage_rights, baskets)
    
    bskids = []
    for basket in baskets:
        bskids.append(basket[0])
    levels = dict(db.is_shared_to(bskids))
    create_link = ''
    if category == cfg_webbasket_categories['PRIVATE']:
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
                     category=cfg_webbasket_categories['PRIVATE'],
                     selected_topic=0, selected_group_id=0,
                     ln=cdslang):
    """Private function. Display a basket giving its category and topic or group.
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
        records.append((recid, nb_cmt, last_cmt, val, score))

    if len(cmt_dates) > 0:
        last_cmt = convert_datestruct_to_dategui(max(cmt_dates), ln)
     
    body = webbasket_templates.tmpl_basket(bskid,
                                           name,
                                           date_modification,
                                           nb_views,
                                           nb_items, last_added,
                                           (__check_sufficient_rights(share_level, cfg_webbasket_share_levels['READITM']),
                                            __check_sufficient_rights(share_level, cfg_webbasket_share_levels['MANAGE']),
                                            __check_sufficient_rights(share_level, cfg_webbasket_share_levels['READCMT']),
                                            __check_sufficient_rights(share_level, cfg_webbasket_share_levels['ADDITM']),
                                            __check_sufficient_rights(share_level, cfg_webbasket_share_levels['DELITM'])),
                                           nb_bsk_cmts, last_cmt,
                                           group_sharing_level,
                                           category, selected_topic, selected_group_id,
                                           records,
                                           ln)
    return (body, errors, warnings)

def perform_request_display_item(uid, bskid, recid, format='hd',
                                 category=cfg_webbasket_categories['PRIVATE'],
                                 topic=0, group_id=0,
                                 infos=[],
                                 ln=cdslang):
    """Display an item of a basket of given category, topic or group.
    @param uid: user id
    @param bskid: basket_id
    @param recid: record id
    @param format: format of the record (hb, hd, etc.)
    @param category: selected category (see webbasket_config.py)
    @param selected_topic: # of selected topic to display baskets
    @param selected_group_id: id of group to display baskets
    @param ln: language""" 

    bskid = wash_url_argument(bskid, 'int')
    recid = wash_url_argument(recid, 'int')
    category = wash_url_argument(category, 'str')
    topic = wash_url_argument(topic, 'int')
    group_id = wash_url_argument(group_id, 'int')
    infos = wash_url_argument(infos, 'list')
    ln = wash_language(ln)
    
    body = ''   
    errors = []
    warnings = []
    
    rights = db.get_max_user_rights_on_basket(uid, bskid)
    if not(__check_sufficient_rights(rights, cfg_webbasket_share_levels['READITM'])):
        errors.append('ERR_WEBBASKET_NO_RIGHTS')
        return (body, errors, warnings)    
    if category == cfg_webbasket_categories['PRIVATE']:
        topics_list = db.get_personal_topics(uid)
        if not topic and len(topics_list):
            topic = 0
        topicsbox = webbasket_templates.tmpl_topic_selection(topics_list, topic, ln)
    elif category == cfg_webbasket_categories['GROUP']:
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
    basket = basket[0]
    
    item_html = webbasket_templates.tmpl_item(basket, 
                                              recid, record, comments,
                                              group_sharing_level, 
                                              (__check_sufficient_rights(rights, cfg_webbasket_share_levels['READCMT']),
                                               __check_sufficient_rights(rights, cfg_webbasket_share_levels['ADDCMT']),
                                               __check_sufficient_rights(rights, cfg_webbasket_share_levels['DELCMT'])),
                                              selected_category=category, selected_topic=topic, selected_group_id=group_id,
                                              ln=ln)
    body = webbasket_templates.tmpl_display(topicsbox=topicsbox, baskets=[item_html], 
                                            selected_category=category, 
                                            nb_groups=db.count_groups_user_member_of(uid),
                                            nb_external_baskets=db.count_external_baskets(uid),
                                            ln=ln)
    return (body, errors, warnings)

def perform_request_write_comment(uid, bskid, recid, cmtid=0,
                                  category=cfg_webbasket_categories['PRIVATE'],
                                  topic=0, group_id=0,
                                  ln=cdslang):
    """Display a comment writing form"""
    uid = wash_url_argument(uid, 'int')
    bskid = wash_url_argument(bskid, 'int')
    recid = wash_url_argument(recid, 'int')
    cmtid = wash_url_argument(cmtid, 'int')
    category = wash_url_argument(category, 'str')
    topic = wash_url_argument(topic, 'int')
    group_id = wash_url_argument(group_id, 'int')
    ln = wash_language(ln)

    body = ''
    warnings = []
    errors = []
    cmt_body = ''
    if not __check_user_can_comment(uid, bskid):
        errors.append(('ERR_WEBBASKET_CANNOT_COMMENT'))
        return (body, errors, warnings)
    if cmtid:
        # this is a reply to another comment
        comment = db.get_comment(cmtid)
        if comment:
            cmt_body = webbasket_templates.tmpl_quote_comment(comment[2], # title
                                                              uid,
                                                              comment[0], # nickname
                                                              comment[4], # date
                                                              comment[3],
                                                              ln)
        else:
            warning = (cfg_webbasket_warning_messages['ERR_WEBBASKET_cmtid_INVALID'], cmtid)
            warnings.append(warning)
    record = db.get_basket_record(bskid, recid, 'hb')
    body = webbasket_templates.tmpl_write_comment(bskid=bskid,
                                                  recid=recid,
                                                  cmt_body=cmt_body,
                                                  record = record,
                                                  selected_category=category,
                                                  selected_topic=topic,
                                                  selected_group_id=group_id,
                                                  warnings=warnings)
    if category == cfg_webbasket_categories['PRIVATE']:
        topics_list = db.get_personal_topics(uid)
        if not topic and len(topics_list):
            topic = 0
        topicsbox = webbasket_templates.tmpl_topic_selection(topics_list, topic, ln)
    elif category == cfg_webbasket_categories['GROUP']:
        groups = db.get_group_infos(uid)
        if group_id == 0 and len(groups):
            group_id = groups[0][0]
        topicsbox = webbasket_templates.tmpl_group_selection(groups, group_id, ln)    
    else:
        topicsbox = ''
    body = webbasket_templates.tmpl_display(topicsbox, '', [ body ], category, ln)
    return (body, errors, warnings)

def perform_request_save_comment(uid, bskid, recid, title='', text='', ln=cdslang):
    """ Save a given comment if able to.
    @param uid: user id (int)
    @param bskid: basket id (int)
    @param recid: record id (int)
    @param title: title of comment (string)
    @param text: comment's body (string)
    @param ln: language (string)
    @return (errors, infos) where errors: list of errors while saving
                                  infos: list of informations to display"""
    uid = wash_url_argument(uid, 'int')
    bskid = wash_url_argument(bskid, 'int')
    recid = wash_url_argument(recid, 'int')
    text = wash_url_argument(text, 'str')
    ln = wash_language(ln)
    
    _ = gettext_set_language(ln)
    errors = []
    infos = []
    if not __check_user_can_comment(uid, bskid):
        errors.append(('ERR_WEBBASKET_CANNOT_COMMENT'))
        return (errors, infos)
    if not(db.save_comment(uid, bskid, recid, title, text)):
        errors.append(('ERR_WEBBASKET_DB_ERROR'))
    else:
        infos.append(_('Your comment has been successfully posted'))
    return (errors, infos)

def perform_request_delete_comment(uid, bskid, recid, cmtid):
    """Delete comment cmtid on record recid for basket bskid."""
    uid = wash_url_argument(uid, 'int')
    bskid = wash_url_argument(bskid, 'int')
    recid = wash_url_argument(recid, 'int')
    cmtid = wash_url_argument(cmtid, 'int')
    errors = []
    if __check_user_can_perform_action(uid, bskid, cfg_webbasket_share_levels['DELCMT']):
        delete_comment(bskid, recid, cmtid)
    else:
        errors.append('ERR_WEBBASKET_NO_RIGHTS')
    return errors

def perform_request_add(uid, recid=[], bskid=[], referer='',
                        new_basket_name='', new_topic_name='', create_in_topic='',
                        ln=cdslang):
    """Add records to baskets
    @param uid: user id
    @param recid: list of records to add
    @param bskid: list of baskets to add records to. if not provided, will return a
                  page where user can select baskets
    @param referer: URL of the referring page
    @param ln: language
    @return (body, errors, warnings) tuple
    """
    uid = wash_url_argument(uid, 'int')
    recid = wash_url_argument(recid, 'list')
    bskid = wash_url_argument(bskid, 'list')
    referer = wash_url_argument(referer, 'str')
    new_basket_name = wash_url_argument(new_basket_name, 'str')
    new_topic_name = wash_url_argument(new_topic_name, 'str')
    create_in_topic = wash_url_argument(create_in_topic, 'str')
    ln = wash_language(ln)
    
    body = ''
    errors = []
    warnings = []
    
    if not(len(recid)):
        warnings.append('WRN_WEBBASKET_NO_RECORD')
        body += webbasket_templates.tmpl_warnings(warnings, ln)
        if referer and not(referer.find(weburl) == -1):
            body += webbasket_templates.tmpl_back_link(referer, ln)
        return (body, errors, warnings)
    
    if new_basket_name != '':
        topic = new_topic_name
        if create_in_topic not in ('','0'):
            topic = create_in_topic
        if topic:
            id_bsk = db.create_basket(uid, new_basket_name, topic)
            bskid.append(id_bsk)
    if len(bskid):       
        # save
        nb_modified_baskets = db.add_to_basket(uid, recid, bskid)
        body = webbasket_templates.tmpl_added_to_basket(nb_modified_baskets, ln)
        body += webbasket_templates.tmpl_back_link(referer, ln)
    else:
        # Display basket_selection
        personal_baskets = db.get_all_personal_baskets_names(uid)
        group_baskets = db.get_all_group_baskets_names(uid)
        external_baskets = db.get_all_external_baskets_names(uid)
        body = webbasket_templates.tmpl_add(recids=recid,
                                            personal_baskets=personal_baskets,
                                            group_baskets=group_baskets,
                                            external_baskets=external_baskets,
                                            topics=db.get_personal_topics(uid), #topics
                                            referer=referer,
                                            ln=ln)
        body += webbasket_templates.tmpl_back_link(referer, ln)
    return (body, errors, warnings)

def perform_request_delete(uid, bskid, confirmed=0,
                           category=cfg_webbasket_categories['PRIVATE'],
                           selected_topic=0, selected_group_id=0,
                           ln=cdslang):
    """Delete a given basket.
    @param uid: user id (user has to be owner of this basket)
    @param bskid: basket id
    @param confirmed: if 0 will return a confirmation page; if 1 will delete it.
    @param category: category currently displayed
    @param selected_topic: topic currently displayed
    @param selected_group id: if category is group, id of the group currently displayed
    @param ln: language
    """
    uid = wash_url_argument(uid, 'int')
    bskid = wash_url_argument(bskid, 'int')
    confirmed = wash_url_argument(confirmed, 'int')
    category = wash_url_argument(category, 'str')
    selected_topic = wash_url_argument(selected_topic, 'int')
    selected_group_id = wash_url_argument(selected_group_id, 'int')
    ln = wash_language(ln)
    
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
    uid = wash_url_argument(uid, 'int')
    bskid = wash_url_argument(bskid, 'int')
    recid = wash_url_argument(recid, 'int')
    if __check_user_can_perform_action(uid, bskid, cfg_webbasket_share_levels['DELITM']):
        db.delete_item(bskid, recid)

def move_record(uid, bskid, recid, direction):
    """Move a record up or down in a basket (change score).
    @param uid: user id (user has to have manage rights over this basket)
    @param bskid: basket id
    @param recid: record we want to move
    @param direction: cfg_webbasket_actions['UP'] or  cfg_webbasket_actions['DOWN'] (default)
    """
    uid = wash_url_argument(uid, 'int')
    bskid = wash_url_argument(bskid, 'int')
    recid = wash_url_argument(recid, 'int')
    direction = wash_url_argument(direction, 'str')
    if __check_user_can_perform_action(uid, bskid, cfg_webbasket_share_levels['MANAGE']):
        db.move_item(bskid, recid, direction)

def perform_request_edit(uid, bskid, topic=0, new_name='', 
                         new_topic = '', new_topic_name='',
                         groups={}, external='', 
                         ln=cdslang):
    """Interface for management of basket. If names, groups or external is provided, 
    will save new rights into database, else will provide interface.
    @param uid: user id (user has to have sufficient rights on this basket
    @param bskid: basket id to change rights on
    @param topic: topic currently used (int)
    @param new_name: new name of basket
    @param new_topic: topic in which to move basket (int), new_topic_name must be left blank
    @param new_topic_name: new topic in which to move basket (will overwrite param new_topic)
    @param groups: dictionary of {usergroup id: new rights}
    @param external: rights for everybody (can be 'NO')
    @param ln: language
    """
    uid = wash_url_argument(uid, 'int')
    bskid = wash_url_argument(bskid, 'int')
    topic = wash_url_argument(topic, 'int')
    new_name = wash_url_argument(new_name, 'str')
    new_topic = wash_url_argument(new_topic, 'int')
    new_topic_name = wash_url_argument(new_topic_name, 'str')
    if not(type(groups) is dict):
        groups = {}
    external = wash_url_argument(external, 'str')
    ln = wash_language(ln)

    body = ''
    errors = []
    warnings = []

    rights = db.get_max_user_rights_on_basket(uid, bskid)
    if rights != cfg_webbasket_share_levels['MANAGE']:
        errors.append(('ERR_WEBBASKET_NO_RIGHTS',))
        return (body, errors, warnings)
    bsk_name = db.get_basket_name(bskid)
    if not(groups) and not(external) and not(new_name) and not(new_topic) and not(new_topic_name):
        # display interface
        topics = db.get_personal_topics(uid)
        groups_rights = db.get_groups_subscribing_to_basket(bskid)
        external_rights = ''
        if groups_rights and groups_rights[0][0] == 0:
            external_rights = groups_rights[0][2]
            groups_rights = groups_rights[1:]
        display_delete = db.check_user_owns_baskets(uid, bskid)
        display_general = display_delete
        body = webbasket_templates.tmpl_edit(bskid=bskid, bsk_name=bsk_name, 
                                             display_general=display_general, topics=topics, topic=topic, 
                                             display_delete=display_delete,
                                             groups_rights=groups_rights, external_rights=external_rights, 
                                             ln=ln)
    else:
        groups['0'] = external
        db.update_rights(bskid, groups)
        if new_name != bsk_name:
            db.rename_basket(bskid, new_name)
        if new_topic_name:
            db.move_baskets_to_topic(uid, bskid, new_topic_name)            
        elif new_topic != -1:
            if db.check_user_owns_baskets(uid, bskid):
                topics = db.get_personal_topics(uid)
                try:
                    new_topic_name = topics[new_topic][0]
                    db.move_baskets_to_topic(uid, bskid, new_topic_name)
                except:
                    errors.append(('ERR_WEBBASKET_DB_ERROR'))
            else:
                topic = 0
            errors.append(('ERR_WEBBASKET_NOT_OWNER')) 
    return (body, errors, warnings)
    
    
def perform_request_manage_rights(uid, bskid, topic=0,
                                  groups={}, external='', ln=cdslang):
    """Interface for management of rights. If groups or external is provided, will save new
    rights into database, else will provide interface.
    @param uid: user id (user has to have sufficient rights on this basket
    @param bskid: basket id to change rights on
    @param topic: topic currently used
    @param groups: dictionary of {usergroup id: new rights}
    @param external: rights for everybody (can be 'NO')
    @param ln: language
    """
    uid = wash_url_argument(uid, 'int')
    bskid = wash_url_argument(bskid, 'int')
    topic = wash_url_argument(topic, 'int')
    if not(type(groups) is dict):
        groups = {}
    external = wash_url_argument(external, 'str')
    ln = wash_language(ln)

    body = ''
    errors = []
    warnings = []

    rights = db.get_max_user_rights_on_basket(uid, bskid)
    if rights != cfg_webbasket_share_levels['MANAGE']:
        errors.append(('ERR_WEBBASKET_NO_RIGHTS',))
        return (body, errors, warnings)
    if not(groups) and not(external):
        bsk_name = db.get_basket_name(bskid)
        groups_rights = db.get_groups_subscribing_to_basket(bskid)
        external_rights = ''
        if groups_rights and groups_rights[0][0] == 0:
            external_rights = groups_rights[0][2]
            groups_rights = groups_rights[1:]
        body = webbasket_templates.tmpl_manage_rights(bskid, bsk_name,
                                                      groups_rights, external_rights,
                                                      topic, ln)
    else:
        groups['0'] = external
        db.update_rights(bskid, groups)
    return (body, errors, warnings)

def perform_request_add_group(uid, bskid, topic=0, group_id=0, ln=cdslang):
    """If group id is specified, share basket bskid to this group;
    else return a page for selection of a group.
    @param uid: user id (selection only of groups user is member of)
    @param bskid: basket id
    @param topic: topic currently displayed
    @param ln: language
    """
    uid = wash_url_argument(uid, 'int')
    bskid = wash_url_argument(bskid, 'int')
    group_id = wash_url_argument(group_id, 'int')
    topic = wash_url_argument(topic, 'int')
    ln = wash_language(ln)
    
    if group_id:
        db.share_basket_with_group(bskid, group_id, cfg_webbasket_share_levels['READITM'])
    else:
        groups = db.get_groups_user_member_of(uid)
        body = webbasket_templates.tmpl_add_group(bskid, topic, groups, ln)
        return body

def perform_request_create_basket(uid,
                                  new_basket_name='',
                                  new_topic_name='', create_in_topic=-1, topic_number=-1,
                                  ln=cdslang):
    """if new_basket_name and topic infos are given create a basket and return topic number,
    else return (body, errors, warnings) tuple of basket creation form.
    @param uid: user id (int)
    @param new_basket_name: name of the basket to create (str)
    @param new_topic_name: name of new topic to create new basket in (str)
    @param create_in_topic: identification number of topic to create new basket in (int)
    @param topic_number: number of topic to preselect on the creation form.
    @pram ln: language
    """
    uid = wash_url_argument(uid, 'int')
    new_basket_name = wash_url_argument(new_basket_name, 'str')
    new_topic_name = wash_url_argument(new_topic_name, 'str')
    create_in_topic = wash_url_argument(create_in_topic, 'int')
    topic_number = wash_url_argument(topic_number, 'int')
    ln = wash_language(ln)
    
    if new_basket_name and (new_topic_name or create_in_topic != -1):
        if new_topic_name:
            topic = new_topic_name
        else:
            topics = db.get_personal_topics(uid)
            try:
                topic = topics[create_in_topic][0]
            except IndexError:
                return 0
        db.create_basket(uid, new_basket_name, topic)
        topics_list = map(lambda x: x[0], db.get_personal_topics(uid))
        try:
            return topics_list.index(topic)
        except ValueError:
            return 0
    else:
        topics = db.get_personal_topics(uid)
        if topic_number > -1 and topic_number < len(topics):
            create_in_topic = topics[topic_number]
            
        body = webbasket_templates.tmpl_create_basket(new_basket_name,
                                                      new_topic_name, create_in_topic,
                                                      topics,
                                                      ln)
        return (body, [], [])
      
def perform_request_display_public(bskid=0, of='hb', ln=cdslang):
    """return html representation of a public basket """
    bskid = wash_url_argument(bskid, 'int')
    of = wash_url_argument(of, 'str')
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    
    body = ''
    errors = []
    warnings = []
    basket = db.get_public_basket_infos(bskid)
    if of[0]=='x':
        items = []
        if len(basket) == 7:
            content = db.get_basket_content(bskid)
            for item in content:
                items.append(print_record(item[0], of))
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
                    val = decompress(int_val)
            records.append((recid, nb_cmt, last_cmt, val, score))
        body = webbasket_templates.tmpl_display_public(basket, records, ln)        
    else:
        errors.append('ERR_WEBBASKET_RESTRICTED_ACCESS')
    return (body, errors, warnings)
    
def perform_request_list_public_baskets(inf_limit=0, order=1, asc=1, ln=cdslang):
    """"""
    inf_limit = wash_url_argument(inf_limit, 'int')
    order = wash_url_argument(order, 'int')
    asc = wash_url_argument(asc, 'int')
    ln = wash_language(ln)
    errors = []
    warnings = []
    
    total_baskets = db.count_public_baskets()
    baskets = db.get_public_baskets_list(inf_limit, cfg_webbasket_max_number_of_displayed_baskets, order, asc)
    body = webbasket_templates.tmpl_display_list_public_baskets(baskets, inf_limit, total_baskets, order, asc, ln)
    return (body, errors, warnings)
        
def perform_request_subscribe(uid, bskid):
    """subscribe to external basket bskid"""
    uid = wash_url_argument(uid, 'int')
    bskid = wash_url_argument(bskid, 'int')
    errors = []
    if db.is_public(bskid):
        db.subscribe(uid, bskid)
    else:
        errors.append('ERR_WEBBASKET_RESTRICTED_ACCESS')
    return errors
        
def perform_request_unsubscribe(uid, bskid):
    """unsubscribe from external basket bskid"""
    uid = wash_url_argument(uid, 'int')
    bskid = wash_url_argument(bskid, 'int')
    unsubscribe(uid, bskid)
    
def __check_user_can_comment(uid, bskid):
    """ Private function. check if a user can comment """
    min_right = cfg_webbasket_share_levels['ADDCMT']
    rights = db.get_max_user_rights_on_basket(uid, bskid)
    if rights:
        if cfg_webbasket_share_levels_ordered.index(rights) >= cfg_webbasket_share_levels_ordered.index(min_right):
            return 1
    return 0

def __check_user_can_perform_action(uid, bskid, rights):
    """ Private function, check if a user has sufficient rights"""
    min_right = rights
    rights = db.get_max_user_rights_on_basket(uid, bskid)
    if rights:
        if cfg_webbasket_share_levels_ordered.index(rights) >= cfg_webbasket_share_levels_ordered.index(min_right):
            return 1
    return 0

def __check_sufficient_rights(rights_user_has, rights_needed):
    """Private function, check if the rights are sufficient."""
    try:
        out = cfg_webbasket_share_levels_ordered.index(rights_user_has) >= cfg_webbasket_share_levels_ordered.index(rights_needed)
    except ValueError:
        out = 0
    return out

def create_guest_warning_box(ln=cdslang):
    """return a warning message about logging into system"""
    ln = wash_language(ln)
    return webbasket_templates.tmpl_create_guest_warning_box(ln)

def create_personal_baskets_selection_box(uid,
                                          html_select_box_name='baskets',
                                          selected_bskid=None,
                                          ln=cdslang):
    """Return HTML box for basket selection. Only for personal baskets.
    @param uid: user id
    @param html_select_box_name: name used in html form
    @param selected_bskid: basket currently selected
    @param ln: language
    """
    baskets = db.get_all_personal_baskets_names(uid)
    return webbasket_templates.tmpl_personal_baskets_selection_box(baskets,
                                                                   html_select_box_name,
                                                                   selected_bskid,
                                                                   ln)

def create_basket_navtrail(uid, 
                           category=cfg_webbasket_categories['PRIVATE'], topic=0, group=0, 
                           bskid=0, ln=cdslang):
    """display navtrail for basket navigation.
    @param uid: user id (int)
    @param category: selected category (see cfg_webbasket_categories)
    @param topic: selected topic # if personal baskets
    @param group: selected group id for displaying (int)
    @param bskid: basket id (int)
    @param ln: language"""
    uid = wash_url_argument(uid, 'int')
    category = wash_url_argument(category, 'str')
    topic = wash_url_argument(topic, 'int')
    group = wash_url_argument(group, 'int')
    bskid = wash_url_argument(bskid, 'int')
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    out = ''
    if category == cfg_webbasket_categories['PRIVATE']:
        out += ' &gt; <a class="navtrail" href="%s/yourbaskets.py/display?%s">%s</a>'
        out %= (weburl, 'category=' + category + '&amp;ln=' + ln, _("Personal baskets"))
        topics = db.get_personal_topics(uid)
        if 0 <= topic < len(topics):
            out += ' &gt; '
            out += '<a class="navtrail" href="%s/yourbaskets.py/display?%s">%s</a>'
            out %= (weburl,
                    'category=' + category + '&amp;topic=' + str(topic) + '&amp;ln=' + ln,
                    topics[topic][0])
            if bskid:
                basket = db.get_public_basket_infos(bskid)
                if basket:
                    out += ' &gt; '
                    out += '<a class="navtrail" href="%s/yourbaskets.py/display?%s">%s</a>'
                    out %= (weburl,
                            'category=' + category + '&amp;topic=' + str(topic) + \
                            '&amp;ln=' + ln + '#bsk' + str(bskid),
                            basket[1])
                
    elif category == cfg_webbasket_categories['GROUP']:
        out += ' &gt; <a class="navtrail" href="%s/yourbaskets.py/display?%s">%s</a>'
        out %= (weburl, 'category=' + category + '&amp;ln=' + ln, _("Group baskets"))
        groups = db.get_group_infos(uid)
        if group:
            groups = filter(lambda x: x[0]==group, groups)
        if len(groups):
            out += ' &gt; '
            out += '<a class="navtrail" href="%s/yourbaskets.py/display?%s">%s</a>'
            out %= (weburl,
                    'category=' + category + '&amp;group=' + str(group) + '&amp;ln=' + ln,
                    groups[0][1])
            if bskid:
                basket = db.get_public_basket_infos(bskid)
                if basket:
                    out += ' &gt; '
                    out += '<a class="navtrail" href="%s/yourbaskets.py/display?%s"">%s</a>'
                    out %= (weburl,
                            'category=' + category + '&amp;group=' + str(group) + \
                            '&amp;ln=' + ln + '#bsk' + str(bskid),
                            basket[1])
    elif category == cfg_webbasket_categories['EXTERNAL']:
        out += ' &gt; <a class="navtrail" href="%s/yourbaskets.py/display?%s">%s</a>'
        out %= (weburl, 'category=' + category + '&amp;ln=' + ln, _("Other's baskets"))
        if bskid:
            basket = db.get_public_basket_infos(bskid)
            if basket:
                out += ' &gt; '
                out += '<a class="navtrail" href="%s/yourbaskets.py/display?%s"">%s</a>'
                out %= (weburl,
                        'category=' + category + '&amp;ln=' + ln + '#bsk' + str(bskid),
                        basket[1])
    return out

def account_list_baskets(uid, ln=cdslang):
    """Display baskets informations on account page"""
    ln = wash_language(ln)
    uid = wash_url_argument(uid, 'int')
    
    _ = gettext_set_language(ln)
    (personal, group, external) = db.count_baskets(uid)
    link = '<a href="%s">%s</a>'
    base_url = weburl + '/yourbaskets.py/display?category=%s&amp;ln=' + ln
    personal_text = _("%i personal baskets") % personal
    if personal:
        url = base_url % cfg_webbasket_categories['PRIVATE']
        personal_text = link % (url, personal_text)
    group_text = _("%i group baskets") % group
    if group:
        url = base_url % cfg_webbasket_categories['GROUP']
        group_text = link % (url, group_text)
    external_text = _("%i other's baskets") % external
    if external:
        url = base_url % cfg_webbasket_categories['EXTERNAL']
    else:
        url = weburl + '/yourbaskets.py/list_public_baskets?ln=' + ln
    external_text = link % (url, external_text) 
    out = _("You have %s and are subscribed to %s and %s.") % (personal_text,
                                                               group_text,
                                                               external_text)
    return out
