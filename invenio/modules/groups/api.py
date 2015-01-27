# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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
from flask import request
from sqlalchemy.exc import DBAPIError
from invenio.ext.sqlalchemy import db
from invenio.ext.sqlalchemy.utils import session_manager
from invenio.ext.restful import pagination
from invenio.ext.restful.errors import(
    RestfulError, InvalidPageError
)
from invenio.modules.accounts.models import (
    User, Usergroup, UserUsergroup,
    get_groups_user_not_joined
)
from invenio.modules.accounts.errors import(
    AccountSecurityError, IntegrityUsergroupError
)


@session_manager
def create_group(uid, name, join_policy, login_method, description=None):
    """Create a new user group.

    :param uid: the identifier of the user that tries to create a group
    :param name: name of the new user group
    :param join_policy: the policy of the group for accepting users
    :param login_method: the login login_method
    :param description: description of the group
    """
    if not uid:
        uid = current_user.get_id()
    # check if name exists in groups
    group = Usergroup.query.filter(Usergroup.name == name).first()
    if group:
        raise IntegrityUsergroupError(
            'Group {} already exists'.format(group.name)
        )
    # try to create the group
    group = Usergroup(name=name, description=description,
                      join_policy=join_policy,
                      login_method=login_method)
    db.session.add(group)
    db.session.commit()
    # add user to the group and make him administrator
    group_admin_entry = UserUsergroup(
        id_user=uid, id_usergroup=group.id,
        user_status=UserUsergroup.USER_STATUS['ADMIN']
    )
    db.session.add(group_admin_entry)
    return group
    # try:
    #     # try to create the group
    #     group = Usergroup(name=name, description=description,
    #                       join_policy=join_policy,
    #                       login_method=login_method)
    #     db.session.add(group)
    #     db.session.commit()
    #     # add user to the group and make him administrator
    #     group_admin_entry = UserUsergroup(
    #         id_user=uid, id_usergroup=group.id,
    #         user_status=UserUsergroup.USER_STATUS['ADMIN']
    #     )
    #     db.session.add(group_admin_entry)
    #     db.session.commit()
    #     # return the created group
    #     return group
    # except DBAPIError as e:
    #     db.session.rollback()
    #     raise e


def get_info_about_group(id_usergroup):
    """Get information about a group.

    ::returns:
        a UserUsergroup object
    """
    uug = UserUsergroup.query.filter(
        UserUsergroup.id_usergroup == id_usergroup
    ).first()
    if uug:
        return uug
    else:
        raise IntegrityUsergroupError(
            "Group {} does not exist".format(id_usergroup)
        )


def get_info_about_user_in_group(id_usergroup, id_user):
    """Get information about a user.

    :returns:
        a UserUsergroup object
    """
    uid = current_user.get_id()
    # check if uid is a member or administrator in group
    uug_uid_record = UserUsergroup.query.filter(
        UserUsergroup.id_usergroup == id_usergroup,
        UserUsergroup.id_user == uid
    ).first()
    if not uug_uid_record:
        raise AccountSecurityError(
            "User with  id {} does not exist in group".format(uid)
        )
    if (uug_uid_record.user_status == UserUsergroup.USER_STATUS['ADMIN'] or
       uug_uid_record.user_status == UserUsergroup.USER_STATUS['MEMBER']):
        # user with uid has the right to get information about user in group
        uug = UserUsergroup.query.filter(
            UserUsergroup.id_usergroup == id_usergroup,
            UserUsergroup.id_user == id_user
        ).first()
        if uug:
            return uug
        else:
            raise IntegrityUsergroupError(
                "User {} does not exist in group {}".format(
                    id_user, id_usergroup
                )
            )
    else:
        raise AccountSecurityError(
            "User with  id {} does not have rights to view users of group".
            format(uid)
        )


@session_manager
def delete_group(id_usergroup):
    """Delete a user group.

    :param id_usergroup: the identifier of the group to be deleted
    """
    uid = current_user.get_id()
    # check if group exists
    user_group = Usergroup.query.get_or_404(id_usergroup)
    # check if current user is administrator of the group
    if not user_group.is_admin(uid):
        raise AccountSecurityError(
            "You don't have the right to delete the group {}".format(
                user_group.name
            )
        )

    # delete group
    db.session.delete(user_group)


def add_user_to_group(id_usergroup, id_user, status=None):
    """Add user to a group.

    :param id_usergroup: the identifier of a group
    :param id_user: the identifier of a user
    :param status: the role of the user
    """
    try:
        # check if group exists
        user_group = Usergroup.query.get_or_404(id_usergroup)
        # check if user to be added exists
        user_to_add = User.query.get_or_404(id_user)
        user_group.join(user_to_add, status)
    except (AccountSecurityError, DBAPIError) as e:
        raise e


def remove_user_from_group(id_usergroup, id_user):
    """Remove a user from a group.

    :param id_usergroup: the identifier of a group
    :param id_user: the identifier of a user
    """
    try:
        # check if group exists
        user_group = Usergroup.query.get_or_404(id_usergroup)
        # check if user to be removed exists
        uid = current_user.get_id()
        id_user_to_remove = id_user or uid
        user_to_remove = User.query.get_or_404(id_user_to_remove)
        user_group.leave(user_to_remove)
    except (AccountSecurityError, IntegrityUsergroupError) as e:
        raise e


@session_manager
def update_group(id_usergroup, name, description, join_policy, login_method):
    """Update a group."""
    user_group = Usergroup.query.get_or_404(id_usergroup)
    uid = current_user.get_id()
    if not user_group.is_admin(uid):
        raise AccountSecurityError(
            "You don't have the right to update group {}".format(
                user_group.name
            )
        )
    user_group.name = name
    user_group.description = description
    user_group.join_policy = join_policy
    user_group.login_method = login_method
    db.session.merge(user_group)


def list_members_of_group(id_usergroup):
    """List all members of a group.

    :param id_usergroup: the identifier of a group
    """
    # check if group exists
    user_group = Usergroup.query.get_or_404(id_usergroup)
    # check that current user is a member in group
    uid = current_user.get_id()
    uug_record = UserUsergroup.query.filter(
        UserUsergroup.id_usergroup == id_usergroup,
        UserUsergroup.id_user == uid
    ).first()
    if not uug_record:
        raise AccountSecurityError(
            "User {} is not in group".format(uid)
        )
    # a list of UserUsergroup objects
    return user_group.users


def get_requested_page_for_members_of_group(id_usergroup, endpoint,
                                            page, per_page):
    from invenio.ext.restful import pagination

    if page < 0:
        raise InvalidPageError(
            error_msg="Invalid page: {}".format(page),
            status_code=400
        )
    if per_page < 0:
        raise InvalidPageError(
            error_msg="Invalid per_page: {}".format(per_page),
            status_code=400
        )
    uugs = list_members_of_group(id_usergroup)
    p = pagination.RestfulPagination(
        page=page, per_page=per_page, total_count=len(uugs)
    )
    if (page > p.pages):
        raise InvalidPageError(
            error_msg="Invalid page: {}".format(page),
            status_code=400
        )
    data = p.slice(uugs)
    kwargs = dict(
        endpoint=endpoint
    )
    link_header = p.links(**kwargs)
    return (data, link_header)


def list_groups_of_user(id_user):
    """List all groups that the user is member.

    :param id_usergroup: the identifier of user
    """
    # check that user exists
    user = User.query.get_or_404(id_user)
    # a list of UserUsergroup objects
    return user.usergroups


def get_requested_page_for_groups_of_user(id_user, endpoint, page, per_page):
    """Paginate the list of groups of a user."""

    from invenio.ext.restful import pagination

    if page < 0:
        raise InvalidPageError(
            error_msg="Invalid page: {}".format(page),
            status_code=400
        )
    if per_page < 0:
        raise InvalidPageError(
            error_msg="Invalid per_page: {}".format(per_page),
            status_code=400
        )
    uugs = list_groups_of_user(id_user)
    p = pagination.RestfulPagination(
        page=page, per_page=per_page, total_count=len(uugs)
    )
    if (page > p.pages):
        raise InvalidPageError(
            error_msg="Invalid page: {}".format(page),
            status_code=400
        )
    data = p.slice(uugs)
    kwargs = dict(
        endpoint=endpoint,
    )
    link_header = p.links(**kwargs)
    return (data, link_header)


def list_users_not_in_group(id_usergroup, query):
    """List users that are not members of a group.

    :param id_usergroup: the identifier of a group
    :param query: user query
    :param page: the number of page of results

    :returns:
        a pagination object
    """
    endpoint = request.endpoint
    args = request.args
    page = int(args.get('page', 1))
    per_page = int(args.get('per_page', 10))
    # get group
    group = Usergroup.query.get_or_404(id_usergroup)
    # get the users
    users = group.get_users_not_in_this_group(nickname="%%%s%%" % query).all()
    if per_page < 0:
        raise RestfulError(
            error_msg="Invalid per_page: {}".format(per_page),
            status_code=400
        )
    # pagination object
    p = pagination.RestfulPagination(
        page=page, per_page=per_page, total_count=len(users)
    )
    if (page < 0) or (page > p.pages):
        raise InvalidPageError(
            error_msg="Invalid page: {}".format(page),
            status_code=400
        )
    data = p.slice(users)
    kwargs = dict(
        endpoint=endpoint,
        args=args
    )
    link_header = p.links(**kwargs)
    return (data, link_header)


def list_groups_that_user_is_not_member(id_user, query):
    # get user
    user = User.query.get_or_404(id_user)
    # get groups that user is not a member
    groups = get_groups_user_not_joined(user.id, query).all()
    endpoint = request.endpoint
    args = request.args
    page = int(args.get('page', 1))
    per_page = int(args.get('per_page', 10))
    if per_page < 0:
        raise RestfulError(
            error_msg="Invalid per_page: {}".format(per_page),
            status_code=400
        )
    p = pagination.RestfulPagination(
        page=page, per_page=per_page, total_count=len(groups)
    )
    if (page < 0) or (page > p.pages):
        raise InvalidPageError(
            error_msg="Invalid page: {}".format(page),
            status_code=400
        )
    data = p.slice(groups)
    kwargs = dict(
        endpoint=endpoint,
        args=args
    )
    link_header = p.links(**kwargs)
    return (data, link_header)
