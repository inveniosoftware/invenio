## $Id$
##
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

__lastupdated__ = """$Date$"""

from mod_python import apache

from invenio.config import weburl, webdir, cdslang
from invenio.messages import gettext_set_language, wash_language
from invenio.webpage import page
from invenio.webuser import getUid, page_not_authorized, isGuestUser
from invenio.messages import wash_language
from invenio.webbasket import *
from invenio.webbasket_config import cfg_webbasket_categories 
from invenio.urlutils import get_referer, redirect_to_url
from invenio.access_control_config import CFG_ACCESS_CONTROL_LEVEL_SITE

imagesurl = "%s/img" % webdir

## rest of the Python code goes below

### CALLABLE INTERFACE

def index(req):
    redirect_to_url(req, '%s/yourbaskets.py/display?%s' % (weburl, req.args))

def display(req,
            category=cfg_webbasket_categories['PRIVATE'], topic=0, group=0,
            bsk_to_sort=0, sort_by_title="", sort_by_date="",
            ln=cdslang):
    """Display basket"""
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)
    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1: 
        return page_not_authorized(req, "../yourbaskets.py/display")
    (body, errors, warnings) = perform_request_display(uid, category,
                                                       topic,
                                                       group,
                                                       ln)
    if isGuestUser(uid):
        body = create_guest_warning_box(ln) + body
    navtrail = '<a class="navtrail" href="%s/youraccount/display">%s</a>'
    navtrail %= (weburl, _("Your Account"))
    navtrail_end = create_basket_navtrail(uid=uid,
                                          category=category, topic=topic, group=group,
                                          ln=ln)
    return page(title       = _("Display baskets"),
                body        = body,
                navtrail    = navtrail + navtrail_end,
                uid         = uid,
                lastupdated = __lastupdated__,
                language    = ln,
                errors      = errors,
                warnings    = warnings,
                req         = req)


def display_item(req,
                 bskid=0, recid=0, format='hb',
                 category=cfg_webbasket_categories['PRIVATE'], topic=0, group=0,
                 ln=cdslang):
    """ Display basket item """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)
    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1: 
        return page_not_authorized(req, "../yourbaskets.py/display_item")
    (body, errors, warnings) = perform_request_display_item(uid=uid,
                                                            bskid=bskid,
                                                            recid=recid,
                                                            format=format,
                                                            category=category,
                                                            topic=topic,
                                                            group_id=group,
                                                            ln=ln)
    if isGuestUser(uid):
        body = create_guest_warning_box(ln) + body
    navtrail = '<a class="navtrail" href="%s/youraccount/display">%s</a>'
    navtrail %= (weburl, _("Your Account"))
    navtrail_end = create_basket_navtrail(uid=uid,
                                          category=category, topic=topic, group=group,
                                          bskid=bskid, ln=ln) 
    return page(title       = _("Details and comments"),
                body        = body,
                navtrail    = navtrail + navtrail_end,
                uid         = uid,
                lastupdated = __lastupdated__,
                language    = ln,
                errors      = errors,
                warnings    = warnings,
                req         = req)


def write_comment(req,
                  bskid=0, recid=0, cmtid=0,
                  category=cfg_webbasket_categories['PRIVATE'], topic=0, group=0,
                  ln=cdslang):
    """Write a comment (just interface for writing)"""
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)
    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1: 
        return page_not_authorized(req, "../yourbaskets.py/write_comment")
    (body, errors, warnings) = perform_request_write_comment(uid=uid,
                                                             bskid=bskid,
                                                             recid=recid,
                                                             cmtid=cmtid,
                                                             category=category,
                                                             topic=topic,
                                                             group_id=group,
                                                             ln=ln)
    navtrail = '<a class="navtrail" href="%s/youraccount/display">%s</a>'
    navtrail %= (weburl, _("Your Account"))
    navtrail_end = create_basket_navtrail(uid=uid,
                                          category=category, topic=topic, group=group,
                                          bskid=bskid, ln=ln) 
    return page(title       = _("Write a comment"),
                body        = body,
                navtrail    = navtrail + navtrail_end,
                uid         = uid,
                lastupdated = __lastupdated__,
                language    = ln,
                errors      = errors,
                warnings    = warnings,
                req         = req)


def save_comment(req, bskid=0, recid=0, title='', text='',
                 category=cfg_webbasket_categories['PRIVATE'], topic=0, group=0,
                 ln=cdslang):
    """Save comment on record in basket"""
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)
    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1: 
        return page_not_authorized(req, "../yourbaskets.py/save_comment")
    (errors_saving, infos) = perform_request_save_comment(uid=uid,
                                                          bskid=bskid,
                                                          recid=recid,
                                                          title=title,
                                                          text=text,
                                                          ln=ln)
    (body, errors_displaying, warnings) = perform_request_display_item(uid=uid,
                                                                       bskid=bskid,
                                                                       recid=recid,
                                                                       format='hb',
                                                                       category=category,
                                                                       topic=topic,
                                                                       group_id=group,
                                                                       infos=infos,
                                                                       ln=ln)
    errors = errors_saving.extend(errors_displaying)
    navtrail = '<a class="navtrail" href="%s/youraccount/display">%s</a>'
    navtrail %= (weburl, _("Your Account"))
    navtrail_end = create_basket_navtrail(uid=uid,
                                          category=category, topic=topic, group=group,
                                          bskid=bskid, ln=ln) 
    return page(title       = _("Details and comments"),
                body        = body,
                navtrail    = navtrail + navtrail_end,
                uid         = uid,
                lastupdated = __lastupdated__,
                language    = ln,
                errors      = errors,
                warnings    = warnings,
                req         = req)

def delete_comment(req, bskid=0, recid=0, cmtid=0, 
                   category=cfg_webbasket_categories['PRIVATE'], topic=0, group=0,
                   ln=cdslang):
    """Delete a comment
    @param bskid: id of basket (int)
    @param recid: id of record (int)
    @param cmtid: id of comment (int)
    @param category: category (see webbasket_config) (str)
    @param topic: nb of topic currently displayed (int)
    @param group: id of group baskets currently displayed (int)
    @param ln: language"""
    uid = getUid(req)
    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1: 
        return page_not_authorized(req, "../yourbaskets.py/delete_comment")
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    recid = wash_url_argument(recid, 'int')
    bskid = wash_url_argument(bskid, 'int')
    category = wash_url_argument(category, 'str')
    topic = wash_url_argument(topic, 'int')
    group = wash_url_argument(group, 'int')
    url = weburl + '/yourbaskets.py/display_item?recid=%i&bskid=%i' % (recid, bskid)
    url += '&category=%s&topic=%i&group=%i&ln=%s' % (category, topic, group, ln)
    errors = perform_request_delete_comment(uid, bskid, recid, cmtid)
    if not(len(errors)):
        redirect_to_url(req, url) 
    else:
        return page(uid         = uid,
                    language    = ln,
                    errors      = errors,
                    req         = req)
    
def add(req, recid=[], referer='',
        new_basket_name='', new_topic_name='', create_in_topic='',
        ln=cdslang, **args):
    """Add records to baskets.
    @param recid: list of records
    @param bskid: list of baskets. If not set or empty, this function will display a form
                  for the selection of baskets.
    @param referer: url of the referer
    @param ln: language
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    if not(type(recid) is list):
        if recid.find(',') != -1:
            recid = wash_url_argument(recid, 'str')
            recid = recid.split(',')
    bskid={}
    for basket_id in args.values():
        basket_id = wash_url_argument(basket_id, 'int')
        if int(basket_id):
            bskid[int(basket_id)] = 1
    uid = getUid(req)
    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1: 
        return page_not_authorized(req, "../yourbaskets.py/add")
    if not referer:
        referer = get_referer(req)
    (body, errors, warnings) = perform_request_add(uid=uid,
                                                   recid=recid,
                                                   bskid=bskid.keys(),
                                                   referer=referer,
                                                   new_basket_name=new_basket_name,
                                                   new_topic_name=new_topic_name,
                                                   create_in_topic=create_in_topic,
                                                   ln=ln)
    if isGuestUser(uid):
        body = create_guest_warning_box(ln) + body
    if not(len(warnings)) :
        title = _("Your Baskets")
    else:
        title = _("Add records to baskets")
    navtrail = '<a class="navtrail" href="%s/youraccount/display">%s</a>'
    navtrail %= (weburl, _("Your Account"))
    return page(title       = title,
                body        = body,
                navtrail    = navtrail,
                uid         = uid,
                lastupdated = __lastupdated__,
                language    = ln,
                errors      = errors,
                warnings    = warnings,
                req         = req)

def delete(req, bskid=-1, confirmed=0,
           category=cfg_webbasket_categories['PRIVATE'], topic=0, group=0,
           ln=cdslang):
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)
    confirmed = wash_url_argument(confirmed, 'int')
    category = wash_url_argument(category, 'str')
    topic = wash_url_argument(topic, 'int')
    group = wash_url_argument(group, 'int')
    bskid = wash_url_argument(bskid, 'int')
    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1: 
        return page_not_authorized(req, "../yourbaskets.py/delete")
    (body, errors, warnings)=perform_request_delete(uid=uid,
                                                    bskid=bskid,
                                                    confirmed=confirmed,
                                                    category=category,
                                                    selected_topic=topic,
                                                    selected_group_id=group,
                                                    ln=ln)
    if confirmed:
        url = weburl + '/yourbaskets.py?category=%s&topic=%i&group=%i&ln=%s' % (category,
                                                                                topic,
                                                                                group,
                                                                                ln)
        redirect_to_url(req, url)
    else:
        navtrail = '<a class="navtrail" href="%s/youraccount/display">%s</a>'
        navtrail %= (weburl, _("Your Account"))
        navtrail_end = create_basket_navtrail(uid=uid,
                                              category=category, topic=topic, group=group,
                                              bskid=bskid, ln=ln)
        if isGuestUser(uid):
            body = create_guest_warning_box(ln) + body
        return page(title = _("Delete a basket"),
                    body        = body,
                    navtrail    = navtrail + navtrail_end,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = ln,
                    errors      = errors,
                    warnings    = warnings,
                    req         = req)

def modify(req, action='', bskid=-1, recid=0,
           category=cfg_webbasket_categories['PRIVATE'], topic=0, group=0, ln=cdslang):
    ln = wash_language(ln)
    category = wash_url_argument(category, 'str')
    topic = wash_url_argument(topic, 'int')
    group = wash_url_argument(group, 'int')
    _ = gettext_set_language(ln)
    uid = getUid(req)
    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1: 
        return page_not_authorized(req, "../yourbaskets.py/modify")
    action = wash_url_argument(action, 'str')
    url = weburl + '/yourbaskets.py/display?category=%s&topic=%i&group=%i&ln=%s' % (category,
                                                                                        topic,
                                                                                        group,
                                                                                        ln)
    if action == cfg_webbasket_actions['DELETE']:
        delete_record(uid, bskid, recid)       
        redirect_to_url(req, url)
    elif action == cfg_webbasket_actions['UP']:
        move_record(uid, bskid, recid, action)
        redirect_to_url(req, url)
    elif action == cfg_webbasket_actions['DOWN']:
        move_record(uid, bskid, recid, action)
        redirect_to_url(req, url)
    elif action == cfg_webbasket_actions['COPY']:
        title = _("Copy record to basket")
        referer = get_referer(req)
        (body, errors, warnings) = perform_request_add(uid=uid,
                                                       recid=[recid],
                                                       referer=referer,
                                                       ln=ln)
        if isGuestUser(uid):
            body = create_guest_warning_box(ln) + body
    else:
        title = ''
        body = ''
        warnings = ''
        errors = [('ERR_WEBBASKET_UNDEFINED_ACTION',)]
    navtrail = '<a class="navtrail" href="%s/youraccount/display">%s</a>'
    navtrail %= (weburl, _("Your Account"))
    navtrail_end = create_basket_navtrail(uid=uid,
                                          category=category, topic=topic, group=group,
                                          bskid=bskid, ln=ln) 
    return page(title = title,
                body        = body,
                navtrail    = navtrail + navtrail_end,
                uid         = uid,
                lastupdated = __lastupdated__,
                language    = ln,
                errors      = errors,
                warnings    = warnings,
                req         = req)

def edit(req, bskid=0, topic='', 
         add_group='', group_cancel='', submit='', cancel='', delete='',
         new_name='', new_topic=-1, new_topic_name='', new_group='', external='', ln=cdslang, **groups):
    """"""
    uid = getUid(req)
    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1: 
        return page_not_authorized(req, "../yourbaskets.py/edit")
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    bskid = wash_url_argument(bskid, 'int')
    topic = wash_url_argument(topic, 'int')
    new_topic = wash_url_argument(new_topic, 'int')
    if cancel:
        url = weburl + '/yourbaskets.py/display?category=%s&topic=%i&ln=%s'
        url %= (cfg_webbasket_categories['PRIVATE'], topic, ln)
        redirect_to_url(req, url)
    elif delete:
        url = weburl + '/yourbaskets.py/delete?bskid=%i&category=%s&topic=%i&ln=%s'
        url %= (bskid, cfg_webbasket_categories['PRIVATE'], topic, ln)
        redirect_to_url(req, url)        
    elif add_group and not(new_group):
        body = perform_request_add_group(uid=uid, bskid=bskid, topic=topic, ln=ln)
        errors = []
        warnings = []
    elif (add_group and new_group) or group_cancel:
        if add_group:
            perform_request_add_group(uid=uid, bskid=bskid, topic=topic, new_group=new_group, ln=ln)
        (body, errors, warnings) = perform_request_edit(uid=uid, bskid=bskid, topic=topic, ln=ln)
    elif submit:
        (body,errors, warnings)=perform_request_edit(uid=uid, bskid=bskid, topic=topic, 
                             new_name=new_name, new_topic=new_topic, new_topic_name=new_topic_name,
                             groups=groups, external=external, ln=ln)  
        if new_topic != -1:
            topic = new_topic
        url = weburl + '/yourbaskets.py/display?category=%s&topic=%i&ln=%s'
        url %= (cfg_webbasket_categories['PRIVATE'], topic, ln)
        redirect_to_url(req, url)
    else:
        (body, errors, warnings) = perform_request_edit(uid=uid, bskid=bskid, topic=topic, ln=ln)
    
    navtrail = '<a class="navtrail" href="%s/youraccount/display">%s</a>'
    navtrail %= (weburl, _("Your Account"))
    navtrail_end = create_basket_navtrail(uid=uid,
                                          category=cfg_webbasket_categories['PRIVATE'],
                                          topic=topic,
                                          group=0,
                                          bskid=bskid, ln=ln)
    if isGuestUser(uid):
        body = create_guest_warning_box(ln) + body
    return page(title = _("Edit basket"),
                body        = body,
                navtrail    = navtrail + navtrail_end,
                uid         = uid,
                lastupdated = __lastupdated__,
                language    = ln,
                errors      = errors,
                warnings    = warnings,
                req         = req)    
        
def create_basket(req, new_basket_name='',
                  new_topic_name='', create_in_topic=-1, topic_number=-1,
                  ln=cdslang):
    """Create basket interface"""
    uid = getUid(req)
    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1: 
        return page_not_authorized(req, "../yourbaskets.py/manage_rights")
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    create_in_topic = wash_url_argument(create_in_topic, 'int')
    if new_basket_name and (new_topic_name or create_in_topic != -1):
        topic = perform_request_create_basket(uid=uid, new_basket_name=new_basket_name,
                                              new_topic_name=new_topic_name,
                                              create_in_topic=create_in_topic)
        url = weburl + '/yourbaskets.py/display?category=%s&topic=%i&ln=%s'
        url %= (cfg_webbasket_categories['PRIVATE'], int(topic), ln)
        redirect_to_url(req, url)
    else:
        (body, errors, warnings) = perform_request_create_basket(uid=uid,
                                                                 new_basket_name=new_basket_name,
                                                                 new_topic_name=new_topic_name,
                                                                 create_in_topic=create_in_topic,
                                                                 topic_number=topic_number,
                                                                 ln=ln)
        navtrail = '<a class="navtrail" href="%s/youraccount/display">%s</a>'
        navtrail %= (weburl, _("Your Account"))
        if isGuestUser(uid):
            body = create_guest_warning_box(ln) + body
        return page(title = _("Create basket"),
                    body        = body,
                    navtrail    = navtrail,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = ln,
                    errors      = errors,
                    warnings    = warnings,
                    req         = req)

def display_public(req, bskid=0, of='hb', ln=cdslang):
    """Display public basket. If of is x** then output will be XML"""
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)    
    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE == 2: 
        return page_not_authorized(req, "../yourbaskets.py/display_public")
    of = wash_url_argument(of, 'str')
    if len(of) and of[0]=='x':
        req.content_type = "text/xml"
        req.send_http_header()
        return perform_request_display_public(bskid=bskid, of=of, ln=ln)
    (body, errors, warnings) = perform_request_display_public(bskid=bskid, ln=ln)
    referer = get_referer(req)
    if 'list_public_basket' not in  referer:
        referer = weburl + '/yourbaskets.py/list_public_baskets?ln=' + ln
    navtrail =  '<a class="navtrail" href="%s">%s</a>' % (referer, _("List of public baskets"))
    return page(title = _("Public basket"),
                body        = body,
                navtrail    = navtrail,
                uid         = uid,
                lastupdated = __lastupdated__,
                language    = ln,
                errors      = errors,
                warnings    = warnings,
                req         = req)
                
def list_public_baskets(req, inf_limit=None, order=1, asc=1, ln=cdslang):
    """"""
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    uid = getUid(req)    
    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE == 2: 
        return page_not_authorized(req, "../yourbaskets.py/unsubscribe")
    (body, errors, warnings) = perform_request_list_public_baskets(inf_limit, order, asc, ln)
    
    return page(title = _("List of public baskets"),
                body        = body,
                navtrail    = '',
                uid         = uid,
                lastupdated = __lastupdated__,
                language    = ln,
                errors      = errors,
                warnings    = warnings,
                req         = req)

def unsubscribe(req, bskid=0, ln=cdslang):
    """"""
    uid = getUid(req)    
    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE == 2: 
        return page_not_authorized(req, "../yourbaskets.py/unsubscribe")
    perform_request_unsubscribe(uid, bskid)
    url = weburl + '/yourbaskets.py/display?category=%s&ln=%s'
    url %= (cfg_webbasket_categories['EXTERNAL'], ln)
    redirect_to_url(req, url)

def subscribe(req, bskid=0, ln=cdslang):
    """"""
    uid = getUid(req)
    if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE == 2: 
        return page_not_authorized(req, "../yourbaskets.py/subscribe")
    errors = perform_request_subscribe(uid, bskid)
    if len(errors):
        return page(errors=errors, uid=uid, language=ln, req=req)
    url = weburl + '/yourbaskets.py/display?category=%s&ln=%s'
    url %= (cfg_webbasket_categories['EXTERNAL'], ln)
    redirect_to_url(req, url)
