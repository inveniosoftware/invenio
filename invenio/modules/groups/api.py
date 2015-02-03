# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014, 2015 CERN.
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

"""Groups API."""

from flask.ext.login import current_user

from invenio.base.i18n import _
from invenio.ext.sqlalchemy import db
from invenio.ext.sqlalchemy.utils import session_manager
from invenio.modules.accounts.errors import AccountSecurityError, \
    IntegrityUsergroupError
from invenio.modules.accounts.models import User, UserUsergroup, Usergroup, \
    get_groups_user_not_joined as models_get_groups_user_not_joined


class GroupsAPI:

    """API for Groups."""

    def __init__(self, user_group):
        """Init API with loading usergroup.

        :param user_group: usergroup
        """
        self.curr_uid = current_user.get_id()
        # check if group exists
        self.user_group = user_group
        # GroupsAPI.get_group(id_usergroup)

    def query_members(self):
        """List all members of a group.

        :param id_usergroup: the identifier of a group
        """
        # check permissions
        if not self.user_group.is_part_of(self.curr_uid):
            # if false, not permitted
            raise AccountSecurityError(
                "You don't have the right to see the list of "
                "users in the group {0}".format(
                    self.user_group.name
                )
            )
        # return list of users
        return UserUsergroup.query.filter_by(id_usergroup=self.user_group.id)

    def query_users_not_in_this_group(self, query=''):
        """Return query to check a list of user not in this group.

        :param query: query to filter users
        :return: query object
        """
        return self.user_group.get_users_not_in_this_group(
            nickname="%%%s%%" % query)

    @session_manager
    @staticmethod
    def create_group(uid, group):
        """Create a new user group.

        :param uid: the identifier of the user that tries to create a group
        :param group: group object with info about the group
        :return: new group
        """
        if not uid:
            uid = current_user.get_id()
        # try to create the group
        return Usergroup.create(
            id_user_admin=uid, group=group)

    @staticmethod
    def get_group(id_usergroup):
        """Load a group object.

        :param id_usergroup: group's id
        :return: the Usergroup object
        """
        curr_uid = current_user.get_id()
        group = Usergroup.query.get_or_404(id_usergroup)
        # check permissions
        if not group.is_part_of(curr_uid):
            user = User.query.get_or_404(curr_uid)
            # check if user is pending
            if group.is_pending(user.id):
                # not permitted
                raise AccountSecurityError(_(
                    'User "%(nickname)s" needs approval to see the'
                    ' members of the group "%(group_name)s"').format(
                        nickname=user.nickname, group_name=group.name
                    ))
            # not permitted
            raise AccountSecurityError(_(
                'User "%(nickname)s" don\'t have the right to see the'
                ' members of the group "%(group_name)s"').format(
                    nickname=user.nickname, group_name=group.name)
            )
        return group

    @session_manager
    def update_group(self, group):
        """Update a group.

        :param group: group's object with the new informations
        :return group object
        """
        # check permissions
        if not self.user_group.is_admin(self.curr_uid):
            # if false, not permitted
            raise AccountSecurityError(
                _("You don't have the right to update group {}").format(
                    self.user_group.name
                )
            )
        # if group change name, check if group name already exists
        if self.user_group.name != group.name and Usergroup.exists(group.name):
            raise IntegrityUsergroupError(
                _('Can\'t rename group "%(group_name)s" to "%(group_name2)s" '
                  'because this group already exists.',
                  group_name=self.user_group.name, group_name2=group.name
                  ))
        self.user_group.name = group.name
        self.user_group.description = group.description
        self.user_group.join_policy = group.join_policy
        self.user_group.login_method = group.login_method
        db.session.merge(self.user_group)
        return self.user_group

    @session_manager
    def delete_group(self):
        """Delete user group."""
        # check if current user is administrator of the group
        if not self.user_group.is_admin(self.curr_uid):
            # not permitted
            user = User.query.get_or_404(self.curr_uid)
            raise AccountSecurityError(
                _('User "%(nickname)s" don\'t have the right to delete'
                  'the group "%(group_name)s"',
                  nickname=user.nickname,
                  group_name=self.user_group.name
                  ))
        # delete group
        db.session.delete(self.user_group)

    def get_info_about_user_in_group(self, id_user=None):
        """Get information about a user in a group.

        :param id_user: user's id
        :returns: UserUsergroup object
        """
        id_user = id_user or self.curr_uid
        # check if uid is a member or administrator in the group
        if id_user != self.curr_uid and \
                not self.user_group.is_part_of(self.curr_uid):
            # not permitted
            user = User.query.get_or_404(self.curr_uid)
            raise AccountSecurityError(_(
                'User "%(nickname)d" does not have rights '
                'to see the list of users of the group "%(group_name)s"',
                nickname=user.nickname,
                group_name=self.user_group.name
            ))
        return self.user_group.query_userusergroup(id_user).first_or_404()

    def add_user_to_group(self, id_user, status=None):
        """Add user to a group.

        :param id_user: the identifier of a user
        :param status: the role of the user
        :return: UserUsergroup object
        """
        # check if user to be added exists
        user_to_add = User.query.get_or_404(id_user)
        # get new status
        status = self.new_user_status(user=user_to_add, status=status)
        return self.user_group.join(user=user_to_add, status=status)

    @session_manager
    def update_user_status(self, id_user, status=None):
        """Update status of user into the group.

        :param id_user: the identifier of a user
        :param status: the role of the user
        :return: UserUsergroup object
        """
        uug = self.get_info_about_user_in_group(id_user=id_user)
        uug.user_status = self.new_user_status(user=uug.user, status=status)
        db.session.merge(uug)
        return uug

    def approve_user_in_group(self, id_user=None):
        """Approve the user into the group.

        :param id_user: user's id
        """
        id_user2approve = id_user or self.curr_uid
        user2approve = User.query.get_or_404(id_user2approve)
        # if I want to approve another user from the group
        if(id_user != self.curr_uid
           # I need to be an admin of the group
           and not self.user_group.is_admin(self.curr_uid)):
            # if false, not permitted
            user = User.query.get_or_404(self.curr_uid)
            raise AccountSecurityError(
                _('User "%(nickname)s" have ot enough right to '
                  'approve user "%(nickname2)s" from group "%(group_name)s"',
                  nickname=user.nickname, nickname2=user2approve.nickname,
                  group_name=self.user_group.name))

        self.user_group.approve(user2approve)

    def remove_user_from_group(self, id_user=None):
        """Remove a user from a group.

        :param id_user: the identifier of a user
        """
        id_user2remove = id_user or self.curr_uid
        user2remove = User.query.get_or_404(id_user2remove)

        # if I want to remove another user from the group
        if(id_user != self.curr_uid
           # I need to be an admin of the group
           and not self.user_group.is_admin(self.curr_uid)):
            # if false, not permitted
            user = User.query.get_or_404(self.curr_uid)
            raise AccountSecurityError(
                _('User "%(nickname)s" have not enough right to '
                  'remove user "%(nickname2)s" from group "%(group_name)s"',
                  nickname=user.nickname, nickname2=user2remove.nickname,
                  group_name=self.user_group.name))

        # remove user from the group
        self.user_group.leave(user=user2remove)

    def new_user_status(self, user, status=None):
        """Return user status for new user.

        This method define the policy for accepting new users
        in the group.

        :param user: user that want to join the group
        :param status: if curr_uid user want join user specifing the new status
        :return: the new status
        """
        # if group don't have admin users
        if not self.user_group or self.user_group.admins.count() == 0:
            # check if current user tries to add another user
            if self.curr_uid != user.id:
                # non administrator tries to add a user to group
                raise AccountSecurityError(
                    _('Not enough right to '
                      'add another user "%(nickname)s" into a group',
                      nickname=user.nickname))

            # set the user as admin
            return UserUsergroup.USER_STATUS['ADMIN']

        # if current user is NOT the admin, return error
        if not self.user_group.is_admin(self.curr_uid):
            # current user can add only him self
            if self.curr_uid != user.id:
                # non administrator tries to add a user to group
                raise AccountSecurityError(
                    _('Not enough right to '
                      'add user "%(nickname)s" from group "%(group_name)s"',
                      nickname=user.nickname, group_name=self.user_group.name))
        # current user is admin, and specify the new status
        else:
            if user.id == self.curr_uid and self.user_group.admins.count() == 1:
                # if current user is the only admin, leave as admin
                return UserUsergroup.USER_STATUS['ADMIN']
            elif status:
                # return the status specified by the admin
                return status
        # returns default status
        return self.user_group.new_user_status

    @staticmethod
    def query_list_usergroups(id_user):
        """Return query to have a list of groups of the user.

        :param id_user: user's id
        :return: query to read list
        """
        curr_uid = current_user.get_id()
        # if you want know group's list of other user
        if(curr_uid != id_user):
            # not permitted
            user = User.query.get_or_404(id_user)
            curr_user = User.query.get_or_404(curr_uid)
            # TODO can be implemented a more complex policy?
            raise AccountSecurityError(
                _('User "{0}" don\'t have the right to get list'
                  ' the groups of user "{1}"').format(
                      curr_user.nickname,
                      user.nickname))
        return Usergroup.query_list_usergroups(id_user=id_user)

    @staticmethod
    def query_list_userusergroups(id_user):
        """Return query to have a list of UserUsergroups of the user.

        :param id_user: user's id
        :return: query to read list
        """
        curr_uid = current_user.get_id()
        # if you want know group's list of other user
        if(curr_uid != id_user):
            # not permitted
            user = User.query.get_or_404(id_user)
            curr_user = User.query.get_or_404(curr_uid)
            # TODO can be implemented a more complex policy?
            raise AccountSecurityError(
                _('User "{0}" don\'t have the right to get list'
                  ' the groups of user "{1}"').format(
                      curr_user.nickname,
                      user.nickname))
        return UserUsergroup.query_list(id_user=id_user)

    @staticmethod
    def query_groups_user_not_joined(id_user, group_name=None):
        """Return a query to filter groups that user not joined.

        :param id_user: user's id
        :param group_name: string to filter group list
        :return filtering query
        """
        curr_uid = current_user.get_id()
        # if you want know group's list of other user
        if(curr_uid != id_user):
            # not permitted
            user = User.query.get_or_404(id_user)
            curr_user = User.query.get_or_404(curr_uid)
            # TODO can be implemented a more complex policy?
            raise AccountSecurityError(
                _('User "%(nickname)s" don\'t have the right to get list'
                  ' the groups that user "%(nickname2)s" don\'t join',
                  nickname=curr_user.nickname,
                  nickname2=user.nickname))
        return models_get_groups_user_not_joined(
            id_user=id_user,
            group_name="%%%s%%" % group_name)
