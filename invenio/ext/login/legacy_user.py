# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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
    Legacy UserInfo object.
"""

from flask import session, request, has_request_context, current_app
from flask.ext.login import UserMixin
from werkzeug.datastructures import CallbackDict, CombinedMultiDict

from invenio.ext.cache import cache


__all__ = ['UserInfo']

CFG_USER_DEFAULT_INFO = {
    'remote_ip': '',
    'remote_host': '',
    'referer': '',
    'uri': '',
    'agent': '',
    'uid': -1,
    'nickname': '',
    'email': '',
    'group': [],
    'guest': '1',
    'session': None,
    'precached_permitted_restricted_collections': [],
    'precached_usebaskets': False,
    'precached_useloans': False,
    'precached_usegroups': False,
    'precached_usealerts': False,
    'precached_usemessages': False,
    'precached_viewsubmissions': False,
    'precached_useapprove': False,
    'precached_useadmin': False,
    'precached_usestats': False,
    'precached_viewclaimlink': False,
    'precached_usepaperclaim': False,
    'precached_usepaperattribution': False,
    'precached_canseehiddenmarctags': False,
    'precached_sendcomments': False,
}


class UserInfo(CombinedMultiDict, UserMixin):
    """
    This provides legacy implementations for the methods that Flask-Login
    and Invenio 1.x expects user objects to have.
    """

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
        CombinedMultiDict.__init__(self, [self.req, self.info, acc,
                                          dict(CFG_USER_DEFAULT_INFO)])
        self.save()

    def get_key(self):
        """ Generates key for caching user information. """
        key = 'current_user::' + str(self.uid)
        return key

    def get_acc_key(self):
        """ Generates key for caching autorizations. """
        remote_ip = str(request.remote_addr) if has_request_context() else '0'
        return 'current_user::' + str(self.uid) + '::' + remote_ip

    def save(self):
        """
        Saves modified data pernamently for logged users.
        """
        if not self.is_guest and self.modified:
            timeout = current_app.config.get(
                'CFG_WEBSESSION_EXPIRY_LIMIT_DEFAULT', 0)*3600
            cache.set(self.get_key(), dict(self.info),
                      timeout=timeout)

    def reload(self):
        """
        Reloads user login information and saves them.
        """
        data = self._login(self.uid, force=True)
        acc = self._precache(data, force=True)
        self.info.update(data)
        CombinedMultiDict.__init__(self, [self.req, self.info, acc,
                                          dict(CFG_USER_DEFAULT_INFO)])
        self.save()

    def update_request_info(self):
        self.req = self._get_request_info()

    def _get_request_info(self):
        """
        Get request information.
        """

        #FIXME: we should support IPV6 too. (hint for FireRole)
        data = {}
        if has_request_context():
            data['remote_ip'] = request.remote_addr or ''
            data['remote_host'] = request.environ.get('REMOTE_HOST', '')
            data['referer'] = request.referrer
            data['uri'] = request.environ['PATH_INFO'] or ''
            data['agent'] = request.headers.get('User-Agent', 'N/A')
            #data['session'] = session.sid
        return data

    def _create_guest(self):
        data = {'settings': {}}

        if current_app.config.get('CFG_WEBSESSION_DIFFERENTIATE_BETWEEN_GUESTS', False):
            from invenio.ext.sqlalchemy import db
            from invenio.modules.accounts.models import User
            note = '1' if current_app.config.get('CFG_ACCESS_CONTROL_LEVEL_GUESTS', 0) == 0 else '0'
            u = User(email='', note=note, password='guest')
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

        from invenio.modules.accounts.models import User
        data = {}

        try:
            user = User.query.get(uid)
            data['id'] = data['uid'] = user.id or -1
            data['nickname'] = user.nickname or ''
            data['email'] = user.email or ''
            data['note'] = user.note or ''
            data.update(user.settings or {})
            data['settings'] = user.settings or {}
            data['guest'] = str(int(user.guest))  # '1' or '0'
            self.modified = True
        except:
            data = self._create_guest()

        return data

    def _precache(self, info, force=False):
        """
        Calculate prermitions for user actions.

        FIXME: compatibility layer only !!!
        """

        CFG_BIBAUTHORID_ENABLED = current_app.config.get(
            'CFG_BIBAUTHORID_ENABLED', False)
        # get autorization key
        acc_key = self.get_acc_key()
        acc = cache.get(acc_key)
        if not force and acc_key is not None and acc is not None:
            return acc

        #FIXME: acc_authorize_action should use flask request directly
        user_info = info
        user_info.update(self.req)

        from invenio.legacy.webuser import isUserSubmitter, isUserReferee, \
            isUserAdmin, isUserSuperAdmin
        from invenio.modules.access.engine import acc_authorize_action
        from invenio.modules.access.control import acc_get_role_id, \
            acc_is_user_in_role
        from invenio.legacy.search_engine import get_permitted_restricted_collections

        data = {}
        data['precached_permitted_restricted_collections'] = \
            get_permitted_restricted_collections(user_info)
        data['precached_usebaskets'] = acc_authorize_action(
            user_info, 'usebaskets')[0] == 0
        data['precached_useloans'] = acc_authorize_action(
            user_info, 'useloans')[0] == 0
        data['precached_usegroups'] = acc_authorize_action(
            user_info, 'usegroups')[0] == 0
        data['precached_usealerts'] = acc_authorize_action(
            user_info, 'usealerts')[0] == 0
        data['precached_usemessages'] = acc_authorize_action(
            user_info, 'usemessages')[0] == 0
        data['precached_usestats'] = acc_authorize_action(
            user_info, 'runwebstatadmin')[0] == 0
        try:
            data['precached_viewsubmissions'] = isUserSubmitter(user_info)
        except:
            data['precached_viewsubmissions'] = None
        data['precached_useapprove'] = isUserReferee(user_info)
        data['precached_useadmin'] = isUserAdmin(user_info)
        data['precached_usesuperadmin'] = isUserSuperAdmin(user_info)
        data['precached_canseehiddenmarctags'] = acc_authorize_action(
            user_info, 'runbibedit')[0] == 0
        usepaperclaim = False
        usepaperattribution = False
        viewclaimlink = False

        if (CFG_BIBAUTHORID_ENABLED and acc_is_user_in_role(
                user_info, acc_get_role_id("paperclaimviewers"))):
            usepaperclaim = True

        if (CFG_BIBAUTHORID_ENABLED and acc_is_user_in_role(
                user_info, acc_get_role_id("paperattributionviewers"))):
            usepaperattribution = True

        viewlink = False
        try:
            viewlink = session['personinfo']['claim_in_process']
        except (KeyError, TypeError):
            pass

        if (current_app.config.get('CFG_BIBAUTHORID_ENABLED') and usepaperattribution and viewlink):
            viewclaimlink = True

#       if (CFG_BIBAUTHORID_ENABLED
#               and ((usepaperclaim or usepaperattribution)
#               and acc_is_user_in_role(
#                   data, acc_get_role_id("paperattributionlinkviewers")))):
#           viewclaimlink = True

        data['precached_viewclaimlink'] = viewclaimlink
        data['precached_usepaperclaim'] = usepaperclaim
        data['precached_usepaperattribution'] = usepaperattribution

        timeout = current_app.config.get(
            'CFG_WEBSESSION_EXPIRY_LIMIT_DEFAULT', 0)*3600
        cache.set(acc_key, data,
                  timeout=timeout)
        return data

    def is_authenticated(self):
        return not self.is_guest

    def is_authorized(self, name, **kwargs):
        from invenio.modules.access.engine import acc_authorize_action
        return acc_authorize_action(self, name)[0] == 0

    def is_active(self):
        return not self.is_guest

    @property
    def is_guest(self):
        return True if self['email'] == '' else False

    @property
    def is_admin(self):
        return self.get('precached_useadmin', False)

    @property
    def is_super_admin(self):
        return self.get('precached_usesuperadmin', False)

    def get_id(self):
        return self.get('id', -1)
