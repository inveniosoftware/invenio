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

"""REST API for groups."""

from functools import wraps
from flask.ext.login import current_user
from flask.ext.restful import abort, Resource, fields, marshal
from flask import request, make_response, json
from invenio.ext.restful import (
    RESTValidator, require_api_auth, require_header
)
from invenio.modules.accounts.models import (
    Usergroup, UserUsergroup
)
from invenio.modules.groups import api as groups_api
from invenio.modules.accounts.errors import(
    AccountSecurityError, IntegrityUsergroupError
)
from invenio.ext.restful.errors import InvalidPageError
from .errors import GroupValidationError


def error_handler(f):
    """Handle exceptions."""
    @wraps(f)
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except GroupValidationError as e:
            abort(e.code, message=e.message,
                  status=e.code, errors=e.error_list)
        except AccountSecurityError as e:
            abort(401, message=e.args[0], status=401)
        except IntegrityUsergroupError as e:
            abort(400, message=e.args[0], status=400)
        except InvalidPageError as e:
            abort(e.status_code, message=e.error_msg, status=e.status_code)
    return inner


class GroupObject(object):

    """A representation of a group."""

    marshal_group_fields = dict(
        name=fields.String,
        description=fields.String,
        join_policy=fields.String
    )

    marshal_uugroup_fields = dict(
        id=fields.Integer,
        name=fields.String,
        description=fields.String,
        join_policy=fields.String,
        member_count=fields.Integer,
        user_status=fields.String
    )

    inverse_usr_status_map = dict(
        (v, k) for k, v in UserUsergroup.USER_STATUS.items()
    )

    def __init__(self, group):
        if isinstance(group, Usergroup):
            self.is_uug = False
            self.name = group.name
            self.description = group.description
            self.join_policy = group.join_policy.value
        elif isinstance(group, UserUsergroup):
            self.is_uug = True
            self.id = group.usergroup.id
            self.name = group.usergroup.name
            self.description = group.usergroup.description
            self.join_policy = group.usergroup.join_policy.value
            self.member_count = len(group.usergroup.users)
            self.user_status = self.inverse_usr_status_map[group.user_status]

    def marshal(self):
        """Package group into a dictionary."""
        if self.is_uug:
            return marshal(self, self.marshal_uugroup_fields)
        return marshal(self, self.marshal_group_fields)


class UserObject(object):

    """A representation of a user."""

    marshal_user_fields = dict(
        id=fields.Integer,
        name=fields.String,
        nickname=fields.String,
        email=fields.String,
        user_status=fields.String
    )

    inverse_usr_status_map = dict(
        (v, k) for k, v in UserUsergroup.USER_STATUS.items()
    )

    def __init__(self, uugroup):
        self.id = uugroup.user.id
        self.name = uugroup.user.name
        self.nickname = uugroup.user.nickname
        self.email = uugroup.user.email
        self.user_status = self.inverse_usr_status_map[uugroup.user_status]

    def marshal(self):
        """Package user information into a dictionary."""
        return marshal(self, self.marshal_user_fields)

# schema for creating a new group
create_group_schema = dict(
    name=dict(required=True, type="string"),
    join_policy=dict(
        required=True,
        type="string",
        allowed=map(lambda key: Usergroup.JOIN_POLICIES[key],
                    Usergroup.JOIN_POLICIES)
    ),
    login_method=dict(
        required=True,
        type="string",
        allowed=map(lambda key: Usergroup.LOGIN_METHODS[key],
                    Usergroup.LOGIN_METHODS)
    ),
    description=dict(required=False, type="string")
)

# schema for updating a group
update_group_schema = dict(
    name=dict(required=True, type="string"),
    description=dict(required=True, type="string"),
    join_policy=dict(
        required=True,
        type="string",
        allowed=map(lambda key: Usergroup.JOIN_POLICIES[key],
                    Usergroup.JOIN_POLICIES)
    ),
    login_method=dict(
        required=True,
        type="string",
        allowed=map(lambda key: Usergroup.LOGIN_METHODS[key],
                    Usergroup.LOGIN_METHODS)
    )
)


class UserResource(Resource):
    """The user resource.

    Contains the actions of a user concerning groups
    """

    method_decorators = [
        require_api_auth(),
        error_handler
    ]

    @require_header('Content-Type', 'application/json')
    def post(self):
        """Create a group."""
        uid = current_user.get_id()
        v = RESTValidator(create_group_schema)
        json_data = request.get_json()
        if v.validate(json_data) is False:
            # raise validation error
            raise GroupValidationError(
                message="validation failed during group creation",
                code=400,
                error_list=v.get_errors()
            )
        name = json_data['name']
        join_policy = json_data['join_policy']
        login_method = json_data['login_method']
        if 'description' in json_data:
            description = json_data['description']
        else:
            description = 'No description'
        created_group = groups_api.create_group(
            uid=uid, name=name, join_policy=join_policy,
            login_method=login_method, description=description
        )
        created_group = GroupObject(created_group).marshal()
        return created_group, 201

    def get(self):
        """Get groups that user is a member."""
        uid = current_user.get_id()
        endpoint = request.endpoint
        args = request.args
        page = int(args.get('page', 1))
        per_page = int(args.get('per_page', 5))
        (uugs, link_header) = groups_api.get_requested_page_for_groups_of_user(
            id_user=uid, endpoint=endpoint, page=page, per_page=per_page
        )
        groups = map(lambda g: GroupObject(g).marshal(), uugs)
        response = make_response(json.dumps(groups))
        response.headers[link_header[0]] = link_header[1]
        response.headers['Content-Type'] = 'application/json'
        return response

    def delete(self):
        abort(405)

    def head(self):
        abort(405)

    def options(self):
        abort(405)

    def patch(self):
        abort(405)

    def put(self):
        abort(405)


class GroupResource(Resource):

    """The group resource."""

    method_decorators = [
        require_api_auth(),
        error_handler
    ]

    def delete(self, id_usergroup):
        """Delete a group.

        :param id_usergroup: the identifier of a group
        """
        groups_api.delete_group(id_usergroup)
        return "", 204

    def get(self, id_usergroup):
        """Get a group.

        :param id_usergroup: the identifier of a group
        """
        uugroup = groups_api.get_info_about_group(id_usergroup)
        group_to_return = GroupObject(uugroup).marshal()
        return group_to_return, 200

    @require_header('Content-Type', 'application/json')
    def patch(self, id_usergroup):
        """Edit group.

        :param id_usergroup: the identifier of a group
        """
        v = RESTValidator(update_group_schema)
        json_data = request.get_json()
        if v.validate(json_data) is False:
            # raise validation error
            raise GroupValidationError(
                message="validation failed during group update",
                code=400,
                error_list=v.get_errors()
            )
        name = json_data['name']
        description = json_data['description']
        join_policy = json_data['join_policy']
        login_method = json_data['login_method']
        groups_api.update_group(
            id_usergroup, name,
            description, join_policy, login_method
        )
        group_to_return = GroupObject(
            groups_api.get_info_about_group()
        ).marshal()
        return group_to_return, 200

    def head(self, id_usergroup):
        abort(405)

    def options(self, id_usergroup):
        abort(405)

    def put(self, id_usergroup):
        abort(405)

    def post(self, id_usergroup):
        abort(405)


class GroupMemberResource(Resource):

    method_decorators = [
        require_api_auth(),
        error_handler
    ]

    def get(self, id_usergroup, id_user):
        """Get user from a group.

        :param id_usergroup: identifier of a group
        :param id_user: identifier of a user
        """
        uug = groups_api.get_info_about_user_in_group(id_usergroup, id_user)
        user_to_return = UserObject(uug).marshal()
        return user_to_return, 200

    def put(self, id_usergroup, id_user):
        """Add user to a group.

        :param id_usergroup: identifier of a group
        :param id_user: identifier of a user
        """
        groups_api.add_user_to_group(id_usergroup, id_user)
        uug = groups_api.get_info_about_user_in_group(id_usergroup, id_user)
        user_to_return = UserObject(uug).marshal()
        return user_to_return, 200

    def delete(self, id_usergroup, id_user):
        """Delete user from group.

        :param id_usergroup: identifier of a group
        :param id_user: identifier of a user
        """
        groups_api.remove_user_from_group(id_usergroup, id_user)
        return "", 204

    def patch(self, id_usergroup, id_user):
        abort(405)

    def post(self, id_usergroup, id_user):
        abort(405)

    def options(self, id_usergroup, id_user):
        abort(405)

    def head(self, id_usergroup, id_user):
        abort(405)


class GroupMemberListResource(Resource):

    method_decorators = [
        require_api_auth(),
        error_handler
    ]

    def get(self, id_usergroup):
        """Get a list of users for a group.

        :param id_usergroup: identifier of a group
        """
        endpoint = request.endpoint
        args = request.args
        page = int(args.get('page', 1))
        per_page = int(args.get('per_page'), 5)
        (uugs, link_header) = groups_api.get_requested_page_for_members_of_group(
            id_usergroup=id_usergroup, endpoint=endpoint,
            page=page, per_page=per_page
        )
        users = map(lambda u: UserObject(u).marshal(), uugs)
        response = make_response(json.dumps(users))
        response.headers[link_header[0]] = link_header[1]
        response.headers['Content-Type'] = 'application/json'
        return response

    def delete(self, id_usergroup):
        abort(405)

    def patch(self, id_usergroup):
        abort(405)

    def post(self, id_usergroup):
        abort(405)

    def options(self, id_usergroup):
        abort(405)

    def head(self, id_usergroup):
        abort(405)

    def put(self, id_usergroup):
        abort(405)


def setup_app(app, api):
    """setup the resources urls."""
    api.add_resource(
        UserResource,
        '/api/users/groups/'
    )
    api.add_resource(
        GroupResource,
        '/api/groups/<int:id_usergroup>'
    )
    api.add_resource(
        GroupMemberResource,
        '/api/groups/<int:id_usergroup>/members/<int:id_user>'
    )
    api.add_resource(
        GroupMemberListResource,
        '/api/groups/<int:id_usergroup>/members'
    )
