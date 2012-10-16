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
     CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS, \
     CFG_CERN_SITE, \
     CFG_INSPIRE_SITE, \
     CFG_BIBAUTHORID_ENABLED, \
     CFG_SITE_RECORD

from invenio.messages import gettext_set_language, wash_languages, wash_language
from invenio.mailutils import send_email
from invenio.errorlib import register_exception
from invenio.external_authentication import InvenioWebAccessExternalAuthError
from invenio.access_control_config import CFG_EXTERNAL_AUTHENTICATION, \
    CFG_WEBACCESS_MSGS, CFG_WEBACCESS_WARNING_MSGS, CFG_EXTERNAL_AUTH_DEFAULT

from functools import wraps
#from invenio.webinterface_handler_flask_utils import _
from werkzeug.local import LocalProxy
from flask import current_app, session, _request_ctx_stack, redirect, url_for,\
                  request, flash, abort



class GuestUser(dict):
    """
    This is the default object for representing an guest user.
    """
    def __init__(self, login_time=False, refresh=False):
        """
        Create user information dictionary from current session or gather them
        based on `session.uid`.
        """

        # set default values
        self.update({
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
        })

        if 'user_info' in session:
            self.update(session['user_info'])
        else:
            self.reload(update_session=False)
        # Always refresh when creating itself.
        self.refresh()

    def _login(self):
        """
        Get account information for logged user.
        """
        if CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS:
            self._create_guest()
        else:
            # Minimal information about user.
            self['id'] = self['uid'] = 0
            self['email'] = ''
            self['guest'] = '1'

    def _create_guest(self):
        from invenio.sqlalchemyutils import db
        from invenio.websession_model import User
        note = '1' if CFG_ACCESS_CONTROL_LEVEL_GUESTS == 0 else '0'
        u = User(email = '', note = note, password='guest')
        db.session.add(u)
        db.session.commit()
        self.update(u.__dict__)

    def refresh(self, update_session=True):
        """
        Refresh request information.
        """
        current_app.logger.info("Refresh UserInfo ...")
        #FIXME: we should support IPV6 too. (hint for FireRole)
        self['remote_ip'] = request.remote_addr or ''
        self['remote_host'] = request.environ.get('REMOTE_HOST', '')
        self['referer'] = request.referrer
        self['uri'] = request.url or ''
        self['agent'] = request.user_agent or 'N/A'
        self['session'] = session.sid
        if update_session:
            session['user_info'] = dict(self)

    def reload(self, update_session=True):
        """
        Reload user information and precached access list.
        """
        self._login()
        if update_session:
            session['user_info'] = dict(self)

    def is_authenticated(self):
        return not self.is_guest()

    def is_authorized(self, name, **kwargs):
        from invenio.access_control_engine import acc_authorize_action
        return acc_authorize_action(self, name)[0] == 0

    def is_active(self):
        return not self.is_guest()

    def is_guest(self):
        return True if self['email']=='' else False

    def get_id(self):
        try:
            return self['id']
        except:
            return None


class UserInfo(GuestUser):

    def _login(self):
        """
        Get account information about currently logged user from database.

        Should raise an exception when session.uid is not valid User.id.
        """
        current_app.logger.info("Login UserInfo ...")
        from invenio.websession_model import User

        try:
            user = User.query.get(session.uid)
        except:
            user = None

        if user is None:
            self.__class__ = GuestUser
            return
        self['id'] = self['uid'] = user.id or None
        self['nickname'] = user.nickname or ''
        self['email'] = user.email or ''
        self['note'] = user.note or ''
        self.update(user.settings or {})
        self.settings = user.settings or {}
        self['guest'] = str(int(user.guest)) # '1' or '0'
        current_app.logger.info(dict(self))
        self._precache()

    def _precache(self):
        """
        Calculate prermitions for user actions.
        """
        from invenio.webuser import isUserSubmitter, isUserReferee, isUserAdmin
        from invenio.access_control_engine import acc_authorize_action
        from invenio.access_control_admin import acc_get_role_id, acc_get_action_roles, acc_get_action_id, acc_is_user_in_role, acc_find_possible_activities
        from invenio.search_engine import get_permitted_restricted_collections
        self['precached_permitted_restricted_collections'] = \
            get_permitted_restricted_collections(self)
        self['precached_usebaskets'] = acc_authorize_action(self, 'usebaskets')[0] == 0
        self['precached_useloans'] = acc_authorize_action(self, 'useloans')[0] == 0
        self['precached_usegroups'] = acc_authorize_action(self, 'usegroups')[0] == 0
        self['precached_usealerts'] = acc_authorize_action(self, 'usealerts')[0] == 0
        self['precached_usemessages'] = acc_authorize_action(self, 'usemessages')[0] == 0
        self['precached_usestats'] = acc_authorize_action(self, 'runwebstatadmin')[0] == 0
        self['precached_viewsubmissions'] = isUserSubmitter(self)
        self['precached_useapprove'] = isUserReferee(self)
        self['precached_useadmin'] = isUserAdmin(self)
        self['precached_canseehiddenmarctags'] = acc_authorize_action(self, 'runbibedit')[0] == 0
        usepaperclaim = False
        usepaperattribution = False
        viewclaimlink = False

        if (CFG_BIBAUTHORID_ENABLED
            and acc_is_user_in_role(self, acc_get_role_id("paperclaimviewers"))):
            usepaperclaim = True

        if (CFG_BIBAUTHORID_ENABLED
            and acc_is_user_in_role(self, acc_get_role_id("paperattributionviewers"))):
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
#                         and acc_is_user_in_role(self, acc_get_role_id("paperattributionlinkviewers")))):
#                    viewclaimlink = True

        self['precached_viewclaimlink'] = viewclaimlink
        self['precached_usepaperclaim'] = usepaperclaim
        self['precached_usepaperattribution'] = usepaperattribution



KEY_USER_ID = '_uid'

class InvenioLoginManager(object):

    def __init__(self):
        self.key_user_id = KEY_USER_ID
        self.guest_user = GuestUser
        self.login_view = None
        self.user_callback = None
        self.unauthorized_callback = None

    def user_loader(self, callback):
        self.user_callback = callback

    def setup_app(self, app):
        app.login_manager = self
        app.before_request(self._load_user)
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
        current_app.logger.info("loading user: %s" % str(uid))
        if uid is None:
            ctx.user = self.guest_user()
        else:
            user = self.user_callback(uid)
            if user is None:
                logout_user()
            else:
                ctx.user = user
        #ctx.user.reload(update_session=True)

# A proxy for current user
current_user = LocalProxy(lambda: _request_ctx_stack.top.user)

def login_user(user, remember=False, force=False):
    if (not force) and (not user.is_active()):
        return False

    uid = user.get_id()
    current_app.logger.info("logging user %d" % uid)
    #session[KEY_USER_ID] = uid
    session.uid = uid
    current_app.login_manager.reload_user()
    return True


def logout_user():
    session.delete()
    session[current_app.login_manager.key_user_id] = None
    current_app.login_manager.reload_user()
    return True


def login_required(fn):
    @wraps(fn)
    def decorated_view(*args, **kwargs):
        current_app.logger.info(current_user.get_id())
        if not current_user.is_authenticated():
            return current_app.login_manager.unauthorized()
        return fn(*args, **kwargs)
    return decorated_view

