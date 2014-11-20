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


def query_list_usergroups(id_user, curr_uid=None):
    """Return query to have a list of groups of the user.

    :param id_user: user's id
    :param curr_uid: user's id of who want to get the group's list
    :return: query to read list
    """
    curr_uid = curr_uid or current_user.get_id()
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
    return Usergroup.query.join(UserUsergroup).filter(
        UserUsergroup.id_user.like(id_user))


def query_groups_user_not_joined(id_user, group_name=None):
    """Return a query to filter groups that user not joined.

    :param id_user: user's id
    :param group_name: string to filter group list
    :return filtering query
    """
    return models_get_groups_user_not_joined(
        id_user=id_user,
        group_name="%%%s%%" % group_name)


def query_members_of_group(id_usergroup, curr_uid=None):
    """List all members of a group.

    :param id_usergroup: the identifier of a group
    """
    curr_uid = curr_uid or current_user.get_id()
    # check if group exists
    user_group = Usergroup.query.get_or_404(id_usergroup)

    # check permissions
    if not user_group.is_part_of(curr_uid):
        # if false, not permitted
        raise AccountSecurityError(
            "You don't have the right to see the list of "
            "users in the group {0}".format(
                user_group.name
            )
        )

    # return list of users
    return UserUsergroup.query.filter_by(id_usergroup=id_usergroup)


def query_users_not_in_this_group(id_usergroup, query='', curr_uid=None):
    """Return query to check a list of user not in this group.

    :param id_usergroup: group's id
    :param query: query to filter users
    :return: query object
    """
    group = Usergroup.query.get_or_404(id_usergroup)
    return group.get_users_not_in_this_group(nickname="%%%s%%" % query)


@session_manager
def create_group(uid, group, curr_uid=None):
    """Create a new user group.

    :param uid: the identifier of the user that tries to create a group
    :param group: group object with info about the group
    :param curr_uid: user's id of who want create group
    :return: new group
    """
    if not uid:
        uid = current_user.get_id()
    curr_uid = curr_uid or uid
    # try to create the group
    return Usergroup.create(
        id_user_admin=uid, group=group)


def get_group(id_usergroup, curr_uid=None):
    """Get information about a group.

    :param id_usergroup: group's id
    :return: the UserUsergroup object
    """
    curr_uid = curr_uid or current_user.get_id()
    group = Usergroup.query.get_or_404(id_usergroup)
    # check permissions
    if not group.is_part_of(curr_uid):
        user = User.query.get_or_404(curr_uid)
        # check if user is pending
        if group.is_pending(user.id):
            # not permitted
            raise AccountSecurityError(_(
                'User "{0}" needs approval to see the'
                ' members of the group "{1}"').format(
                    user.nickname, group.name
                ))
        # not permitted
        raise AccountSecurityError(_(
            'User "{0}" don\'t have the right to see the'
            ' members of the group "{1}"').format(
                user.nickname, group.name)
        )
    return group


@session_manager
def update_group(id_usergroup, group, curr_uid=None):
    """Update a group.

    :param id_usergroup: group's id
    :param name: new name
    :param description: new description
    :param join_policy: new join policy
    :param login_method: new login method
    :return group object
    """
    user_group = Usergroup.query.get_or_404(id_usergroup)
    curr_uid = curr_uid or current_user.get_id()
    # check permissions
    if not user_group.is_admin(curr_uid):
        # if false, not permitted
        raise AccountSecurityError(
            _("You don't have the right to update group {}").format(
                user_group.name
            )
        )
    # if group change name, check if group name already exists
    if user_group.name != group.name and Usergroup.exists(group.name):
        raise IntegrityUsergroupError(
            _('Can\'t rename group "{0}" to "{1}" because '
              'this group already exists.').format(
                  user_group.name, group.name
            )
        )
    user_group.name = group.name
    user_group.description = group.description
    user_group.join_policy = group.join_policy
    user_group.login_method = group.login_method
    db.session.merge(user_group)
    return user_group


@session_manager
def delete_group(id_usergroup, curr_uid=None):
    """Delete a user group.

    :param id_usergroup: the identifier of the group to be deleted
    """
    curr_uid = curr_uid or current_user.get_id()
    user_group = Usergroup.query.get_or_404(id_usergroup)
    # check if current user is administrator of the group
    if not user_group.is_admin(curr_uid):
        # not permitted
        user = User.query.get_or_404(curr_uid)
        raise AccountSecurityError(
            _('User "{0}" don\'t have the right to delete'
              'the group "{1}"').format(
                  user.nickname,
                  user_group.name
            ))
    # delete group
    db.session.delete(user_group)


def get_info_about_user_in_group(id_usergroup, id_user, curr_uid=None):
    """Get information about a user in a group.

    :param id_usergroup: group's id
    :param id_user: user's id
    :returns: UserUsergroup object
    """
    uid = curr_uid or current_user.get_id()
    group = Usergroup.query.filter_by(id=id_usergroup).one()
    # check if uid is a member or administrator in the group
    if not group.is_part_of(uid):
        # not permitted
        raise AccountSecurityError(
            'User with id "{0}" does not have rights to view users of group'.
            format(uid)
        )
    return group.query_userusergroup(id_user).first_or_404()


def add_user_to_group(id_usergroup, id_user, status=None, curr_uid=None):
    """Add user to a group.

    :param id_usergroup: the identifier of a group
    :param id_user: the identifier of a user
    :param status: the role of the user
    """
    curr_uid = curr_uid or current_user.get_id()
    # check if group exists
    user_group = Usergroup.query.get_or_404(id_usergroup)
    # check if user to be added exists
    user_to_add = User.query.get_or_404(id_user)
    # get new status
    status = new_user_status(user=user_to_add, group=user_group,
                             status=status, curr_uid=curr_uid)
    return user_group.join(user=user_to_add, status=status)


@session_manager
def update_userusergroup(id_usergroup, id_user, status=None, curr_uid=None):
    """Update status of user into the group.

    :param id_usergroup: the identifier of a group
    :param id_user: the identifier of a user
    :param status: the role of the user
    :return: UserUsergroup object
    """
    curr_uid = curr_uid or current_user.get_id()
    uug = get_info_about_user_in_group(id_usergroup=id_usergroup,
                                       id_user=id_user, curr_uid=curr_uid)
    uug.user_status = new_user_status(user=uug.user, group=uug.usergroup,
                                      status=status, curr_uid=curr_uid)
    db.session.merge(uug)
    return uug


def approve_user_in_group(id_usergroup, id_user=None, curr_uid=None):
    """Approve the user into the group.

    :param id_usergroup: group's user
    :param id_user: user's id
    :param curr_uid: user that perform the operation
    """
    curr_uid = curr_uid or current_user.get_id()
    user_group = Usergroup.query.get_or_404(id_usergroup)
    id_user2approve = id_user or curr_uid
    user2approve = User.query.get_or_404(id_user2approve)
    # if I want to approve another user from the group
    if(id_user != curr_uid
       # I need to be an admin of the group
       and not user_group.is_admin(curr_uid)):
        # if false, not permitted
        user = User.query.get_or_404(curr_uid)
        raise AccountSecurityError(
            _('User "{0}" have ot enough right to '
              'approve user "{1}" from group "{2}"')
            .format(
                user.nickname, user2approve.nickname,
                user_group.name))

    user_group.approve(user2approve)


def remove_user_from_group(id_usergroup, id_user=None, curr_uid=None):
    """Remove a user from a group.

    :param id_usergroup: the identifier of a group
    :param id_user: the identifier of a user
    """
    curr_uid = curr_uid or current_user.get_id()
    id_user2remove = id_user or curr_uid
    user_group = Usergroup.query.get_or_404(id_usergroup)
    user2remove = User.query.get_or_404(id_user2remove)

    # if I want to remove another user from the group
    if(id_user != curr_uid
       # I need to be an admin of the group
       and not user_group.is_admin(curr_uid)):
        # if false, not permitted
        user = User.query.get_or_404(curr_uid)
        raise AccountSecurityError(
            _('User "{0}" have not enough right to '
              'remove user "{1}" from group "{2}"')
            .format(
                user.nickname, user2remove.nickname,
                user_group.name))

    # remove user from the group
    user_group.leave(user=user2remove)


def new_user_status(user, group=None, status=None, curr_uid=None):
    """Return user status for new user.

    This method define the policy for accepting new users
    in the group.

    :param user: user that want to join the group
    :param group: if None, is as asking to join newly created group
    :param status: if curr_uid user want join user specifing the new status
    :param curr_uid: user's id of who want to add user in the group
    :return: the new status
    """
    curr_uid = curr_uid or current_user.get_id()
    # if group don't have admin users
    if not group or group.admins.count() == 0:
        # check if current user tries to add another user
        if curr_uid != user.id:
            # non administrator tries to add a user to group
            raise AccountSecurityError(
                _('Not enough right to '
                    'add another user "{0}" into a group').format(
                        user.nickname)
            )

        # set the user as admin
        return UserUsergroup.USER_STATUS['ADMIN']

    # if current user is NOT the admin, return error
    if not group.is_admin(curr_uid):
        # current user can add only him self
        if curr_uid != user.id:
            # non administrator tries to add a user to group
            raise AccountSecurityError(
                _('Not enough right to '
                    'add user "{0}" from group "{1}"').format(
                        user.nickname, group.name)
            )
    # current user is admin, and specify the new status
    else:
        if user.id == curr_uid and group.admins.count() == 1:
            # if current user is the only admin, leave as admin
            return UserUsergroup.USER_STATUS['ADMIN']
        elif status:
            # return the status specified by the admin
            return status
    # returns default status
    return group.new_user_status
