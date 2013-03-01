# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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

"""
Flask-sqlalchemy re-implementation of webuser.
"""
from flask import Request, Flask, logging, session, request, g, url_for, current_app

from invenio.config import \
     CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS, \
     CFG_ACCESS_CONTROL_LEVEL_GUESTS, \
     CFG_ACCESS_CONTROL_LEVEL_SITE, \
     CFG_ACCESS_CONTROL_LIMIT_REGISTRATION_TO_DOMAIN, \
     CFG_ACCESS_CONTROL_NOTIFY_ADMIN_ABOUT_NEW_ACCOUNTS, \
     CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_NEW_ACCOUNT, \
     CFG_SITE_ADMIN_EMAIL, \
     CFG_SITE_LANG, \
     CFG_SITE_NAME, \
     CFG_SITE_NAME_INTL, \
     CFG_SITE_SUPPORT_EMAIL, \
     CFG_SITE_SECURE_URL, \
     CFG_SITE_URL, \
     CFG_WEBSESSION_EXPIRY_LIMIT_DEFAULT, \
     CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS, \
     CFG_CERN_SITE, \
     CFG_INSPIRE_SITE, \
     CFG_BIBAUTHORID_ENABLED, \
     CFG_SITE_RECORD

from invenio.cache import cache
from invenio.messages import gettext_set_language, wash_languages, wash_language
from invenio.mailutils import send_email
from invenio.errorlib import register_exception
from invenio.external_authentication import InvenioWebAccessExternalAuthError
from invenio.access_control_config import CFG_EXTERNAL_AUTHENTICATION, \
    CFG_WEBACCESS_MSGS, CFG_WEBACCESS_WARNING_MSGS, CFG_EXTERNAL_AUTH_DEFAULT

from functools import wraps
#from invenio.webinterface_handler_flask_utils import _
from werkzeug.local import LocalProxy
from werkzeug.datastructures import CallbackDict, CombinedMultiDict
from flask import current_app, session, _request_ctx_stack, redirect, url_for,\
                  request, flash, abort

CFG_USER_DEFAULT_INFO = {
            'remote_ip' : '',
            'remote_host' : '',
            'referer' : '',
            'uri' : '',
            'agent' : '',
            'uid' :-1,
            'nickname' : '',
            'email' : '',
            'group' : [],
            'guest' : '1',
            'session' : None,
            'precached_permitted_restricted_collections' : [],
            'precached_usebaskets' : False,
            'precached_useloans' : False,
            'precached_usegroups' : False,
            'precached_usealerts' : False,
            'precached_usemessages' : False,
            'precached_viewsubmissions' : False,
            'precached_useapprove' : False,
            'precached_useadmin' : False,
            'precached_usestats' : False,
            'precached_viewclaimlink' : False,
            'precached_usepaperclaim' : False,
            'precached_usepaperattribution' : False,
            'precached_canseehiddenmarctags' : False,
            'precached_sendcomments' : False,
            }

class UserInfo(CombinedMultiDict):

    def __init__(self, uid=None, force=False):
        """
        Keeps information about user.
        """
        def on_update(self):
            """ Changes own status when the user info is modified. """
            self.modified = True

        self.modified = False
        self.uid = uid
        self.req = self._get_request_info()
        acc = {}

        if uid > 0:
            data = self._login(uid, force)
            acc = self._precache(data, force)
        else:
            data = self._create_guest()

        self.info = CallbackDict(data, on_update)
        #FIXME remove req after everybody start using flask request.
        CombinedMultiDict.__init__(self, [self.req, self.info, acc, dict(CFG_USER_DEFAULT_INFO)])
        self.save()


    def get_key(self):
        """ Generates key for caching user information. """
        key = 'current_user::' + str(self.uid)
        return key


    def get_acc_key(self):
        """ Generates key for caching autorizations. """
        key = 'current_user::' + str(self.uid) + \
              '::' + str(request.remote_addr)
        return key


    def save(self):
        """
        Saves modified data pernamently for logged users.
        """
        if not self.is_guest and self.modified:
            cache.set(self.get_key(), dict(self.info),
                      timeout=CFG_WEBSESSION_EXPIRY_LIMIT_DEFAULT*3600)

    def reload(self):
        """
        Reloads user login information and saves them.
        """
        data = self._login(self.uid, force=True)
        acc = self._precache(data, force=True)
        self.info.update(data)
        CombinedMultiDict.__init__(self, [self.req, self.info, acc, dict(CFG_USER_DEFAULT_INFO)])
        self.save()

    def update_request_info(self):
        self.req = self._get_request_info()

    def _get_request_info(self):
        """
        Get request information.
        """
        #FIXME: we should support IPV6 too. (hint for FireRole)
        data = {}
        data['remote_ip'] = request.remote_addr or ''
        data['remote_host'] = request.environ.get('REMOTE_HOST', '')
        data['referer'] = request.referrer
        data['uri'] = request.environ['PATH_INFO'] or ''
        data['agent'] = request.user_agent or 'N/A'
        #data['session'] = session.sid
        return data

    def _create_guest(self):
        data = {'settings': {}}

        if CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS:
            from invenio.sqlalchemyutils import db
            from invenio.websession_model import User
            note = '1' if CFG_ACCESS_CONTROL_LEVEL_GUESTS == 0 else '0'
            u = User(email = '', note = note, password='guest')
            db.session.add(u)
            db.session.commit()
            data.update(u.__dict__)
        else:
            # Minimal information about user.
            data['id'] = data['uid'] = 0

        return data


    def _login(self, uid, force=False):
        """
        Get account information about currently logged user from database.

        Should raise an exception when session.uid is not valid User.id.
        """
        data = cache.get(self.get_key())
        if not force and data is not None:
            return data

        from invenio.websession_model import User
        data = {}

        try:
            user = User.query.get(uid)
            data['id'] = data['uid'] = user.id or -1
            data['nickname'] = user.nickname or ''
            data['email'] = user.email or ''
            data['note'] = user.note or ''
            data.update(user.settings or {})
            data['settings'] = user.settings or {}
            data['guest'] = str(int(user.guest)) # '1' or '0'
            self.modified = True
        except:
            data = self._create_guest()

        return data

    def _precache(self, info, force=False):
        """
        Calculate prermitions for user actions.

        FIXME: compatibility layer only !!!
        """
        # get autorization key
        acc_key = self.get_acc_key()
        acc = cache.get(acc_key)
        if not force and acc is not None:
            return acc

        #FIXME: acc_authorize_action should use flask request directly
        user_info = info
        user_info.update(self.req)

        from invenio.webuser import isUserSubmitter, isUserReferee, \
                                    isUserAdmin, isUserSuperAdmin
        from invenio.access_control_engine import acc_authorize_action
        from invenio.access_control_admin import acc_get_role_id, \
                                                 acc_is_user_in_role
        from invenio.search_engine import get_permitted_restricted_collections

        data = {}
        data['precached_permitted_restricted_collections'] = \
            get_permitted_restricted_collections(user_info)
        data['precached_usebaskets'] = acc_authorize_action(user_info, 'usebaskets')[0] == 0
        data['precached_useloans'] = acc_authorize_action(user_info, 'useloans')[0] == 0
        data['precached_usegroups'] = acc_authorize_action(user_info, 'usegroups')[0] == 0
        data['precached_usealerts'] = acc_authorize_action(user_info, 'usealerts')[0] == 0
        data['precached_usemessages'] = acc_authorize_action(user_info, 'usemessages')[0] == 0
        data['precached_usestats'] = acc_authorize_action(user_info, 'runwebstatadmin')[0] == 0
        data['precached_viewsubmissions'] = isUserSubmitter(user_info)
        data['precached_useapprove'] = isUserReferee(user_info)
        data['precached_useadmin'] = isUserAdmin(user_info)
        data['precached_usesuperadmin'] = isUserSuperAdmin(user_info)
        data['precached_canseehiddenmarctags'] = acc_authorize_action(user_info, 'runbibedit')[0] == 0
        usepaperclaim = False
        usepaperattribution = False
        viewclaimlink = False

        if (CFG_BIBAUTHORID_ENABLED
            and acc_is_user_in_role(user_info, acc_get_role_id("paperclaimviewers"))):
            usepaperclaim = True

        if (CFG_BIBAUTHORID_ENABLED
            and acc_is_user_in_role(user_info, acc_get_role_id("paperattributionviewers"))):
            usepaperattribution = True

        viewlink = False
        try:
            viewlink = session['personinfo']['claim_in_process']
        except (KeyError, TypeError):
            pass

        if (CFG_BIBAUTHORID_ENABLED
            and usepaperattribution
            and viewlink):
            viewclaimlink = True

#                if (CFG_BIBAUTHORID_ENABLED
#                    and ((usepaperclaim or usepaperattribution)
#                         and acc_is_user_in_role(data, acc_get_role_id("paperattributionlinkviewers")))):
#                    viewclaimlink = True

        data['precached_viewclaimlink'] = viewclaimlink
        data['precached_usepaperclaim'] = usepaperclaim
        data['precached_usepaperattribution'] = usepaperattribution

        cache.set(acc_key, data,
                  timeout = CFG_WEBSESSION_EXPIRY_LIMIT_DEFAULT*3600)
        return data

    def is_authenticated(self):
        return not self.is_guest

    def is_authorized(self, name, **kwargs):
        from invenio.access_control_engine import acc_authorize_action
        return acc_authorize_action(self, name)[0] == 0

    @property
    def is_active(self):
        return not self.is_guest

    @property
    def is_guest(self):
        return True if self['email']=='' else False

    @property
    def is_admin(self):
        return self.get('precached_useadmin', False)

    @property
    def is_super_admin(self):
        return self.get('precached_usesuperadmin', False)

    def get_id(self):
        return self.get('id', None)



KEY_USER_ID = '_uid'

class InvenioLoginManager(object):

    def __init__(self):
        self.key_user_id = KEY_USER_ID
        self.guest_user = UserInfo
        self.login_view = None
        self.user_callback = None
        self.unauthorized_callback = None

    def user_loader(self, callback):
        self.user_callback = callback

    def setup_app(self, app):
        app.login_manager = self
        app.before_request(self._load_user)
        def save_user(response):
            current_user.save()
            return response
        app.after_request(save_user)
        #app.after_request(self._update_remember_cookie)

    def unauthorized_handler(self, callback):
        self.unauthorized_callback = callback

    def unauthorized(self):
        if self.unauthorized_callback:
            return self.unauthorized_callback()
        if not self.login_view:
            abort(401)
        return redirect(url_for(self.login_view, referer=request.url))

    def _load_user(self):
        #FIXME add remember me
        self.reload_user()

    def reload_user(self):
        ctx = _request_ctx_stack.top
        uid = session.get(self.key_user_id, None)
        if uid is None:
            ctx.user = self.guest_user()
        else:
            user = self.user_callback(uid)
            if user is None:
                logout_user()
            else:
                ctx.user = user
        ctx.user.save() #.reload(update_session=True)

# A proxy for current user
def _request_top_user():
    try:
        return _request_ctx_stack.top.user
    except:
        return UserInfo()

current_user = LocalProxy(_request_top_user)

def login_user(uid, remember_me=False, force=False):
    #FIXME: create user info from uid
    #if not force and not user.is_active:
    #    return False

    session.uid = uid
    session.set_remember_me(remember_me)
    current_app.login_manager.reload_user()
    return True


def logout_user():
    session.uid = None
    current_app.login_manager.reload_user()
    return True


def login_required(fn):
    @wraps(fn)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated():
            return current_app.login_manager.unauthorized()
        return fn(*args, **kwargs)
    return decorated_view

