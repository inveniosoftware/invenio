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

"""WebBasket Web Interface."""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""
from invenio import webinterface_handler_wsgi_utils as apache

import os
from invenio.config import CFG_SITE_URL, \
                           CFG_ACCESS_CONTROL_LEVEL_SITE, \
                           CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS, \
                           CFG_SITE_SECURE_URL, CFG_PREFIX
from invenio.messages import gettext_set_language
from invenio.webpage import page
from invenio.webuser import getUid, page_not_authorized, isGuestUser
from invenio.webbasket import \
     check_user_can_comment, \
     check_sufficient_rights, \
     perform_request_display, \
     create_guest_warning_box, \
     create_basket_navtrail, \
     perform_request_display_item, \
     create_guest_warning_box, \
     perform_request_write_comment, \
     perform_request_save_comment, \
     perform_request_delete_comment, \
     perform_request_add_group, \
     perform_request_edit, \
     perform_request_list_public_baskets, \
     perform_request_unsubscribe, \
     perform_request_subscribe, \
     create_infobox, \
     perform_request_display_public, \
     delete_record, \
     move_record, \
     perform_request_add, \
     perform_request_create_basket, \
     perform_request_delete
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
try:
    from invenio.fckeditor_invenio_connector import FCKeditorConnectorInvenio
    fckeditor_available = True
except ImportError, e:
    fckeditor_available = False
from invenio.bibdocfile import stream_file

class WebInterfaceBasketCommentsFiles(WebInterfaceDirectory):
    """Handle upload and access to files for comments in WebBasket.

       The upload is currently only available through the FCKeditor.
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
                                 # defined by FCKeditor)

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
        CFG_SITE_URL/yourbaskets/attachments/get/31/91/5/file/myfile.pdf
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
        uid = getUid(req)
        user_info = collect_user_info(req)
        rights = get_max_user_rights_on_basket(argd['uid'], argd['bskid'])

        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))

        if user_info['email'] == 'guest' and not user_info['apache_user']:
            # Ask to login
            target = '/youraccount/login' + \
                     make_canonical_urlargd({'ln' : argd['ln'], 'referer' : \
                                             CFG_SITE_URL + user_info['uri']}, {})
            return redirect_to_url(req, target)

        elif not(check_sufficient_rights(rights, CFG_WEBBASKET_SHARE_LEVELS['READITM'])):
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to view this attachment"))

        if not argd['file'] is None:
            # Prepare path to file on disk. Normalize the path so that
            # ../ and other dangerous components are removed.
            path = os.path.abspath('/opt/cds-invenio/var/data/baskets/comments/' + \
                                   str(argd['bskid']) + '/'  + str(argd['recid']) + '/' + \
                                   str(argd['uid']) + '/' + argd['type'] + '/' + \
                                   argd['file'])

            # Check that we are really accessing attachements
            # directory, for the declared basket and record.
            if path.startswith('/opt/cds-invenio/var/data/baskets/comments/' + \
                               str(argd['bskid']) + '/' + str(argd['recid'])) and \
                               os.path.exists(path):
                return stream_file(req, path)

        # Send error 404 in all other cases
        return(apache.HTTP_NOT_FOUND)

    def _put(self, req, form):
        """
        Process requests received from FCKeditor to upload files, etc.

        URL eg:
        CFG_SITE_URL/yourbaskets/attachments/put/31/91/
                                             bskid/recid/
        """
        if not fckeditor_available:
            return

        argd = wash_urlargd(form, {'bskid': (int, 0),
                                   'recid': (int, 0)})

        uid = getUid(req)

        # URL where the file can be fetched after upload
        user_files_path = '%(CFG_SITE_URL)s/yourbaskets/attachments/get/%(bskid)s/%(recid)i/%(uid)s' % \
                          {'uid': uid,
                           'recid': argd['recid'],
                           'bskid': argd['bskid'],
                           'CFG_SITE_URL': CFG_SITE_URL}
        # Path to directory where uploaded files are saved
        user_files_absolute_path = '%(CFG_PREFIX)s/var/data/baskets/comments/%(bskid)s/%(recid)s/%(uid)s' % \
                                   {'uid': uid,
                                    'recid': argd['recid'],
                                    'bskid': argd['bskid'],
                                    'CFG_PREFIX': CFG_PREFIX}
        # Create a Connector instance to handle the request
        conn = FCKeditorConnectorInvenio(form, recid=argd['recid'], uid=uid,
                                         allowed_commands=['QuickUpload'],
                                         allowed_types = ['File', 'Image', 'Flash', 'Media'],
                                         user_files_path = user_files_path,
                                         user_files_absolute_path = user_files_absolute_path)

        # Check that user can
        # 1. is logged in
        # 2. comment records of this basket (to simplify, we use
        #    WebComment function to check this, even if it is not
        #    entirely adequate)
        # 3. attach files

        user_info = collect_user_info(req)
        (auth_code, auth_msg) = check_user_can_attach_file_to_comments(user_info, argd['recid'])

        if user_info['email'] == 'guest' and not user_info['apache_user']:
            # 1. User is guest: must login prior to upload
            data = conn.sendUploadResults(1, '', '', 'Please login before uploading file.')
        if not user_info['precached_usebaskets']:
            data = conn.sendUploadResults(1, '', '', 'Sorry, you are not allowed to use WebBasket')
        elif not check_user_can_comment(uid, argd['bskid']):
            # 2. User cannot edit comment of this basket
            data = conn.sendUploadResults(1, '', '', 'Sorry, you are not allowed to submit files')
        elif auth_code:
            # 3. User cannot submit
            data = conn.sendUploadResults(1, '', '', 'Sorry, you are not allowed to submit files.')
        else:
            # Process the upload and get the response
            data = conn.doResponse()

        # Transform the headers into something ok for mod_python
        for header in conn.headers:
            if not header is None:
                if header[0] == 'Content-Type':
                    req.content_type = header[1]
                else:
                    req.headers_out[header[0]] = header[1]
        # Send our response
        req.send_http_header()
        req.write(data)


class WebInterfaceYourBasketsPages(WebInterfaceDirectory):
    """Defines the set of /yourbaskets pages."""

    _exports = ['', 'display', 'display_item', 'write_comment',
                'save_comment', 'delete_comment', 'add', 'delete',
                'modify', 'edit', 'create_basket', 'display_public',
                'list_public_baskets', 'unsubscribe', 'subscribe',
                'attachments']

    attachments = WebInterfaceBasketCommentsFiles()

    def index(self, req, form):
        """Index page."""
        redirect_to_url(req, '%s/yourbaskets/display?%s' % (CFG_SITE_URL, req.args))

    def display(self, req, form):
        """Display basket"""

        argd = wash_urlargd(form, {'category':
                                     (str, CFG_WEBBASKET_CATEGORIES['PRIVATE']),
                                   'topic': (int, 0),
                                   'group': (int, 0),
                                   'bsk_to_sort': (int, 0),
                                   'sort_by_title': (str, ""),
                                   'sort_by_date': (str, ""),
                                   'of': (str, '')
                                   })

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
                        CFG_SITE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        user_info = collect_user_info(req)

        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))

        (body, errors, warnings) = perform_request_display(uid,
                                                           argd['category'],
                                                           argd['topic'],
                                                           argd['group'],
                                                           argd['ln'])

        if isGuestUser(uid):
            body = create_guest_warning_box(argd['ln']) + body
        navtrail = '<a class="navtrail" href="%s/youraccount/display?ln=%s">'\
                   '%s</a>'
        navtrail %= (CFG_SITE_URL, argd['ln'], _("Your Account"))
        navtrail_end = create_basket_navtrail(uid=uid,
                                              category=argd['category'],
                                              topic=argd['topic'],
                                              group=argd['group'],
                                              ln=argd['ln'])

        # register event in webstat
        if user_info['email']:
            user_str = "%s (%d)" % (user_info['email'], user_info['uid'])
        else:
            user_str = ""
        try:
            register_customevent("baskets", ["display", "", user_str])
        except:
            register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

        return page(title       = _("Display baskets"),
                    body        = body,
                    navtrail    = navtrail + navtrail_end,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    errors      = errors,
                    warnings    = warnings,
                    req         = req,
                    navmenuid   = 'yourbaskets',
                    of          = argd['of'])

    def display_item(self, req, form):
        """ Display basket item """

        argd = wash_urlargd(form, {'bskid': (int, 0),
                                   'recid': (int, 0),
                                   'format': (str, "hb"),
                                   'category':
                                     (str, CFG_WEBBASKET_CATEGORIES['PRIVATE']),
                                   'topic': (int, 0),
                                   'group': (int, 0),
                                   'of': (str, '')
                                   })

        _ = gettext_set_language(argd['ln'])
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../yourbaskets/display_item",
                                       navmenuid = 'yourbaskets')

        if isGuestUser(uid):
            if not CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS:
                return redirect_to_url(req, "%s/youraccount/login%s" % (
                    CFG_SITE_SECURE_URL,
                        make_canonical_urlargd({
                    'referer' : "%s/yourbaskets/display_item%s" % (
                        CFG_SITE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        user_info = collect_user_info(req)
        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))

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
        navtrail %= (CFG_SITE_URL, argd['ln'], _("Your Account"))
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
            register_customevent("baskets", ["display", basket_str, user_str])
        except:
            register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

        return page(title       = _("Details and comments"),
                    body        = body,
                    navtrail    = navtrail + navtrail_end,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    errors      = errors,
                    warnings    = warnings,
                    req         = req,
                    navmenuid   = 'yourbaskets',
                    of          = argd['of'])

    def write_comment(self, req, form):
        """Write a comment (just interface for writing)"""

        argd = wash_urlargd(form, {'bskid': (int, 0),
                                   'recid': (int, 0),
                                   'cmtid': (int, 0),
                                   'category':
                                     (str, CFG_WEBBASKET_CATEGORIES['PRIVATE']),
                                   'topic': (int, 0),
                                   'group': (int, 0),
                                   'of'   : (str, '')
                                   })

        _ = gettext_set_language(argd['ln'])
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../yourbaskets/write_comment",
                                       navmenuid = 'yourbaskets')

        if isGuestUser(uid):
            if not CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS:
                return redirect_to_url(req, "%s/youraccount/login%s" % (
                    CFG_SITE_SECURE_URL,
                        make_canonical_urlargd({
                    'referer' : "%s/yourbaskets/write_comment%s" % (
                        CFG_SITE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        user_info = collect_user_info(req)
        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))

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
        navtrail %= (CFG_SITE_URL, argd['ln'], _("Your Account"))
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
            register_customevent("baskets", ["write_comment", basket_str, user_str])
        except:
            register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

        return page(title       = _("Write a comment"),
                    body        = body,
                    navtrail    = navtrail + navtrail_end,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    errors      = errors,
                    warnings    = warnings,
                    req         = req,
                    navmenuid   = 'yourbaskets',
                    of          = argd['of'])

    def save_comment(self, req, form):
        """Save comment on record in basket"""

        argd = wash_urlargd(form, {'bskid': (int, 0),
                                   'recid': (int, 0),
                                   'title': (str, ""),
                                   'text': (str, ""),
                                   'category':
                                     (str, CFG_WEBBASKET_CATEGORIES['PRIVATE']),
                                   'topic': (int, 0),
                                   'group': (int, 0),
                                   'of'   : (str, ''),
                                   'editor_type':(str, ""),
                                   })

        _ = gettext_set_language(argd['ln'])
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../yourbaskets/save_comment",
                                       navmenuid = 'yourbaskets')

        if isGuestUser(uid):
            if not CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS:
                return redirect_to_url(req, "%s/youraccount/login%s" % (
                    CFG_SITE_SECURE_URL,
                        make_canonical_urlargd({
                    'referer' : "%s/yourbaskets/save_comment%s" % (
                        CFG_SITE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        user_info = collect_user_info(req)
        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))

        (errors_saving, infos) = perform_request_save_comment(
                                        uid=uid,
                                        bskid=argd['bskid'],
                                        recid=argd['recid'],
                                        title=argd['title'],
                                        text=argd['text'],
                                        ln=argd['ln'],
                                        editor_type=argd['editor_type'])
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
        navtrail %= (CFG_SITE_URL, argd['ln'], _("Your Account"))
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
            register_customevent("baskets", ["save_comment", basket_str, user_str])
        except:
            register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

        return page(title       = _("Details and comments"),
                    body        = body,
                    navtrail    = navtrail + navtrail_end,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    errors      = errors,
                    warnings    = warnings,
                    req         = req,
                    navmenuid   = 'yourbaskets',
                    of          = argd['of'])

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
                                   'group': (int, 0),
                                   'of'   : (str, '')
                                   })

        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../yourbaskets/delete_comment",
                                       navmenuid = 'yourbaskets')

        if isGuestUser(uid):
            if not CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS:
                return redirect_to_url(req, "%s/youraccount/delete_comment%s" % (
                    CFG_SITE_SECURE_URL,
                        make_canonical_urlargd({
                    'referer' : "%s/yourbaskets/display%s" % (
                        CFG_SITE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        _ = gettext_set_language(argd['ln'])

        user_info = collect_user_info(req)
        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))


        url = CFG_SITE_URL + '/yourbaskets/display_item?recid=%i&bskid=%i' % \
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
            # register event in webstat
            basket_str = "%s (%d)" % (get_basket_name(argd['bskid']), argd['bskid'])
            user_info = collect_user_info(req)
            if user_info['email']:
                user_str = "%s (%d)" % (user_info['email'], user_info['uid'])
            else:
                user_str = ""
            try:
                register_customevent("baskets", ["delete_comment", basket_str, user_str])
            except:
                register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

            return page(uid         = uid,
                        title       = '',
                        body        = '',
                        language    = argd['ln'],
                        errors      = errors,
                        req         = req,
                        navmenuid   = 'yourbaskets',
                        of          = argd['of'])

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
                                   "of" : (str, '')
                                   })
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
                        CFG_SITE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        user_info = collect_user_info(req)
        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))

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
        navtrail %= (CFG_SITE_URL, argd['ln'], _("Your Account"))

        # register event in webstat
        basket_str = ["%s (%s)" % (get_basket_name(bskid), bskid) for bskid in argd['bskids']]
        if user_info['email']:
            user_str = "%s (%d)" % (user_info['email'], user_info['uid'])
        else:
            user_str = ""
        try:
            register_customevent("baskets", ["add", basket_str, user_str])
        except:
            register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")

        return page(title       = title,
                    body        = body,
                    navtrail    = navtrail,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    errors      = errors,
                    warnings    = warnings,
                    req         = req,
                    navmenuid   = 'yourbaskets',
                    of          = argd['of'])

    def delete(self, req, form):
        """Delete basket interface"""
        argd = wash_urlargd(form, {'bskid': (int, -1),
                                   'confirmed': (int, 0),
                                   'category':
                                     (str, CFG_WEBBASKET_CATEGORIES['PRIVATE']),
                                   'topic': (int, 0),
                                   'group': (int, 0),
                                   'of'   : (str, '')
                                   })

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
                        CFG_SITE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        user_info = collect_user_info(req)
        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))

        (body, errors, warnings)=perform_request_delete(
                                        uid=uid,
                                        bskid=argd['bskid'],
                                        confirmed=argd['confirmed'],
                                        category=argd['category'],
                                        selected_topic=argd['topic'],
                                        selected_group_id=argd['group'],
                                        ln=argd['ln'])
        if argd['confirmed']:
            url = CFG_SITE_URL
            url += '/yourbaskets/display?category=%s&topic=%i&group=%i&ln=%s' % \
                   (argd['category'], argd['topic'], argd['group'], argd['ln'])
            redirect_to_url(req, url)
        else:
            navtrail = '<a class="navtrail" href="%s/youraccount/display?ln=%s">'\
                       '%s</a>'
            navtrail %= (CFG_SITE_URL, argd['ln'], _("Your Account"))
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
                        errors      = errors,
                        warnings    = warnings,
                        req         = req,
                        navmenuid   = 'yourbaskets',
                        of          = argd['of'])

    def modify(self, req, form):
        """Modify basket content interface (reorder, suppress record, etc.)"""
        argd = wash_urlargd(form, {'action': (str, ""),
                                   'bskid': (int, -1),
                                   'recid': (int, 0),
                                   'category':
                                     (str, CFG_WEBBASKET_CATEGORIES['PRIVATE']),
                                   'topic': (int, 0),
                                   'group': (int, 0),
                                   'of'   : (str, '')
                                   })

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
                        CFG_SITE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        user_info = collect_user_info(req)
        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))

        url = CFG_SITE_URL
        url += '/yourbaskets/display?category=%s&topic=%i&group=%i&ln=%s' % \
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
        navtrail %= (CFG_SITE_URL, argd['ln'], _("Your Account"))
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
                    errors      = errors,
                    warnings    = warnings,
                    req         = req,
                    navmenuid   = 'yourbaskets',
                    of          = argd['of'])

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
                                   'of'      : (str, '')
                                   })

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
                        CFG_SITE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        _ = gettext_set_language(argd['ln'])
        user_info = collect_user_info(req)
        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))

        if argd['cancel']:
            url = CFG_SITE_URL + '/yourbaskets/display?category=%s&topic=%i&ln=%s'
            url %= (CFG_WEBBASKET_CATEGORIES['PRIVATE'], argd['topic'],
                    argd['ln'])
            redirect_to_url(req, url)
        elif argd['delete']:
            url = CFG_SITE_URL
            url += '/yourbaskets/delete?bskid=%i&category=%s&topic=%i&ln=%s' % \
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
            url = CFG_SITE_URL + '/yourbaskets/display?category=%s&topic=%i&ln=%s' % \
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
        navtrail %= (CFG_SITE_URL, argd['ln'], _("Your Account"))
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
                    errors      = errors,
                    warnings    = warnings,
                    req         = req,
                    navmenuid   = 'yourbaskets',
                    of          = argd['of'])

    def create_basket(self, req, form):
        """Create basket interface"""

        argd = wash_urlargd(form, {'new_basket_name': (str, ""),
                                   'new_topic_name': (str, ""),
                                   'create_in_topic': (int, -1),
                                   'topic_number': (int, -1),
                                   'of'          : (str, ''),
                                   })

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
                        CFG_SITE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        user_info = collect_user_info(req)
        _ = gettext_set_language(argd['ln'])
        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))

        if argd['new_basket_name'] and \
                (argd['new_topic_name'] or argd['create_in_topic'] != -1):
            topic = perform_request_create_basket(
                            uid=uid,
                            new_basket_name=argd['new_basket_name'],
                            new_topic_name=argd['new_topic_name'],
                            create_in_topic=argd['create_in_topic'],
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

            url = CFG_SITE_URL + '/yourbaskets/display?category=%s&topic=%i&ln=%s'
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
            navtrail %= (CFG_SITE_URL, argd['ln'], _("Your Account"))
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
                        req         = req,
                        navmenuid   = 'yourbaskets',
                        of          = argd['of'])

    def display_public(self, req, form):
        """Display public basket. If of is x** then output will be XML"""

        argd = wash_urlargd(form, {'bskid': (int, 0),
                                   'of': (str, "hb"),
                                   })

        _ = gettext_set_language(argd['ln'])
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE == 2:
            return page_not_authorized(req, "../yourbaskets/display_public",
                                       navmenuid = 'yourbaskets')

        user_info = collect_user_info(req)
        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))

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
                        req         = req,
                        of          = argd['of'])
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
            referer = CFG_SITE_URL + '/yourbaskets/list_public_baskets?ln=' + \
                                argd['ln']
        navtrail =  '<a class="navtrail" href="%s">%s</a>' % \
                    (referer, _("List of public baskets"))

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

        return page(title = _("Public basket"),
                    body        = body,
                    navtrail    = navtrail,
                    uid         = uid,
                    lastupdated = __lastupdated__,
                    language    = argd['ln'],
                    errors      = errors,
                    warnings    = warnings,
                    req         = req,
                    navmenuid   = 'yourbaskets',
                    of          = argd['of'])

    def list_public_baskets(self, req, form):
        """List of public baskets interface"""
        argd = wash_urlargd(form, {'inf_limit': (int, 0),
                                   'order': (int, 1),
                                   'asc': (int, 1),
                                   'of': (str, '')
                                   })

        if argd['inf_limit'] < 0:
            argd['inf_limit'] = 0
        _ = gettext_set_language(argd['ln'])
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE == 2:
            return page_not_authorized(req, "../yourbaskets/list_public_baskets",
                                       navmenuid = 'yourbaskets')

        user_info = collect_user_info(req)
        ## This is to public to require user to be logged in to visit them...
        #if not user_info['precached_usebaskets']:
            #return page_not_authorized(req, "../", \
                                       #text = _("You are not authorized to use baskets."))

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
                    req         = req,
                    navmenuid   = 'yourbaskets',
                    of          = argd['of'])

    def unsubscribe(self, req, form):
        """unsubscribe to basket"""
        argd = wash_urlargd(form, {'bskid': (int, 0),
                                   'of': (str, '')
                                   })

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
                        CFG_SITE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        _ = gettext_set_language(argd['ln'])
        user_info = collect_user_info(req)
        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))

        perform_request_unsubscribe(uid, argd['bskid'])
        url = CFG_SITE_URL + '/yourbaskets/display?category=%s&ln=%s'
        url %= (CFG_WEBBASKET_CATEGORIES['EXTERNAL'], argd['ln'])
        redirect_to_url(req, url)

    def subscribe(self, req, form):
        """subscribe to basket"""
        argd = wash_urlargd(form, {'bskid': (int, 0),
                                    'of': (str, '')
                                   })
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
                        CFG_SITE_URL,
                        make_canonical_urlargd(argd, {})),
                    "ln" : argd['ln']}, {})))

        _ = gettext_set_language(argd['ln'])
        user_info = collect_user_info(req)
        if not user_info['precached_usebaskets']:
            return page_not_authorized(req, "../", \
                                       text = _("You are not authorized to use baskets."))

        errors = perform_request_subscribe(uid, argd['bskid'])
        if len(errors):
            return page(errors=errors,
                        uid=uid,
                        language=argd['ln'],
                        body = '',
                        title = '',
                        req=req,
                        navmenuid = 'yourbaskets')
        url = CFG_SITE_URL + '/yourbaskets/display?category=%s&ln=%s'
        url %= (CFG_WEBBASKET_CATEGORIES['EXTERNAL'], argd['ln'])
        redirect_to_url(req, url)
