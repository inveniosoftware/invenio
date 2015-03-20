# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014, 2015 CERN.
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

"""Provide support for legacy UserInfo object."""

from flask import current_app, has_request_context, request, session

from flask_login import UserMixin

from werkzeug.datastructures import CallbackDict, CombinedMultiDict

from invenio.ext.cache import cache

__all__ = ('UserInfo', )

CFG_USER_DEFAULT_INFO = {
    'remote_ip': '',
    'remote_host': '',
    'referer': '',
    'uri': '',
    'agent': '',
    'uid': -1,
    'nickname': '',
    'given_names': '',
    'family_name': '',
    'email': '',
    'group': [],
    'guest': '1',
    'session': None,
    'precached_permitted_restricted_collections': [],
    'precached_allowed_deposition_types': [],
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

    """Provide legacy implementation.

    Methods that Flask-Login and Invenio 1.x expect user objects to have.
    """

    def __init__(self, uid=None, force=False):
        """Retrieve information about user."""
        def on_update(self):
            """Change own status when the user info is modified."""
            self.modified = True

        self.modified = False
        self.uid = uid
        self.req = self._get_request_info()
        acc = {}

        if uid is not None and uid > 0:
            data = self._login(uid, force)
            acc = self._precache(data, force)
        else:
            data = self._create_guest()

        self.info = CallbackDict(data, on_update)
        # FIXME remove req after everybody start using flask request.
        CombinedMultiDict.__init__(self, [self.req, self.info, acc,
                                          dict(CFG_USER_DEFAULT_INFO)])
        self.save()

    def get_key(self):
        """Generate key for caching user information."""
        key = 'current_user::' + str(self.uid)
        return key

    def get_acc_key(self):
        """Generate key for caching authorizations."""
        remote_ip = str(request.remote_addr) if has_request_context() else '0'
        return 'current_user::' + str(self.uid) + '::' + remote_ip

    def save(self):
        """Save modified data permanently for logged users."""
        if not self.is_guest and self.modified:
            timeout = current_app.config.get(
                'CFG_WEBSESSION_EXPIRY_LIMIT_DEFAULT', 0)*3600
            cache.set(self.get_key(), dict(self.info),
                      timeout=timeout)

    def reload(self):
        """Reload user login information and saves them."""
        data = self._login(self.uid, force=True)
        acc = self._precache(data, force=True)
        self.info.update(data)
        CombinedMultiDict.__init__(self, [self.req, self.info, acc,
                                          dict(CFG_USER_DEFAULT_INFO)])
        self.save()

    def update_request_info(self):
        """Update request information."""
        self.req = self._get_request_info()

    def _get_request_info(self):
        """Get request information."""
        # FIXME: we should support IPV6 too. (hint for FireRole)
        data = {}
        if has_request_context():
            data['remote_ip'] = request.remote_addr or ''
            data['remote_host'] = request.environ.get('REMOTE_HOST', '')
            data['referer'] = request.referrer
            data['uri'] = request.environ['PATH_INFO'] or ''
            data['agent'] = request.headers.get('User-Agent', 'N/A')
        return data

    def _create_guest(self):
        # Minimal information about user.
        return {'settings': {}, 'id': 0, 'uid': 0}

    def _login(self, uid, force=False):
        """Get account information about currently logged user from database.

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
            data['given_names'] = user.given_names or ''
            data['family_name'] = user.family_name or ''
            data['email'] = user.email or ''
            data['note'] = user.note or ''
            data['group'] = map(lambda x: x.usergroup.name,
                                user.usergroups or [])
            data.update(user.settings or {})
            data['settings'] = user.settings or {}
            data['guest'] = str(int(user.guest))  # '1' or '0'
            self.modified = True
        except Exception:
            data = self._create_guest()

        return data

    def _precache(self, info, force=False):
        """Calculate permissions for user actions.

        FIXME: compatibility layer only !!!
        """
        CFG_BIBAUTHORID_ENABLED = current_app.config.get(
            'CFG_BIBAUTHORID_ENABLED', False)
        # get authorization key
        acc_key = self.get_acc_key()
        acc = cache.get(acc_key)
        if not force and acc_key is not None and acc is not None:
            return acc

        # FIXME: acc_authorize_action should use flask request directly
        user_info = info
        user_info.update(self.req)

        from invenio.legacy.webuser import isUserSubmitter, isUserReferee, \
            isUserAdmin, isUserSuperAdmin
        from invenio.modules.access.engine import acc_authorize_action
        from invenio.modules.access.control import acc_get_role_id, \
            acc_is_user_in_role
        from invenio.modules.search.utils import \
            get_permitted_restricted_collections
        from invenio.modules.deposit.cache import \
            get_authorized_deposition_types

        data = {}
        data['precached_permitted_restricted_collections'] = \
            get_permitted_restricted_collections(user_info)
        data['precached_allowed_deposition_types'] = \
            get_authorized_deposition_types(user_info)
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
        except Exception:
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

        if (current_app.config.get('CFG_BIBAUTHORID_ENABLED') and
           usepaperattribution and viewlink):
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
        """Check if user is authenticated."""
        return not self.is_guest

    def is_authorized(self, name, **kwargs):
        """Check if user is authorized."""
        from invenio.modules.access.engine import acc_authorize_action
        return acc_authorize_action(self, name)[0] == 0

    def is_active(self):
        """Check if user is active."""
        return not self.is_guest

    def is_confirmed(self):
        """Return true if accounts has been confirmed."""
        return self['note'] == "1"

    @property
    def is_guest(self):
        """Check if user is guest."""
        return True if self['email'] == '' else False

    @property
    def is_admin(self):
        """Check if user is admin."""
        return self.get('precached_useadmin', False)

    @property
    def is_super_admin(self):
        """Check if user is super admin."""
        return self.get('precached_usesuperadmin', False)

    def get_id(self):
        """Get user id."""
        return self.get('id', -1)
