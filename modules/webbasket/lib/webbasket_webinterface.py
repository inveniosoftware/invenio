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

"""WebBasket Web Interface."""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

from mod_python import apache

from invenio.config import weburl, webdir, cdslang, \
                           CFG_ACCESS_CONTROL_LEVEL_SITE
from invenio.messages import gettext_set_language
from invenio.webpage import page
from invenio.webuser import getUid, page_not_authorized, isGuestUser
from invenio.webbasket import *
from invenio.webbasket_config import CFG_WEBBASKET_CATEGORIES, \
                                     CFG_WEBBASKET_ACTIONS
from invenio.urlutils import get_referer, redirect_to_url
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory

class WebInterfaceYourBasketsPages(WebInterfaceDirectory):
    """Defines the set of /yourbaskets pages."""

    _exports = ['', 'display', 'display_item', 'write_comment',
                'save_comment', 'delete_comment', 'add', 'delete',
                'modify', 'edit', 'create_basket', 'display_public',
                'list_public_baskets', 'unsubscribe', 'subscribe']

    def index(self, req, form):
        """Index page."""
        redirect_to_url(req, '%s/yourbaskets/display?%s' % (weburl, req.args))

    def display(self, req, form):
        """Display basket"""

        argd = wash_urlargd(form, {'category': 
                                     (str, CFG_WEBBASKET_CATEGORIES['PRIVATE']),
                                   'topic': (int, 0),
                                   'group': (int, 0),
                                   'bsk_to_sort': (int, 0),
                                   'sort_by_title': (str, ""),
                                   'sort_by_date': (str, "")
                                   })
        
        _ = gettext_set_language(argd['ln'])
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1: 
            return page_not_authorized(req, "../yourbaskets/display")
        (body, errors, warnings) = perform_request_display(uid,
                                                           argd['category'],
                                                           argd['topic'],
                                                           argd['group'],
                                                           argd['ln'])
        if isGuestUser(uid):
            body = create_guest_warning_box(argd['ln']) + body
        navtrail = '<a class="navtrail" href="%s/youraccount/display?ln=%s">'\
                   '%s</a>'
        navtrail %= (weburl, argd['ln'], _("Your Account"))
        navtrail_end = create_basket_navtrail(uid=uid,
                                              category=argd['category'],
                                              topic=argd['topic'],
                                              group=argd['group'],
                                              ln=argd['ln'])
        return page(title       = _("Display baskets"),
                    body        = body,
                    navtrail    = navtrail + navtrail_end,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    errors      = errors,
                    warnings    = warnings,
                    req         = req)

    def display_item(self, req, form):
        """ Display basket item """

        argd = wash_urlargd(form, {'bskid': (int, 0),
                                   'recid': (int, 0),
                                   'format': (str, "hb"),
                                   'category': 
                                     (str, CFG_WEBBASKET_CATEGORIES['PRIVATE']),
                                   'topic': (int, 0),
                                   'group': (int, 0)
                                   })

        _ = gettext_set_language(argd['ln'])
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1: 
            return page_not_authorized(req, "../yourbaskets/display_item")
        (body, errors, warnings) = perform_request_display_item(
                                            uid=uid,
                                            bskid=argd['bskid'],
                                            recid=argd['recid'],
                                            format=argd['format'],
                                            category=argd['category'],
                                            topic=argd['topic'],
                                            group_id=argd['group'],
                                            ln=argd['ln'])
        if isGuestUser(uid):
            body = create_guest_warning_box(argd['ln']) + body
        navtrail = '<a class="navtrail" href="%s/youraccount/display?ln=%s">'\
                   '%s</a>'
        navtrail %= (weburl, argd['ln'], _("Your Account"))
        navtrail_end = create_basket_navtrail(uid=uid,
                                              category=argd['category'],
                                              topic=argd['topic'],
                                              group=argd['group'],
                                              bskid=argd['bskid'],
                                              ln=argd['ln']) 
        return page(title       = _("Details and comments"),
                    body        = body,
                    navtrail    = navtrail + navtrail_end,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    errors      = errors,
                    warnings    = warnings,
                    req         = req)

    def write_comment(self, req, form):
        """Write a comment (just interface for writing)"""

        argd = wash_urlargd(form, {'bskid': (int, 0),
                                   'recid': (int, 0),
                                   'cmtid': (int, 0),
                                   'category': 
                                     (str, CFG_WEBBASKET_CATEGORIES['PRIVATE']),
                                   'topic': (int, 0),
                                   'group': (int, 0)
                                   })

        _ = gettext_set_language(argd['ln'])
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1: 
            return page_not_authorized(req, "../yourbaskets/write_comment")
        (body, errors, warnings) = perform_request_write_comment(
                                        uid=uid,
                                        bskid=argd['bskid'],
                                        recid=argd['recid'],
                                        cmtid=argd['cmtid'],
                                        category=argd['category'],
                                        topic=argd['topic'],
                                        group_id=argd['group'],
                                        ln=argd['ln'])
        navtrail = '<a class="navtrail" href="%s/youraccount/display?ln=%s">'\
                   '%s</a>'
        navtrail %= (weburl, argd['ln'], _("Your Account"))
        navtrail_end = create_basket_navtrail(uid=uid,
                                              category=argd['category'],
                                              topic=argd['topic'],
                                              group=argd['group'],
                                              bskid=argd['bskid'],
                                              ln=argd['ln']) 
        return page(title       = _("Write a comment"),
                    body        = body,
                    navtrail    = navtrail + navtrail_end,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    errors      = errors,
                    warnings    = warnings,
                    req         = req)

    def save_comment(self, req, form):
        """Save comment on record in basket"""

        argd = wash_urlargd(form, {'bskid': (int, 0),
                                   'recid': (int, 0),
                                   'title': (str, ""),
                                   'text': (str, ""),
                                   'category': 
                                     (str, CFG_WEBBASKET_CATEGORIES['PRIVATE']),
                                   'topic': (int, 0),
                                   'group': (int, 0)
                                   })

        _ = gettext_set_language(argd['ln'])
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1: 
            return page_not_authorized(req, "../yourbaskets/save_comment")
        (errors_saving, infos) = perform_request_save_comment(
                                        uid=uid,
                                        bskid=argd['bskid'],
                                        recid=argd['recid'],
                                        title=argd['title'],
                                        text=argd['text'],
                                        ln=argd['ln'])
        (body, errors_displaying, warnings) = perform_request_display_item(
                                                    uid=uid,
                                                    bskid=argd['bskid'],
                                                    recid=argd['recid'],
                                                    format='hb',
                                                    category=argd['category'],
                                                    topic=argd['topic'],
                                                    group_id=argd['group'],
                                                    ln=argd['ln'])
        body = create_infobox(infos) + body                                                                   
        errors = errors_saving.extend(errors_displaying)
        navtrail = '<a class="navtrail" href="%s/youraccount/display?ln=%s">'\
                   '%s</a>'
        navtrail %= (weburl, argd['ln'], _("Your Account"))
        navtrail_end = create_basket_navtrail(uid=uid,
                                              category=argd['category'],
                                              topic=argd['topic'],
                                              group=argd['group'],
                                              bskid=argd['bskid'],
                                              ln=argd['ln']) 
        return page(title       = _("Details and comments"),
                    body        = body,
                    navtrail    = navtrail + navtrail_end,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    errors      = errors,
                    warnings    = warnings,
                    req         = req)

    def delete_comment(self, req, form):
        """Delete a comment
        @param bskid: id of basket (int)
        @param recid: id of record (int)
        @param cmtid: id of comment (int)
        @param category: category (see webbasket_config) (str)
        @param topic: nb of topic currently displayed (int)
        @param group: id of group baskets currently displayed (int)
        @param ln: language"""

        argd = wash_urlargd(form, {'bskid': (int, 0),
                                   'recid': (int, 0),
                                   'cmtid': (int, 0),
                                   'category': 
                                     (str, CFG_WEBBASKET_CATEGORIES['PRIVATE']),
                                   'topic': (int, 0),
                                   'group': (int, 0)
                                   })

        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1: 
            return page_not_authorized(req, "../yourbaskets/delete_comment")

        _ = gettext_set_language(argd['ln'])
        url = weburl + '/yourbaskets/display_item?recid=%i&bskid=%i' % \
                            (argd['recid'], argd['bskid'])
        url += '&category=%s&topic=%i&group=%i&ln=%s' % \
                            (argd['category'], argd['topic'],
                             argd['group'], argd['ln'])
        errors = perform_request_delete_comment(uid, 
                                                argd['bskid'], 
                                                argd['recid'], 
                                                argd['cmtid'])
        if not(len(errors)):
            redirect_to_url(req, url) 
        else:
            return page(uid         = uid,
                        title       = '',
                        body        = '',
                        language    = argd['ln'],
                        errors      = errors,
                        req         = req)
    
    def add(self, req, form):
        """Add records to baskets.
        @param recid: list of records to add
        @param bskids: list of baskets to add records to. if not provided, 
                       will return a page where user can select baskets
        @param referer: URL of the referring page
        @param new_basket_name: add record to new basket
        @param new_topic_name: new basket goes into new topic
        @param create_in_topic: # of topic to put basket into
        @param ln: language"""
        argd = wash_urlargd(form, {'recid': (list, []),
                                   'bskids': (list, []),
                                   'referer': (str, ""),
                                   'new_basket_name': (str, ""),
                                   'new_topic_name': (str, ""),
                                   'create_in_topic': (int, -1),
                                   })
        _ = gettext_set_language(argd['ln'])
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1: 
            return page_not_authorized(req, "../yourbaskets/add")
        if not argd['referer']:
            argd['referer'] = get_referer(req)
        (body, errors, warnings) = perform_request_add(
                                        uid=uid,
                                        recids=argd['recid'],
                                        bskids=argd['bskids'],
                                        referer=argd['referer'],
                                        new_basket_name=argd['new_basket_name'],
                                        new_topic_name=argd['new_topic_name'],
                                        create_in_topic=argd['create_in_topic'],
                                        ln=argd['ln'])
        if isGuestUser(uid):
            body = create_guest_warning_box(argd['ln']) + body
        if not(len(warnings)) :
            title = _("Your Baskets")
        else:
            title = _("Add records to baskets")
        navtrail = '<a class="navtrail" href="%s/youraccount/display?ln=%s">'\
                   '%s</a>'
        navtrail %= (weburl, argd['ln'], _("Your Account"))
        return page(title       = title,
                    body        = body,
                    navtrail    = navtrail,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    errors      = errors,
                    warnings    = warnings,
                    req         = req)

    def delete(self, req, form):
        """Delete basket interface"""
        argd = wash_urlargd(form, {'bskid': (int, -1),
                                   'confirmed': (int, 0),
                                   'category': 
                                     (str, CFG_WEBBASKET_CATEGORIES['PRIVATE']),
                                   'topic': (int, 0),
                                   'group': (int, 0),
                                   })

        _ = gettext_set_language(argd['ln'])
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1: 
            return page_not_authorized(req, "../yourbaskets/delete")
        (body, errors, warnings)=perform_request_delete(
                                        uid=uid,
                                        bskid=argd['bskid'],
                                        confirmed=argd['confirmed'],
                                        category=argd['category'],
                                        selected_topic=argd['topic'],
                                        selected_group_id=argd['group'],
                                        ln=argd['ln'])
        if argd['confirmed']:
            url = weburl 
            url += '/yourbaskets/display?category=%s&topic=%i&group=%i&ln=%s' %\
                   (argd['category'], argd['topic'], argd['group'], argd['ln'])
            redirect_to_url(req, url)
        else:
            navtrail = '<a class="navtrail" href="%s/youraccount/display?ln=%s">'\
                       '%s</a>'
            navtrail %= (weburl, argd['ln'], _("Your Account"))
            navtrail_end = create_basket_navtrail(uid=uid,
                                                  category=argd['category'],
                                                  topic=argd['topic'],
                                                  group=argd['group'],
                                                  bskid=argd['bskid'],
                                                  ln=argd['ln'])
            if isGuestUser(uid):
                body = create_guest_warning_box(argd['ln']) + body
            return page(title = _("Delete a basket"),
                        body        = body,
                        navtrail    = navtrail + navtrail_end,
                        uid         = uid,
                        lastupdated = __lastupdated__,
                        language    = argd['ln'],
                        errors      = errors,
                        warnings    = warnings,
                        req         = req)

    def modify(self, req, form):
        """Modify basket content interface (reorder, suppress record, etc.)"""
        argd = wash_urlargd(form, {'action': (str, ""),
                                   'bskid': (int, -1),
                                   'recid': (int, 0),
                                   'category': 
                                     (str, CFG_WEBBASKET_CATEGORIES['PRIVATE']),
                                   'topic': (int, 0),
                                   'group': (int, 0),
                                   })

        _ = gettext_set_language(argd['ln'])
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1: 
            return page_not_authorized(req, "../yourbaskets/modify")
        url = weburl 
        url += '/yourbaskets/display?category=%s&topic=%i&group=%i&ln=%s' %\
               (argd['category'], argd['topic'], argd['group'], argd['ln'])
        if argd['action'] == CFG_WEBBASKET_ACTIONS['DELETE']:
            delete_record(uid, argd['bskid'], argd['recid'])       
            redirect_to_url(req, url)
        elif argd['action'] == CFG_WEBBASKET_ACTIONS['UP']:
            move_record(uid, argd['bskid'], argd['recid'], argd['action'])
            redirect_to_url(req, url)
        elif argd['action'] == CFG_WEBBASKET_ACTIONS['DOWN']:
            move_record(uid, argd['bskid'], argd['recid'], argd['action'])
            redirect_to_url(req, url)
        elif argd['action'] == CFG_WEBBASKET_ACTIONS['COPY']:
            title = _("Copy record to basket")
            referer = get_referer(req)
            (body, errors, warnings) = perform_request_add(uid=uid,
                                                           recids=argd['recid'],
                                                           referer=referer,
                                                           ln=argd['ln'])
            if isGuestUser(uid):
                body = create_guest_warning_box(argd['ln']) + body
        else:
            title = ''
            body = ''
            warnings = ''
            errors = [('ERR_WEBBASKET_UNDEFINED_ACTION',)]
        navtrail = '<a class="navtrail" href="%s/youraccount/display?ln=%s">'\
                   '%s</a>'
        navtrail %= (weburl, argd['ln'], _("Your Account"))
        navtrail_end = create_basket_navtrail(uid=uid,
                                              category=argd['category'],
                                              topic=argd['topic'],
                                              group=argd['group'],
                                              bskid=argd['bskid'], 
                                              ln=argd['ln']) 
        return page(title = title,
                    body        = body,
                    navtrail    = navtrail + navtrail_end,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    errors      = errors,
                    warnings    = warnings,
                    req         = req)

    def edit(self, req, form):
        """Edit basket interface"""
        argd = wash_urlargd(form, {'bskid': (int, 0),
                                   'groups': (list, []),
                                   'topic': (int, 0),
                                   'add_group': (str, ""),
                                   'group_cancel': (str, ""),
                                   'submit': (str, ""),
                                   'cancel': (str, ""),
                                   'delete': (str, ""),
                                   'new_name': (str, ""),
                                   'new_topic': (int, -1),
                                   'new_topic_name': (str, ""),
                                   'new_group': (str, ""),
                                   'external': (str, ""),
                                   })

        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1: 
            return page_not_authorized(req, "../yourbaskets/edit")

        _ = gettext_set_language(argd['ln'])
        if argd['cancel']:
            url = weburl + '/yourbaskets/display?category=%s&topic=%i&ln=%s'
            url %= (CFG_WEBBASKET_CATEGORIES['PRIVATE'], argd['topic'], 
                    argd['ln'])
            redirect_to_url(req, url)
        elif argd['delete']:
            url = weburl 
            url += '/yourbaskets/delete?bskid=%i&category=%s&topic=%i&ln=%s' %\
                   (argd['bskid'], CFG_WEBBASKET_CATEGORIES['PRIVATE'], 
                   argd['topic'], argd['ln'])
            redirect_to_url(req, url)        
        elif argd['add_group'] and not(argd['new_group']):
            body = perform_request_add_group(uid=uid,
                                             bskid=argd['bskid'],
                                             topic=argd['topic'],
                                             ln=argd['ln'])
            errors = []
            warnings = []
        elif (argd['add_group'] and argd['new_group']) or argd['group_cancel']:
            if argd['add_group']:
                perform_request_add_group(uid=uid,
                                          bskid=argd['bskid'],
                                          topic=argd['topic'],
                                          group_id=argd['new_group'],
                                          ln=argd['ln'])
            (body, errors, warnings) = perform_request_edit(uid=uid,
                                                            bskid=argd['bskid'],
                                                            topic=argd['topic'],
                                                            ln=argd['ln'])
        elif argd['submit']:
            (body, errors, warnings) = perform_request_edit(
                                         uid=uid,
                                         bskid=argd['bskid'],
                                         topic=argd['topic'],
                                         new_name=argd['new_name'],
                                         new_topic=argd['new_topic'],
                                         new_topic_name=argd['new_topic_name'],
                                         groups=argd['groups'],
                                         external=argd['external'],
                                         ln=argd['ln'])  
            if argd['new_topic'] != -1:
                argd['topic'] = argd['new_topic']
            url = weburl + '/yourbaskets/display?category=%s&topic=%i&ln=%s' %\
                  (CFG_WEBBASKET_CATEGORIES['PRIVATE'], 
                   argd['topic'], argd['ln'])
            redirect_to_url(req, url)
        else:
            (body, errors, warnings) = perform_request_edit(uid=uid, 
                                                            bskid=argd['bskid'],
                                                            topic=argd['topic'],
                                                            ln=argd['ln'])

        navtrail = '<a class="navtrail" href="%s/youraccount/display?ln=%s">'\
                   '%s</a>'
        navtrail %= (weburl, argd['ln'], _("Your Account"))
        navtrail_end = create_basket_navtrail(
                            uid=uid,
                            category=CFG_WEBBASKET_CATEGORIES['PRIVATE'],
                            topic=argd['topic'],
                            group=0,
                            bskid=argd['bskid'],
                            ln=argd['ln'])
        if isGuestUser(uid):
            body = create_guest_warning_box(argd['ln']) + body
        return page(title = _("Edit basket"),
                    body        = body,
                    navtrail    = navtrail + navtrail_end,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    errors      = errors,
                    warnings    = warnings,
                    req         = req)    
        
    def create_basket(self, req, form):
        """Create basket interface"""

        argd = wash_urlargd(form, {'new_basket_name': (str, ""),
                                   'new_topic_name': (str, ""),
                                   'create_in_topic': (int, -1),
                                   'topic_number': (int, -1),
                                   })

        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1: 
            return page_not_authorized(req, "../yourbaskets/create_basket")

        _ = gettext_set_language(argd['ln'])
        if argd['new_basket_name'] and \
                (argd['new_topic_name'] or argd['create_in_topic'] != -1):
            topic = perform_request_create_basket(
                            uid=uid,
                            new_basket_name=argd['new_basket_name'],
                            new_topic_name=argd['new_topic_name'],
                            create_in_topic=argd['create_in_topic'],
                            ln=argd['ln'])
            url = weburl + '/yourbaskets/display?category=%s&topic=%i&ln=%s'
            url %= (CFG_WEBBASKET_CATEGORIES['PRIVATE'], int(topic), argd['ln'])
            redirect_to_url(req, url)
        else:
            (body, errors, warnings) = perform_request_create_basket(
                                            uid=uid,
                                            new_basket_name=argd['new_basket_name'],
                                            new_topic_name=argd['new_topic_name'],
                                            create_in_topic=argd['create_in_topic'],
                                            topic_number=argd['topic_number'],
                                            ln=argd['ln'])
            navtrail = '<a class="navtrail" href="%s/youraccount/'\
                       'display?ln=%s">%s</a>'
            navtrail %= (weburl, argd['ln'], _("Your Account"))
            if isGuestUser(uid):
                body = create_guest_warning_box(argd['ln']) + body
            return page(title = _("Create basket"),
                        body        = body,
                        navtrail    = navtrail,
                        uid         = uid,
                        lastupdated = __lastupdated__,
                        language    = argd['ln'],
                        errors      = errors,
                        warnings    = warnings,
                        req         = req)

    def display_public(self, req, form):
        """Display public basket. If of is x** then output will be XML"""

        argd = wash_urlargd(form, {'bskid': (int, 0),
                                   'of': (str, "hb"),
                                   })

        _ = gettext_set_language(argd['ln'])
        uid = getUid(req)    
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE == 2: 
            return page_not_authorized(req, "../yourbaskets/display_public")
        if argd['bskid'] == 0:
            # No given basket => display list of public baskets
            (body, errors, warnings) = perform_request_list_public_baskets(
                                            0, 1, 1, 
                                            argd['ln'])
            return page(title = _("List of public baskets"),
                        body        = body,
                        navtrail    = '',
                        uid         = uid,
                        lastupdated = __lastupdated__,
                        language    = argd['ln'],
                        errors      = errors,
                        warnings    = warnings,
                        req         = req)
        if len(argd['of']) and argd['of'][0]=='x':
            # XML output
            req.content_type = "text/xml"
            req.send_http_header()
            return perform_request_display_public(bskid=argd['bskid'],
                                                  of=argd['of'],
                                                  ln=argd['ln'])
        (body, errors, warnings) = perform_request_display_public(
                                            bskid=argd['bskid'],
                                            ln=argd['ln'])
        referer = get_referer(req)
        if 'list_public_basket' not in  referer:
            referer = weburl + '/yourbaskets/list_public_baskets?ln=' + \
                                argd['ln']
        navtrail =  '<a class="navtrail" href="%s">%s</a>' % \
                    (referer, _("List of public baskets"))
        return page(title = _("Public basket"),
                    body        = body,
                    navtrail    = navtrail,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    errors      = errors,
                    warnings    = warnings,
                    req         = req)
                
    def list_public_baskets(self, req, form):
        """List of public baskets interface"""
        argd = wash_urlargd(form, {'inf_limit': (int, 0),
                                   'order': (int, 1),
                                   'asc': (int, 1),
                                   })

        _ = gettext_set_language(argd['ln'])
        uid = getUid(req)    
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE == 2: 
            return page_not_authorized(req, "../yourbaskets/unsubscribe")
        (body, errors, warnings) = perform_request_list_public_baskets(
                                        argd['inf_limit'],
                                        argd['order'],
                                        argd['asc'], argd['ln'])

        return page(title = _("List of public baskets"),
                    body        = body,
                    navtrail    = '',
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    errors      = errors,
                    warnings    = warnings,
                    req         = req)

    def unsubscribe(self, req, form):
        """unsubscribe to basket"""
        argd = wash_urlargd(form, {'bskid': (int, 0),
                                   })
        
        uid = getUid(req)    
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE == 2: 
            return page_not_authorized(req, "../yourbaskets/unsubscribe")
        perform_request_unsubscribe(uid, argd['bskid'])
        url = weburl + '/yourbaskets/display?category=%s&ln=%s'
        url %= (CFG_WEBBASKET_CATEGORIES['EXTERNAL'], argd['ln'])
        redirect_to_url(req, url)

    def subscribe(self, req, form):
        """subscribe to basket"""
        argd = wash_urlargd(form, {'bskid': (int, 0),
                                   })
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE == 2: 
            return page_not_authorized(req, "../yourbaskets/subscribe")
        errors = perform_request_subscribe(uid, argd['bskid'])
        if len(errors):
            return page(errors=errors, 
                        uid=uid, 
                        language=argd['ln'], 
                        body = '', 
                        title = '', 
                        req=req)
        url = weburl + '/yourbaskets/display?category=%s&ln=%s'
        url %= (CFG_WEBBASKET_CATEGORIES['EXTERNAL'], argd['ln'])
        redirect_to_url(req, url)
