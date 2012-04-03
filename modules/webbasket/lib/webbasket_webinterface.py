## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

"""WebBasket Web Interface."""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""
from invenio import webinterface_handler_config as apache

import os
import cgi
import urllib
from invenio.config import CFG_SITE_SECURE_URL, \
                           CFG_ACCESS_CONTROL_LEVEL_SITE, \
                           CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS, \
                           CFG_SITE_SECURE_URL, CFG_PREFIX, CFG_SITE_LANG
from invenio.messages import gettext_set_language
from invenio.webpage import page
from invenio.webuser import getUid, page_not_authorized, isGuestUser
from invenio.webbasket import \
     check_user_can_comment, \
     check_sufficient_rights, \
     perform_request_display, \
     perform_request_search, \
     create_guest_warning_box, \
     create_basket_navtrail, \
     perform_request_write_note, \
     perform_request_save_note, \
     perform_request_delete_note, \
     perform_request_add_group, \
     perform_request_edit, \
     perform_request_edit_topic, \
     perform_request_list_public_baskets, \
     perform_request_unsubscribe, \
     perform_request_subscribe, \
     perform_request_display_public, \
     perform_request_write_public_note, \
     perform_request_save_public_note, \
     delete_record, \
     move_record, \
     perform_request_add, \
     perform_request_create_basket, \
     perform_request_delete, \
     wash_topic, \
     wash_group, \
     perform_request_export_xml, \
     page_start, \
     page_end
from invenio.webbasket_config import CFG_WEBBASKET_CATEGORIES, \
                                     CFG_WEBBASKET_ACTIONS, \
                                     CFG_WEBBASKET_SHARE_LEVELS
from invenio.webbasket_dblayer import get_basket_name, \
     get_max_user_rights_on_basket
from invenio.urlutils import get_referer, redirect_to_url, make_canonical_urlargd
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory
from invenio.webstat import register_customevent
from invenio.errorlib import register_exception
from invenio.webuser import collect_user_info
from invenio.webcomment import check_user_can_attach_file_to_comments
from invenio.access_control_engine import acc_authorize_action
from htmlutils import is_html_text_editor_installed
from ckeditor_invenio_connector import process_CKEditor_upload, send_response
from invenio.bibdocfile import stream_file

class WebInterfaceBasketCommentsFiles(WebInterfaceDirectory):
    """Handle upload and access to files for comments in WebBasket.

       The upload is currently only available through the CKEditor.
    """

    def _lookup(self, component, path):
        """ This handler is invoked for the dynamic URLs (for getting
        and putting attachments) Eg:
        /yourbaskets/attachments/get/31/652/5/file/myfile.pdf
        /yourbaskets/attachments/get/31/552/5/image/myfigure.png
                                 bskid/recid/uid/

        /yourbaskets/attachments/put/31/550/
                                   bskid/recid
        """
        if component == 'get' and len(path) > 4:
            bskid = path[0] # Basket id
            recid = path[1] # Record id
            uid = path[2]   # uid of the submitter
            file_type = path[3]  # file, image, flash or media (as
                                 # defined by CKEditor)

            if file_type in ['file', 'image', 'flash', 'media']:
                file_name = '/'.join(path[4:]) # the filename

                def answer_get(req, form):
                    """Accessing files attached to comments."""
                    form['file'] = file_name
                    form['type'] = file_type
                    form['uid'] = uid
                    form['recid'] = recid
                    form['bskid'] = bskid
                    return self._get(req, form)

                return answer_get, []

        elif component == 'put' and len(path) > 1:
            bskid = path[0] # Basket id
            recid = path[1] # Record id

            def answer_put(req, form):
                """Attaching file to a comment."""
                form['recid'] = recid
                form['bskid'] = bskid
                return self._put(req, form)

            return answer_put, []

        # All other cases: file not found
        return None, []

    def _get(self, req, form):
        """
        Returns a file attached to a comment.

        A file is attached to a comment of a record of a basket, by a
        user (who is the author of the comment), and is of a certain
        type (file, image, etc). Therefore these 5 values are part of
        the URL. Eg:
        CFG_SITE_SECURE_URL/yourbaskets/attachments/get/31/91/5/file/myfile.pdf
                                             bskid/recid/uid
        """
        argd = wash_urlargd(form, {'file': (str, None),
                                   'type': (str, None),
                                   'uid': (int, 0),
                                   'bskid': (int, 0),
                                   'recid': (int, 0)})

        _ = gettext_set_language(argd['ln'])

        # Can user view this basket & record & comment, i.e. can user
        # access its attachments?
        #uid = getUid(req)
        user_info = collect_user_info(req)
        rights = get_max_user_rights_on_basket(argd['uid'], argd['bskid'])

        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))

        if user_info['email'] == 'guest':
            # Ask to login
            target = '/youraccount/login' + \
                     make_canonical_urlargd({'ln' : argd['ln'], 'referer' : \
                                             CFG_SITE_SECURE_URL + user_info['uri']}, {})
            return redirect_to_url(req, target)

        elif not(check_sufficient_rights(rights, CFG_WEBBASKET_SHARE_LEVELS['READITM'])):
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to view this attachment"))

        if not argd['file'] is None:
            # Prepare path to file on disk. Normalize the path so that
            # ../ and other dangerous components are removed.
            path = os.path.abspath(CFG_PREFIX + '/var/data/baskets/comments/' + \
                                   str(argd['bskid']) + '/'  + str(argd['recid']) + '/' + \
                                   str(argd['uid']) + '/' + argd['type'] + '/' + \
                                   argd['file'])

            # Check that we are really accessing attachements
            # directory, for the declared basket and record.
            if path.startswith(CFG_PREFIX + '/var/data/baskets/comments/' + \
                               str(argd['bskid']) + '/' + str(argd['recid'])) and \
                               os.path.exists(path):
                return stream_file(req, path)

        # Send error 404 in all other cases
        return apache.HTTP_NOT_FOUND

    def _put(self, req, form):
        """
        Process requests received from CKEditor to upload files, etc.

        URL eg:
        CFG_SITE_SECURE_URL/yourbaskets/attachments/put/31/91/
                                             bskid/recid/
        """
        if not is_html_text_editor_installed():
            return

        argd = wash_urlargd(form, {'bskid': (int, 0),
                                   'recid': (int, 0)})

        uid = getUid(req)

        # URL where the file can be fetched after upload
        user_files_path = '%(CFG_SITE_SECURE_URL)s/yourbaskets/attachments/get/%(bskid)s/%(recid)i/%(uid)s' % \
                          {'uid': uid,
                           'recid': argd['recid'],
                           'bskid': argd['bskid'],
                           'CFG_SITE_SECURE_URL': CFG_SITE_SECURE_URL}
        # Path to directory where uploaded files are saved
        user_files_absolute_path = '%(CFG_PREFIX)s/var/data/baskets/comments/%(bskid)s/%(recid)s/%(uid)s' % \
                                   {'uid': uid,
                                    'recid': argd['recid'],
                                    'bskid': argd['bskid'],
                                    'CFG_PREFIX': CFG_PREFIX}

        # Check that user can
        # 1. is logged in
        # 2. comment records of this basket (to simplify, we use
        #    WebComment function to check this, even if it is not
        #    entirely adequate)
        # 3. attach files

        user_info = collect_user_info(req)
        (auth_code, dummy) = check_user_can_attach_file_to_comments(user_info, argd['recid'])

        fileurl = ''
        callback_function = ''
        if user_info['email'] == 'guest':
            # 1. User is guest: must login prior to upload
            data ='Please login before uploading file.'
        if not user_info['precached_usebaskets']:
            msg = 'Sorry, you are not allowed to use WebBasket'
        elif not check_user_can_comment(uid, argd['bskid']):
            # 2. User cannot edit comment of this basket
            msg = 'Sorry, you are not allowed to submit files'
        elif auth_code:
            # 3. User cannot submit
            msg = 'Sorry, you are not allowed to submit files.'
        else:
            # Process the upload and get the response
            (msg, uploaded_file_path, filename, fileurl, callback_function) = \
                      process_CKEditor_upload(form, uid, user_files_path, user_files_absolute_path,
                                              recid=argd['recid'])

        send_response(req, msg, fileurl, callback_function)


class WebInterfaceYourBasketsPages(WebInterfaceDirectory):
    """Defines the set of /yourbaskets pages."""

    _exports = ['',
                'display_item',
                'display',
                'search',
                'write_note',
                'save_note',
                'delete_note',
                'add',
                'delete',
                'modify',
                'edit',
                'edit_topic',
                'create_basket',
                'display_public',
                'list_public_baskets',
                'subscribe',
                'unsubscribe',
                'write_public_note',
                'save_public_note',
                'attachments']

    attachments = WebInterfaceBasketCommentsFiles()

    def index(self, req, dummy):
        """Index page."""
        redirect_to_url(req, '%s/yourbaskets/display?%s' % (CFG_SITE_SECURE_URL, req.args))

    def display_item(self, req, dummy):
        """Legacy URL redirection."""
        redirect_to_url(req, '%s/yourbaskets/display?%s' % (CFG_SITE_SECURE_URL, req.args))

    def display(self, req, form):
        """Display basket interface."""
        #import rpdb2; rpdb2.start_embedded_debugger('password', fAllowRemote=True)

        argd = wash_urlargd(form, {'category':
                                     (str, CFG_WEBBASKET_CATEGORIES['PRIVATE']),
                                   'topic': (str, ""),
                                   'group': (int, 0),
                                   'bskid': (int, 0),
                                   'recid': (int, 0),
                                   'bsk_to_sort': (int, 0),
                                   'sort_by_title': (str, ""),
                                   'sort_by_date': (str, ""),
                                   'of': (str, "hb"),
                                   'ln': (str, CFG_SITE_LANG)})

        _ = gettext_set_language(argd['ln'])

        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../yourbaskets/display",
                                       navmenuid = 'yourbaskets')
        if isGuestUser(uid):
            if not CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS:
                return redirect_to_url(req, "%s/youraccount/login%s" % (
                    CFG_SITE_SECURE_URL,
                        make_canonical_urlargd({
                    'referer' : "%s/yourbaskets/display%s" % (
                        CFG_SITE_SECURE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        user_info = collect_user_info(req)
        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))

        (body, dummy, navtrail) = perform_request_display(uid=uid,
                                                   selected_category=argd['category'],
                                                   selected_topic=argd['topic'],
                                                   selected_group_id=argd['group'],
                                                   selected_bskid=argd['bskid'],
                                                   selected_recid=argd['recid'],
                                                   of=argd['of'],
                                                   ln=argd['ln'])

        if isGuestUser(uid):
            body = create_guest_warning_box(argd['ln']) + body

        # register event in webstat
        if user_info['email']:
            user_str = "%s (%d)" % (user_info['email'], user_info['uid'])
        else:
            user_str = ""
        try:
            register_customevent("baskets", ["display", "", user_str])
        except:
            register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

        rssurl = CFG_SITE_SECURE_URL + "/rss"

        if argd['of'] != 'hb':
            page_start(req, of=argd['of'])

            if argd['of'].startswith('x'):
                req.write(body)
                page_end(req, of=argd['of'])
                return

        elif argd['bskid']:
            rssurl = "%s/yourbaskets/display?category=%s&amp;topic=%s&amp;group=%i&amp;bskid=%i&amp;of=xr" % \
                     (CFG_SITE_SECURE_URL,
                      argd['category'],
                      urllib.quote(argd['topic']),
                      argd['group'],
                      argd['bskid'])

        return page(title       = _("Display baskets"),
                    body        = body,
                    navtrail    = navtrail,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    req         = req,
                    navmenuid   = 'yourbaskets',
                    of          = argd['of'],
                    navtrail_append_title_p = 0,
                    secure_page_p=1,
                    rssurl=rssurl)

    def search(self, req, form):
        """Search baskets interface."""
        argd = wash_urlargd(form, {'category': (str, ""),
                                   'topic': (str, ""),
                                   'group': (int, 0),
                                   'p': (str, ""),
                                   'b': (str, ""),
                                   'n': (int, 0),
                                   'of': (str, "hb"),
                                   'verbose': (int, 0),
                                   'ln': (str, CFG_SITE_LANG)})

        _ = gettext_set_language(argd['ln'])

        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../yourbaskets/search",
                                       navmenuid = 'yourbaskets')
        if isGuestUser(uid):
            if not CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS:
                return redirect_to_url(req, "%s/youraccount/login%s" % (
                    CFG_SITE_SECURE_URL,
                        make_canonical_urlargd({
                    'referer' : "%s/yourbaskets/search%s" % (
                        CFG_SITE_SECURE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        user_info = collect_user_info(req)
        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))

        (body, navtrail) = perform_request_search(uid=uid,
                                                  selected_category=argd['category'],
                                                  selected_topic=argd['topic'],
                                                  selected_group_id=argd['group'],
                                                  p=argd['p'],
                                                  b=argd['b'],
                                                  n=argd['n'],
#                                                  format=argd['of'],
                                                  ln=argd['ln'])

        # register event in webstat
        if user_info['email']:
            user_str = "%s (%d)" % (user_info['email'], user_info['uid'])
        else:
            user_str = ""
        try:
            register_customevent("baskets", ["search", "", user_str])
        except:
            register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

        return page(title       = _("Search baskets"),
                    body        = body,
                    navtrail    = navtrail,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    req         = req,
                    navmenuid   = 'yourbaskets',
                    of          = argd['of'],
                    navtrail_append_title_p = 0,
                    secure_page_p=1)

    def write_note(self, req, form):
        """Write a comment (just interface for writing)"""

        argd = wash_urlargd(form, {'category': (str, CFG_WEBBASKET_CATEGORIES['PRIVATE']),
                                   'topic': (str, ""),
                                   'group': (int, 0),
                                   'bskid': (int, 0),
                                   'recid': (int, 0),
                                   'cmtid': (int, 0),
                                   'of'   : (str, ''),
                                   'ln': (str, CFG_SITE_LANG)})

        _ = gettext_set_language(argd['ln'])
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../yourbaskets/write_note",
                                       navmenuid = 'yourbaskets')

        if isGuestUser(uid):
            if not CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS:
                return redirect_to_url(req, "%s/youraccount/login%s" % (
                    CFG_SITE_SECURE_URL,
                        make_canonical_urlargd({
                    'referer' : "%s/yourbaskets/write_note%s" % (
                        CFG_SITE_SECURE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        user_info = collect_user_info(req)
        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))

        (body, navtrail) = perform_request_write_note(uid=uid,
                                                      category=argd['category'],
                                                      topic=argd['topic'],
                                                      group_id=argd['group'],
                                                      bskid=argd['bskid'],
                                                      recid=argd['recid'],
                                                      cmtid=argd['cmtid'],
                                                      ln=argd['ln'])

        # register event in webstat
        basket_str = "%s (%d)" % (get_basket_name(argd['bskid']), argd['bskid'])
        if user_info['email']:
            user_str = "%s (%d)" % (user_info['email'], user_info['uid'])
        else:
            user_str = ""
        try:
            register_customevent("baskets", ["write_note", basket_str, user_str])
        except:
            register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

        return page(title       = _("Add a note"),
                    body        = body,
                    navtrail    = navtrail,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    req         = req,
                    navmenuid   = 'yourbaskets',
                    of          = argd['of'],
                    secure_page_p=1)

    def save_note(self, req, form):
        """Save comment on record in basket"""

        argd = wash_urlargd(form, {'category': (str, CFG_WEBBASKET_CATEGORIES['PRIVATE']),
                                   'topic': (str, ""),
                                   'group': (int, 0),
                                   'bskid': (int, 0),
                                   'recid': (int, 0),
                                   'note_title': (str, ""),
                                   'note_body': (str, ""),
                                   'date_creation': (str, ""),
                                   'editor_type': (str, ""),
                                   'of': (str, ''),
                                   'ln': (str, CFG_SITE_LANG),
                                   'reply_to': (int, 0)})

        _ = gettext_set_language(argd['ln'])
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../yourbaskets/save_note",
                                       navmenuid = 'yourbaskets')

        if isGuestUser(uid):
            if not CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS:
                return redirect_to_url(req, "%s/youraccount/login%s" % (
                    CFG_SITE_SECURE_URL,
                        make_canonical_urlargd({
                    'referer' : "%s/yourbaskets/save_note%s" % (
                        CFG_SITE_SECURE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        user_info = collect_user_info(req)
        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))

        (body, navtrail) = perform_request_save_note(uid=uid,
                                                     category=argd['category'],
                                                     topic=argd['topic'],
                                                     group_id=argd['group'],
                                                     bskid=argd['bskid'],
                                                     recid=argd['recid'],
                                                     note_title=argd['note_title'],
                                                     note_body=argd['note_body'],
                                                     date_creation=argd['date_creation'],
                                                     editor_type=argd['editor_type'],
                                                     ln=argd['ln'],
                                                     reply_to=argd['reply_to'])

        # TODO: do not stat event if save was not succussful
        # register event in webstat
        basket_str = "%s (%d)" % (get_basket_name(argd['bskid']), argd['bskid'])
        if user_info['email']:
            user_str = "%s (%d)" % (user_info['email'], user_info['uid'])
        else:
            user_str = ""
        try:
            register_customevent("baskets", ["save_note", basket_str, user_str])
        except:
            register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

        return page(title       = _("Display item and notes"),
                    body        = body,
                    navtrail    = navtrail,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    req         = req,
                    navmenuid   = 'yourbaskets',
                    of          = argd['of'],
                    navtrail_append_title_p = 0,
                    secure_page_p=1)

    def delete_note(self, req, form):
        """Delete a comment
        @param bskid: id of basket (int)
        @param recid: id of record (int)
        @param cmtid: id of comment (int)
        @param category: category (see webbasket_config) (str)
        @param topic: nb of topic currently displayed (int)
        @param group: id of group baskets currently displayed (int)
        @param ln: language"""

        argd = wash_urlargd(form, {'category': (str, CFG_WEBBASKET_CATEGORIES['PRIVATE']),
                                   'topic': (str, ""),
                                   'group': (int, 0),
                                   'bskid': (int, 0),
                                   'recid': (int, 0),
                                   'cmtid': (int, 0),
                                   'of'   : (str, ''),
                                   'ln': (str, CFG_SITE_LANG)})

        _ = gettext_set_language(argd['ln'])

        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../yourbaskets/delete_note",
                                       navmenuid = 'yourbaskets')

        if isGuestUser(uid):
            if not CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS:
                return redirect_to_url(req, "%s/youraccount/delete_note%s" % (
                    CFG_SITE_SECURE_URL,
                        make_canonical_urlargd({
                    'referer' : "%s/yourbaskets/display%s" % (
                        CFG_SITE_SECURE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        user_info = collect_user_info(req)
        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))

        (body, navtrail) = perform_request_delete_note(uid=uid,
                                                       category=argd['category'],
                                                       topic=argd['topic'],
                                                       group_id=argd['group'],
                                                       bskid=argd['bskid'],
                                                       recid=argd['recid'],
                                                       cmtid=argd['cmtid'],
                                                       ln=argd['ln'])

        # TODO: do not stat event if delete was not succussful
        # register event in webstat
        basket_str = "%s (%d)" % (get_basket_name(argd['bskid']), argd['bskid'])
        user_info = collect_user_info(req)
        if user_info['email']:
            user_str = "%s (%d)" % (user_info['email'], user_info['uid'])
        else:
            user_str = ""
        try:
            register_customevent("baskets", ["delete_note", basket_str, user_str])
        except:
            register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

        return page(title       = _("Display item and notes"),
                    body        = body,
                    navtrail    = navtrail,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    req         = req,
                    navmenuid   = 'yourbaskets',
                    of          = argd['of'],
                    navtrail_append_title_p = 0,
                    secure_page_p=1)

    def add(self, req, form):
        """Add records to baskets.
        @param recid: list of records to add
        @param colid: in case of external collections, the id of the collection the records belong to
        @param bskids: list of baskets to add records to. if not provided,
                       will return a page where user can select baskets
        @param referer: URL of the referring page
        @param new_basket_name: add record to new basket
        @param new_topic_name: new basket goes into new topic
        @param create_in_topic: # of topic to put basket into
        @param ln: language"""

        # TODO: apply a maximum limit of items (100) that can be added to a basket
        # at once. Also see the build_search_url function of websearch_..._searcher.py
        # for the "rg" GET variable.
        argd = wash_urlargd(form, {'recid': (list, []),
                                   'category': (str, ""),
                                   'bskid': (int, 0),
                                   'colid': (int, 0),
                                   'es_title': (str, ""),
                                   'es_desc': (str, ""),
                                   'es_url': (str, ""),
                                   'note_body': (str, ""),
                                   'date_creation': (str, ""),
                                   'editor_type': (str, ""),
                                   'b': (str, ""),
                                   'copy': (int, 0),
                                   'wait': (int, 0),
                                   'referer': (str, ""),
                                   "of" : (str, ''),
                                   'ln': (str, CFG_SITE_LANG)})

        _ = gettext_set_language(argd['ln'])

        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../yourbaskets/add",
                                       navmenuid = 'yourbaskets')

        if isGuestUser(uid):
            if not CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS:
                return redirect_to_url(req, "%s/youraccount/login%s" % (
                    CFG_SITE_SECURE_URL,
                        make_canonical_urlargd({
                    'referer' : "%s/yourbaskets/add%s" % (
                        CFG_SITE_SECURE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        user_info = collect_user_info(req)
        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))

        if not argd['referer']:
            argd['referer'] = get_referer(req)

        (body, navtrail) = perform_request_add(uid=uid,
                                               recids=argd['recid'],
                                               colid=argd['colid'],
                                               bskid=argd['bskid'],
                                               es_title=argd['es_title'],
                                               es_desc=argd['es_desc'],
                                               es_url=argd['es_url'],
                                               note_body=argd['note_body'],
                                               date_creation=argd['date_creation'],
                                               editor_type=argd['editor_type'],
                                               category=argd['category'],
                                               b=argd['b'],
                                               copy=argd['copy'],
                                               wait=argd['wait'],
                                               referer=argd['referer'],
                                               ln=argd['ln'])

        if isGuestUser(uid):
            body = create_guest_warning_box(argd['ln']) + body

        # register event in webstat
        bskid = argd['bskid']
        basket_str = "%s (%s)" % (get_basket_name(bskid), bskid)
        if user_info['email']:
            user_str = "%s (%d)" % (user_info['email'], user_info['uid'])
        else:
            user_str = ""
        try:
            register_customevent("baskets", ["add", basket_str, user_str])
        except:
            register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

        return page(title       = _('Add to basket'),
                    body        = body,
                    navtrail    = navtrail,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    req         = req,
                    navmenuid   = 'yourbaskets',
                    of          = argd['of'],
                    navtrail_append_title_p = 0,
                    secure_page_p=1)

    def delete(self, req, form):
        """Delete basket interface"""
        argd = wash_urlargd(form, {'bskid'      : (int, -1),
                                   'confirmed'  : (int, 0),
                                   'category'   : (str, CFG_WEBBASKET_CATEGORIES['PRIVATE']),
                                   'topic'      : (str, ""),
                                   'group'      : (int, 0),
                                   'of'         : (str, ''),
                                   'ln'         : (str, CFG_SITE_LANG)})

        _ = gettext_set_language(argd['ln'])
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../yourbaskets/delete",
                                       navmenuid = 'yourbaskets')

        if isGuestUser(uid):
            if not CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS:
                return redirect_to_url(req, "%s/youraccount/login%s" % (
                    CFG_SITE_SECURE_URL,
                        make_canonical_urlargd({
                    'referer' : "%s/yourbaskets/delete%s" % (
                        CFG_SITE_SECURE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        user_info = collect_user_info(req)
        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))

        body=perform_request_delete(uid=uid,
                                    bskid=argd['bskid'],
                                    confirmed=argd['confirmed'],
                                    category=argd['category'],
                                    selected_topic=argd['topic'],
                                    selected_group_id=argd['group'],
                                    ln=argd['ln'])
        if argd['confirmed']:
            if argd['category'] == CFG_WEBBASKET_CATEGORIES['PRIVATE']:
                argd['topic'] = wash_topic(uid, argd['topic'])[0]
            elif argd['category'] == CFG_WEBBASKET_CATEGORIES['GROUP']:
                argd['group'] = wash_group(uid, argd['group'])[0]
            url = """%s/yourbaskets/display?category=%s&topic=%s&group=%i&ln=%s""" % \
                  (CFG_SITE_SECURE_URL,
                   argd['category'],
                   urllib.quote(argd['topic']),
                   argd['group'],
                   argd['ln'])
            redirect_to_url(req, url)
        else:
            navtrail = '<a class="navtrail" href="%s/youraccount/display?ln=%s">'\
                       '%s</a>'
            navtrail %= (CFG_SITE_SECURE_URL, argd['ln'], _("Your Account"))
            navtrail_end = create_basket_navtrail(uid=uid,
                                                  category=argd['category'],
                                                  topic=argd['topic'],
                                                  group=argd['group'],
                                                  bskid=argd['bskid'],
                                                  ln=argd['ln'])
            if isGuestUser(uid):
                body = create_guest_warning_box(argd['ln']) + body

            # register event in webstat
            basket_str = "%s (%d)" % (get_basket_name(argd['bskid']), argd['bskid'])
            if user_info['email']:
                user_str = "%s (%d)" % (user_info['email'], user_info['uid'])
            else:
                user_str = ""
            try:
                register_customevent("baskets", ["delete", basket_str, user_str])
            except:
                register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

            return page(title = _("Delete a basket"),
                        body        = body,
                        navtrail    = navtrail + navtrail_end,
                        uid         = uid,
                        lastupdated = __lastupdated__,
                        language    = argd['ln'],
                        req         = req,
                        navmenuid   = 'yourbaskets',
                        of          = argd['of'],
                        secure_page_p=1)

    def modify(self, req, form):
        """Modify basket content interface (reorder, suppress record, etc.)"""

        argd = wash_urlargd(form, {'action': (str, ""),
                                   'bskid': (int, -1),
                                   'recid': (int, 0),
                                   'category': (str, CFG_WEBBASKET_CATEGORIES['PRIVATE']),
                                   'topic': (str, ""),
                                   'group': (int, 0),
                                   'of'   : (str, ''),
                                   'ln': (str, CFG_SITE_LANG)})

        _ = gettext_set_language(argd['ln'])

        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../yourbaskets/modify",
                                       navmenuid = 'yourbaskets')

        if isGuestUser(uid):
            if not CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS:
                return redirect_to_url(req, "%s/youraccount/login%s" % (
                    CFG_SITE_SECURE_URL,
                        make_canonical_urlargd({
                    'referer' : "%s/yourbaskets/modify%s" % (
                        CFG_SITE_SECURE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        user_info = collect_user_info(req)
        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))

        url = CFG_SITE_SECURE_URL
        url += '/yourbaskets/display?category=%s&topic=%s&group=%i&bskid=%i&ln=%s' % \
               (argd['category'], urllib.quote(argd['topic']), argd['group'], argd['bskid'], argd['ln'])
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
            (body, navtrail) = perform_request_add(uid=uid,
                                                   recids=argd['recid'],
                                                   copy=True,
                                                   referer=referer,
                                                   ln=argd['ln'])
            if isGuestUser(uid):
                body = create_guest_warning_box(argd['ln']) + body
        else:
            title = ''
            body = ''
#            warnings = [('WRN_WEBBASKET_UNDEFINED_ACTION',)]
        navtrail = '<a class="navtrail" href="%s/youraccount/display?ln=%s">'\
                   '%s</a>'
        navtrail %= (CFG_SITE_SECURE_URL, argd['ln'], _("Your Account"))
        navtrail_end = create_basket_navtrail(uid=uid,
                                              category=argd['category'],
                                              topic=argd['topic'],
                                              group=argd['group'],
                                              bskid=argd['bskid'],
                                              ln=argd['ln'])

        # register event in webstat
        basket_str = "%s (%d)" % (get_basket_name(argd['bskid']), argd['bskid'])
        if user_info['email']:
            user_str = "%s (%d)" % (user_info['email'], user_info['uid'])
        else:
            user_str = ""
        try:
            register_customevent("baskets", ["modify", basket_str, user_str])
        except:
            register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

        return page(title = title,
                    body        = body,
                    navtrail    = navtrail + navtrail_end,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    req         = req,
                    navmenuid   = 'yourbaskets',
                    of          = argd['of'],
                    secure_page_p=1)

    def edit(self, req, form):
        """Edit basket interface"""
        argd = wash_urlargd(form, {'bskid': (int, 0),
                                   'groups': (list, []),
                                   'topic': (str, ""),
                                   'add_group': (str, ""),
                                   'group_cancel': (str, ""),
                                   'submit': (str, ""),
                                   'cancel': (str, ""),
                                   'delete': (str, ""),
                                   'new_name': (str, ""),
                                   'new_topic': (str, ""),
                                   'new_topic_name': (str, ""),
                                   'new_group': (str, ""),
                                   'external': (str, ""),
                                   'of'      : (str, ''),
                                   'ln': (str, CFG_SITE_LANG)})

        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../yourbaskets/edit",
                                       navmenuid = 'yourbaskets')

        if isGuestUser(uid):
            if not CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS:
                return redirect_to_url(req, "%s/youraccount/login%s" % (
                    CFG_SITE_SECURE_URL,
                        make_canonical_urlargd({
                    'referer' : "%s/yourbaskets/edit%s" % (
                        CFG_SITE_SECURE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        _ = gettext_set_language(argd['ln'])
        user_info = collect_user_info(req)
        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))

        if argd['cancel']:
            url = CFG_SITE_SECURE_URL + '/yourbaskets/display?category=%s&topic=%s&ln=%s'
            url %= (CFG_WEBBASKET_CATEGORIES['PRIVATE'],
                    urllib.quote(argd['topic']),
                    argd['ln'])
            redirect_to_url(req, url)
        elif argd['delete']:
            url = CFG_SITE_SECURE_URL
            url += '/yourbaskets/delete?bskid=%i&category=%s&topic=%s&ln=%s' % \
                   (argd['bskid'],
                    CFG_WEBBASKET_CATEGORIES['PRIVATE'],
                    urllib.quote(argd['topic']),
                    argd['ln'])
            redirect_to_url(req, url)
        elif argd['add_group'] and not(argd['new_group']):
            body = perform_request_add_group(uid=uid,
                                             bskid=argd['bskid'],
                                             topic=argd['topic'],
                                             ln=argd['ln'])
#            warnings = []
        elif (argd['add_group'] and argd['new_group']) or argd['group_cancel']:
            if argd['add_group']:
                perform_request_add_group(uid=uid,
                                          bskid=argd['bskid'],
                                          topic=argd['topic'],
                                          group_id=argd['new_group'],
                                          ln=argd['ln'])
            body = perform_request_edit(uid=uid,
                                        bskid=argd['bskid'],
                                        topic=argd['topic'],
                                        ln=argd['ln'])
        elif argd['submit']:
            body = perform_request_edit(uid=uid,
                                        bskid=argd['bskid'],
                                        topic=argd['topic'],
                                        new_name=argd['new_name'],
                                        new_topic=argd['new_topic'],
                                        new_topic_name=argd['new_topic_name'],
                                        groups=argd['groups'],
                                        external=argd['external'],
                                        ln=argd['ln'])
            if argd['new_topic'] != "-1":
                argd['topic'] = argd['new_topic']
            url = CFG_SITE_SECURE_URL + '/yourbaskets/display?category=%s&topic=%s&ln=%s' % \
                  (CFG_WEBBASKET_CATEGORIES['PRIVATE'],
                   urllib.quote(argd['topic']),
                   argd['ln'])
            redirect_to_url(req, url)
        else:
            body = perform_request_edit(uid=uid,
                                        bskid=argd['bskid'],
                                        topic=argd['topic'],
                                        ln=argd['ln'])

        navtrail = '<a class="navtrail" href="%s/youraccount/display?ln=%s">'\
                   '%s</a>'
        navtrail %= (CFG_SITE_SECURE_URL, argd['ln'], _("Your Account"))
        navtrail_end = create_basket_navtrail(
                            uid=uid,
                            category=CFG_WEBBASKET_CATEGORIES['PRIVATE'],
                            topic=argd['topic'],
                            group=0,
                            bskid=argd['bskid'],
                            ln=argd['ln'])
        if isGuestUser(uid):
            body = create_guest_warning_box(argd['ln']) + body

        # register event in webstat
        basket_str = "%s (%d)" % (get_basket_name(argd['bskid']), argd['bskid'])
        if user_info['email']:
            user_str = "%s (%d)" % (user_info['email'], user_info['uid'])
        else:
            user_str = ""
        try:
            register_customevent("baskets", ["edit", basket_str, user_str])
        except:
            register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

        return page(title = _("Edit basket"),
                    body        = body,
                    navtrail    = navtrail + navtrail_end,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    req         = req,
                    navmenuid   = 'yourbaskets',
                    of          = argd['of'],
                    secure_page_p=1)

    def edit_topic(self, req, form):
        """Edit topic interface"""
        argd = wash_urlargd(form, {'topic': (str, ""),
                                   'submit': (str, ""),
                                   'cancel': (str, ""),
                                   'delete': (str, ""),
                                   'new_name': (str, ""),
                                   'of'      : (str, ''),
                                   'ln': (str, CFG_SITE_LANG)})

        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../yourbaskets/edit",
                                       navmenuid = 'yourbaskets')

        if isGuestUser(uid):
            if not CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS:
                return redirect_to_url(req, "%s/youraccount/login%s" % (
                    CFG_SITE_SECURE_URL,
                        make_canonical_urlargd({
                    'referer' : "%s/yourbaskets/edit_topic%s" % (
                        CFG_SITE_SECURE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        _ = gettext_set_language(argd['ln'])
        user_info = collect_user_info(req)
        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))

        if argd['cancel']:
            url = CFG_SITE_SECURE_URL + '/yourbaskets/display?category=%s&ln=%s'
            url %= (CFG_WEBBASKET_CATEGORIES['PRIVATE'], argd['ln'])
            redirect_to_url(req, url)
        elif argd['delete']:
            url = CFG_SITE_SECURE_URL
            url += '/yourbaskets/delete?bskid=%i&category=%s&topic=%s&ln=%s' % \
                   (argd['bskid'],
                    CFG_WEBBASKET_CATEGORIES['PRIVATE'],
                    urllib.quote(argd['topic']),
                    argd['ln'])
            redirect_to_url(req, url)
        elif argd['submit']:
            body = perform_request_edit_topic(uid=uid,
                                              topic=argd['topic'],
                                              new_name=argd['new_name'],
                                              ln=argd['ln'])
            url = CFG_SITE_SECURE_URL + '/yourbaskets/display?category=%s&ln=%s' % \
                  (CFG_WEBBASKET_CATEGORIES['PRIVATE'], argd['ln'])
            redirect_to_url(req, url)
        else:
            body = perform_request_edit_topic(uid=uid,
                                              topic=argd['topic'],
                                              ln=argd['ln'])

        navtrail = '<a class="navtrail" href="%s/youraccount/display?ln=%s">'\
                   '%s</a>'
        navtrail %= (CFG_SITE_SECURE_URL, argd['ln'], _("Your Account"))
        navtrail_end = ""
        #navtrail_end = create_basket_navtrail(
        #                    uid=uid,
        #                    category=CFG_WEBBASKET_CATEGORIES['PRIVATE'],
        #                    topic=argd['topic'],
        #                    group=0,
        #                    ln=argd['ln'])
        if isGuestUser(uid):
            body = create_guest_warning_box(argd['ln']) + body

        # register event in webstat
        #basket_str = "%s (%d)" % (get_basket_name(argd['bskid']), argd['bskid'])
        #if user_info['email']:
        #    user_str = "%s (%d)" % (user_info['email'], user_info['uid'])
        #else:
        #    user_str = ""
        #try:
        #    register_customevent("baskets", ["edit", basket_str, user_str])
        #except:
        #    register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

        return page(title       = _("Edit topic"),
                    body        = body,
                    navtrail    = navtrail + navtrail_end,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    req         = req,
                    navmenuid   = 'yourbaskets',
                    of          = argd['of'],
                    secure_page_p=1)

    def create_basket(self, req, form):
        """Create basket interface"""

        argd = wash_urlargd(form, {'new_basket_name': (str, ""),
                                   'new_topic_name' : (str, ""),
                                   'create_in_topic': (str, "-1"),
                                   'topic'          : (str, ""),
                                   'recid'          : (list, []),
                                   'colid'          : (int, -1),
                                   'es_title'       : (str, ''),
                                   'es_desc'        : (str, ''),
                                   'es_url'         : (str, ''),
                                   'of'             : (str, ''),
                                   'ln'             : (str, CFG_SITE_LANG)})

        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../yourbaskets/create_basket",
                                       navmenuid = 'yourbaskets')

        if isGuestUser(uid):
            if not CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS:
                return redirect_to_url(req, "%s/youraccount/login%s" % (
                    CFG_SITE_SECURE_URL,
                        make_canonical_urlargd({
                    'referer' : "%s/yourbaskets/create_basket%s" % (
                        CFG_SITE_SECURE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        user_info = collect_user_info(req)
        _ = gettext_set_language(argd['ln'])
        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))

        if argd['new_basket_name'] and \
                (argd['new_topic_name'] or argd['create_in_topic'] != "-1"):
            (bskid, topic) = perform_request_create_basket(
                                req,
                                uid=uid,
                                new_basket_name=argd['new_basket_name'],
                                new_topic_name=argd['new_topic_name'],
                                create_in_topic=argd['create_in_topic'],
                                recids=argd['recid'],
                                colid=argd['colid'],
                                es_title=argd['es_title'],
                                es_desc=argd['es_desc'],
                                es_url=argd['es_url'],
                                ln=argd['ln'])

            # register event in webstat
            basket_str = "%s ()" % argd['new_basket_name']
            if user_info['email']:
                user_str = "%s (%d)" % (user_info['email'], user_info['uid'])
            else:
                user_str = ""
            try:
                register_customevent("baskets", ["create_basket", basket_str, user_str])
            except:
                register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

            if ( argd['recid'] and argd['colid'] >= 0 ):
                url = CFG_SITE_SECURE_URL + '/yourbaskets/add?category=%s&bskid=%i&colid=%i&recid=%s&wait=1&ln=%s'
                url %= (CFG_WEBBASKET_CATEGORIES['PRIVATE'],
                        bskid,
                        argd['colid'],
                        '&recid='.join(str(recid) for recid in argd['recid']),
                        argd['ln'])
            elif ( argd['es_title'] and argd['es_desc'] and argd['es_url'] and argd['colid'] == -1 ):
                url = CFG_SITE_SECURE_URL + '/yourbaskets/add?category=%s&bskid=%i&colid=%i&es_title=%s&es_desc=%s&es_url=%s&wait=1&ln=%s'
                url %= (CFG_WEBBASKET_CATEGORIES['PRIVATE'],
                        bskid,
                        argd['colid'],
                        urllib.quote(argd['es_title']),
                        urllib.quote(argd['es_desc']),
                        urllib.quote(argd['es_url']),
                        argd['ln'])
            else:
                url = CFG_SITE_SECURE_URL + '/yourbaskets/display?category=%s&topic=%s&ln=%s'
                url %= (CFG_WEBBASKET_CATEGORIES['PRIVATE'],
                        urllib.quote(topic),
                        argd['ln'])
            redirect_to_url(req, url)
        else:
            body = perform_request_create_basket(req,
                                                 uid=uid,
                                                 new_basket_name=argd['new_basket_name'],
                                                 new_topic_name=argd['new_topic_name'],
                                                 create_in_topic=argd['create_in_topic'],
                                                 topic=argd['topic'],
                                                 recids=argd['recid'],
                                                 colid=argd['colid'],
                                                 es_title=argd['es_title'],
                                                 es_desc=argd['es_desc'],
                                                 es_url=argd['es_url'],
                                                 ln=argd['ln'])
            navtrail = '<a class="navtrail" href="%s/youraccount/'\
                       'display?ln=%s">%s</a>'
            navtrail %= (CFG_SITE_SECURE_URL, argd['ln'], _("Your Account"))
            if isGuestUser(uid):
                body = create_guest_warning_box(argd['ln']) + body
            return page(title = _("Create basket"),
                        body        = body,
                        navtrail    = navtrail,
                        uid         = uid,
                        lastupdated = __lastupdated__,
                        language    = argd['ln'],
                        req         = req,
                        navmenuid   = 'yourbaskets',
                        of          = argd['of'],
                        secure_page_p=1)

    def display_public(self, req, form):
        """Display a public basket"""

        argd = wash_urlargd(form, {'bskid': (int, 0),
                                   'recid': (int, 0),
                                   'of': (str, "hb"),
                                   'ln': (str, CFG_SITE_LANG)})

        _ = gettext_set_language(argd['ln'])

        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../yourbaskets/display",
                                       navmenuid = 'yourbaskets')

        user_info = collect_user_info(req)

        if not argd['bskid']:
            (body, navtrail) = perform_request_list_public_baskets(uid)
            title = _('List of public baskets')

            # register event in webstat
            if user_info['email']:
                user_str = "%s (%d)" % (user_info['email'], user_info['uid'])
            else:
                user_str = ""
            try:
                register_customevent("baskets", ["list_public_baskets", "", user_str])
            except:
                register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

        else:
            (body, dummy, navtrail) = perform_request_display_public(uid=uid,
                                                                  selected_bskid=argd['bskid'],
                                                                  selected_recid=argd['recid'],
                                                                  of=argd['of'],
                                                                  ln=argd['ln'])
            title = _('Public basket')

            # register event in webstat
            basket_str = "%s (%d)" % (get_basket_name(argd['bskid']), argd['bskid'])
            if user_info['email']:
                user_str = "%s (%d)" % (user_info['email'], user_info['uid'])
            else:
                user_str = ""
            try:
                register_customevent("baskets", ["display_public", basket_str, user_str])
            except:
                register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

        rssurl = CFG_SITE_SECURE_URL + "/rss"

        if argd['of'] != 'hb':
            page_start(req, of=argd['of'])

            if argd['of'].startswith('x'):
                req.write(body)
                page_end(req, of=argd['of'])
                return
        elif argd['bskid']:
            rssurl = "%s/yourbaskets/display_public?&amp;bskid=%i&amp;of=xr" % \
                     (CFG_SITE_SECURE_URL,
                      argd['bskid'])

        return page(title       = title,
                    body        = body,
                    navtrail    = navtrail,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    req         = req,
                    navmenuid   = 'yourbaskets',
                    of          = argd['of'],
                    navtrail_append_title_p = 0,
                    secure_page_p=1,
                    rssurl=rssurl)

    def list_public_baskets(self, req, form):
        """List of public baskets interface."""

        argd = wash_urlargd(form, {'limit': (int, 1),
                                   'sort': (str, 'name'),
                                   'asc': (int, 1),
                                   'of': (str, ''),
                                   'ln': (str, CFG_SITE_LANG)})

        _ = gettext_set_language(argd['ln'])

        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE == 2:
            return page_not_authorized(req, "../yourbaskets/list_public_baskets",
                                       navmenuid = 'yourbaskets')

        user_info = collect_user_info(req)
        nb_views_show = acc_authorize_action(user_info, 'runwebstatadmin')
        nb_views_show_p = not(nb_views_show[0])

        (body, navtrail) = perform_request_list_public_baskets(uid,
                                                               argd['limit'],
                                                               argd['sort'],
                                                               argd['asc'],
                                                               nb_views_show_p,
                                                               argd['ln'])

        return page(title = _("List of public baskets"),
                    body        = body,
                    navtrail    = navtrail,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    req         = req,
                    navmenuid   = 'yourbaskets',
                    of          = argd['of'],
                    navtrail_append_title_p = 0,
                    secure_page_p=1)

    def subscribe(self, req, form):
        """Subscribe to a basket pseudo-interface."""

        argd = wash_urlargd(form, {'bskid': (int, 0),
                                   'of': (str, 'hb'),
                                   'ln': (str, CFG_SITE_LANG)})

        _ = gettext_set_language(argd['ln'])

        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE == 2:
            return page_not_authorized(req, "../yourbaskets/subscribe",
                                       navmenuid = 'yourbaskets')

        if isGuestUser(uid):
            if not CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS:
                return redirect_to_url(req, "%s/youraccount/login%s" % (
                    CFG_SITE_SECURE_URL,
                        make_canonical_urlargd({
                    'referer' : "%s/yourbaskets/subscribe%s" % (
                        CFG_SITE_SECURE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        user_info = collect_user_info(req)
        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))

        if not argd['bskid']:
            (body, navtrail) = perform_request_list_public_baskets(uid)
            title = _('List of public baskets')

        else:
            # TODO: Take care of XML output as shown below
            #req.content_type = "text/xml"
            #req.send_http_header()
            #return perform_request_display_public(bskid=argd['bskid'], of=argd['of'], ln=argd['ln'])
            subscribe_warnings_html = perform_request_subscribe(uid, argd['bskid'], argd['ln'])
            (body, dummy, navtrail) = perform_request_display_public(uid=uid,
                                                               selected_bskid=argd['bskid'],
                                                               selected_recid=0,
                                                               of=argd['of'],
                                                               ln=argd['ln'])
            #warnings.extend(subscribe_warnings)
            body = subscribe_warnings_html + body
            title = _('Public basket')

        return page(title       = title,
                    body        = body,
                    navtrail    = navtrail,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    req         = req,
                    navmenuid   = 'yourbaskets',
                    of          = argd['of'],
                    navtrail_append_title_p = 0,
                    secure_page_p=1)

    def unsubscribe(self, req, form):
        """Unsubscribe from basket pseudo-interface."""

        argd = wash_urlargd(form, {'bskid': (int, 0),
                                   'of': (str, 'hb'),
                                   'ln': (str, CFG_SITE_LANG)})

        _ = gettext_set_language(argd['ln'])

        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE == 2:
            return page_not_authorized(req, "../yourbaskets/unsubscribe",
                                       navmenuid = 'yourbaskets')

        if isGuestUser(uid):
            if not CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS:
                return redirect_to_url(req, "%s/youraccount/login%s" % (
                    CFG_SITE_SECURE_URL,
                        make_canonical_urlargd({
                    'referer' : "%s/yourbaskets/unsubscribe%s" % (
                        CFG_SITE_SECURE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        user_info = collect_user_info(req)
        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))

        if not argd['bskid']:
            (body, navtrail) = perform_request_list_public_baskets(uid)
            title = _('List of public baskets')

        else:
            # TODO: Take care of XML output as shown below
            #req.content_type = "text/xml"
            #req.send_http_header()
            #return perform_request_display_public(bskid=argd['bskid'], of=argd['of'], ln=argd['ln'])
            unsubscribe_warnings_html = perform_request_unsubscribe(uid, argd['bskid'], argd['ln'])
            (body, dummy, navtrail) = perform_request_display_public(uid=uid,
                                                              selected_bskid=argd['bskid'],
                                                              selected_recid=0,
                                                              of=argd['of'],
                                                              ln=argd['ln'])
           # warnings.extend(unsubscribe_warnings)
            body = unsubscribe_warnings_html + body
            title = _('Public basket')

        return page(title       = title,
                    body        = body,
                    navtrail    = navtrail,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    req         = req,
                    navmenuid   = 'yourbaskets',
                    of          = argd['of'],
                    navtrail_append_title_p = 0,
                    secure_page_p=1)

    def write_public_note(self, req, form):
        """Write a comment (just interface for writing)"""

        argd = wash_urlargd(form, {'bskid': (int, 0),
                                   'recid': (int, 0),
                                   'cmtid': (int, 0),
                                   'of'   : (str, ''),
                                   'ln'   : (str, CFG_SITE_LANG)})

        _ = gettext_set_language(argd['ln'])

        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../yourbaskets/write_public_note",
                                       navmenuid = 'yourbaskets')

        if isGuestUser(uid):
            if not CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS:
                return redirect_to_url(req, "%s/youraccount/login%s" % (
                    CFG_SITE_SECURE_URL,
                        make_canonical_urlargd({
                    'referer' : "%s/yourbaskets/write_public_note%s" % (
                        CFG_SITE_SECURE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        user_info = collect_user_info(req)
        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))

        (body, navtrail) = perform_request_write_public_note(uid=uid,
                                                            bskid=argd['bskid'],
                                                            recid=argd['recid'],
                                                            cmtid=argd['cmtid'],
                                                            ln=argd['ln'])

        # register event in webstat
        basket_str = "%s (%d)" % (get_basket_name(argd['bskid']), argd['bskid'])
        if user_info['email']:
            user_str = "%s (%d)" % (user_info['email'], user_info['uid'])
        else:
            user_str = ""
        try:
            register_customevent("baskets", ["write_public_note", basket_str, user_str])
        except:
            register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

        return page(title       = _("Add a note"),
                    body        = body,
                    navtrail    = navtrail,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    req         = req,
                    navmenuid   = 'yourbaskets',
                    of          = argd['of'],
                    secure_page_p=1)

    def save_public_note(self, req, form):
        """Save comment on record in basket"""

        argd = wash_urlargd(form, {'bskid': (int, 0),
                                   'recid': (int, 0),
                                   'note_title': (str, ""),
                                   'note_body': (str, ""),
                                   'editor_type': (str, ""),
                                   'of': (str, ''),
                                   'ln': (str, CFG_SITE_LANG),
                                   'reply_to': (str, 0)})

        _ = gettext_set_language(argd['ln'])

        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../yourbaskets/save_public_note",
                                       navmenuid = 'yourbaskets')

        if isGuestUser(uid):
            if not CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS:
                return redirect_to_url(req, "%s/youraccount/login%s" % (
                    CFG_SITE_SECURE_URL,
                        make_canonical_urlargd({
                    'referer' : "%s/yourbaskets/save_public_note%s" % (
                        CFG_SITE_SECURE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        user_info = collect_user_info(req)
        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))

        (body, navtrail) = perform_request_save_public_note(uid=uid,
                                                                      bskid=argd['bskid'],
                                                                      recid=argd['recid'],
                                                                      note_title=argd['note_title'],
                                                                      note_body=argd['note_body'],
                                                                      editor_type=argd['editor_type'],
                                                                      ln=argd['ln'],
                                                                      reply_to=argd['reply_to'])

        # TODO: do not stat event if save was not succussful
        # register event in webstat
        basket_str = "%s (%d)" % (get_basket_name(argd['bskid']), argd['bskid'])
        if user_info['email']:
            user_str = "%s (%d)" % (user_info['email'], user_info['uid'])
        else:
            user_str = ""
        try:
            register_customevent("baskets", ["save_public_note", basket_str, user_str])
        except:
            register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

        return page(title       = _("Display item and notes"),
                    body        = body,
                    navtrail    = navtrail,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    req         = req,
                    navmenuid   = 'yourbaskets',
                    of          = argd['of'],
                    navtrail_append_title_p = 0,
                    secure_page_p=1)
