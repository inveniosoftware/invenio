# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""
    invenio.models.access.bases
    ---------------------------

    JSONAlchemy model extension.

    example of a document base::

        bases:
            invenio.modules.access.bases.AclFactory('doc')
"""

import six

from flask_login import current_user

from .engine import acc_authorize_action
from .control import acc_is_user_in_role, acc_get_role_id
from .firerole import compile_role_definition, acc_firerole_check_user
from .local_config import SUPERADMINROLE, CFG_WEBACCESS_WARNING_MSGS


def AclFactory(obj=''):
    """Creates access control behavior extension for JSONAlchemy model.

    :param obj: name of action object (e.g. check 'viewrestrdoc' where
        'viewrestr' is action and 'doc' is `obj`)
    :return: JSONAlchemy class extesion
        (note: it has to return class not instance)
    """

    class Acl(object):
        """
        Access controled behavior for JSONAlchemy models.
        """

        def is_authorized(self, user_info=None, action='viewrestr'):
            """Check if the user is authorized to perform the action with the
            given restrictions.

            This method is able to run *pre* and *post* hooks to extend its
            functionality,
            e.g. :class:`~invenio.modules.records.bases:DocumentsHooks`

        .. note::

                If the object has embed restrictions it will override the
                access right of the parent. For example in
                :class:`~invenio.modules.documents.api:Document` and
                :class:`~invenio.modules.records.api:Record` the `Document`
                will override the `Record` restriction which means if the
                `Record` is restricted and the `Document` is open the user
                will have access to the file.

            :param user_info: an instance of
                :class:`~invenio.ext.login.legacy_user.UserInfo`
                (default: :class:`flask_login.current_user`)
            :return: a tuple, of the form `(auth_code, auth_message)` where
                `auth_code` is 0 if the authorization is granted and greater
                than 0 otherwise.
            """
            if user_info is None:
                user_info = current_user

            restriction = self.get('restriction')
            if restriction is None:
                return (1, 'Missing restriction')

            if acc_is_user_in_role(user_info, acc_get_role_id(SUPERADMINROLE)):
                return (0, CFG_WEBACCESS_WARNING_MSGS[0])

            is_authorized = (0, CFG_WEBACCESS_WARNING_MSGS[0])

            try:
                is_authorized = self.acl_pre_authorized_hook(
                    user_info, action, is_authorized)
            except AttributeError:
                pass

            if is_authorized[0] != 0 and not any(restriction.values()):
                return is_authorized

            for auth_type, auth_value in six.iteritems(restriction):
                if auth_type == 'status':
                    is_authorized = acc_authorize_action(user_info,
                                                         action+obj,
                                                         status=auth_value)
                elif auth_type == 'email':
                    if auth_value.lower().strip() != \
                            user_info['email'].lower().strip():
                        is_authorized = (1, 'You must be member of the group'
                                         '%s in order to access this document'
                                         % repr(auth_value))
                elif auth_type == 'group':
                    if auth_value not in user_info['group']:
                        is_authorized = (1, 'You must be member of the group'
                                         '%s in order to access this document'
                                         % repr(auth_value))
                elif auth_type == 'role':
                    if not acc_is_user_in_role(user_info,
                                               acc_get_role_id(auth_value)):
                        is_authorized = (1, 'You must be member in the role %s'
                                         ' in order to access this document' %
                                         repr(auth_value))
                elif auth_type == 'firerole':
                    if not acc_firerole_check_user(
                            user_info, compile_role_definition(auth_value)):
                        is_authorized = (1, 'You must be authorized in '
                                         'order to access this document')

                if is_authorized[0] != 0:
                    break

            try:
                is_authorized = self.acl_post_authorized_hook(
                    user_info, action, is_authorized)
            except AttributeError:
                pass

            return is_authorized

    # Returns class not an instance!
    return Acl
