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

"""REST API for groups."""

from functools import wraps

from flask import request
from flask.ext.login import current_user
from flask.ext.restful import Resource, abort, fields, marshal_with, reqparse

from invenio.ext.restful import pagination, require_api_auth, require_header, \
    require_oauth_scopes
from invenio.ext.restful.errors import InvalidPageError
from invenio.modules.accounts.errors import(
    AccountSecurityError, IntegrityUsergroupError
)
from invenio.modules.accounts.models import UserUsergroup, Usergroup
from invenio.modules.groups.api import GroupsAPI

from .errors import GroupValidationError


class LoginMethodField(fields.Raw):

    """Translate a login_method."""

    def format(self, value):
        """Translate value."""
        return next((key for key, val in Usergroup.LOGIN_METHODS.items()
                     if val == value), None)


class JoinPolicyField(fields.Raw):

    """Translate a join_policy."""

    def format(self, value):
        """Translate value."""
        return next((key for key, val in Usergroup.JOIN_POLICIES.items()
                     if val == value), None)


class UserStatusField(fields.Raw):

    """Translate a user_status."""

    def format(self, value):
        """Translate value."""
        return next((key for key, val in UserUsergroup.USER_STATUS.items()
                     if val == value), None)


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
            abort(401, message=e.args[0].encode('utf-8'))
            # abort(405, message="hello")
        except IntegrityUsergroupError as e:
            abort(400, message=e.args[0].encode('utf-8'), status=400)
        except InvalidPageError as e:
            abort(e.status_code, message=e.error_msg,
                  status=e.status_code)
    return inner


UsergroupObject = {
    'id': fields.Integer,
    'name': fields.String,
    'description': fields.String,
    'join_policy': JoinPolicyField,
    'login_method': LoginMethodField,
}

UserObject = {
    'id': fields.Integer,
    'nickname': fields.String,
    'email': fields.String,
    'last_login': fields.DateTime(),
}

UserUserUsergroupObject = {
    'user_status': UserStatusField,
    'user_status_date': fields.DateTime(),
    'user': fields.Nested(UserObject),
}


class GroupsResource(Resource):

    """The groups resource."""

    method_decorators = [
        require_api_auth(),
        error_handler
    ]

    @marshal_with(UsergroupObject)
    @require_oauth_scopes('groups:read')
    def get(self):
        """Get the group's list.

        Url parameters:
            - page
            - per_page
        """
        id_user = current_user.get_id()

        parser = reqparse.RequestParser()
        parser.add_argument('page', type=int,
                            help="Require a specific page")
        parser.add_argument('per_page', type=int,
                            help="Set how much result per page")

        args = parser.parse_args()
        page = args['page']
        per_page = args['per_page']

        return pagination.RestfulSQLAlchemyPagination(
            GroupsAPI.query_list_usergroups(
                id_user=id_user),
            page=page or 1, per_page=per_page or 10).items

    @require_header('Content-Type', 'application/json')
    @marshal_with(UsergroupObject)
    @require_oauth_scopes('groups:write')
    def post(self, i_dont_know=None):
        """Create new group."""
        json_data = request.get_json() or {}

        usergroup = Usergroup(
            name=json_data['name'] if 'name' in json_data else None,
            description=json_data['description']
            if 'description' in json_data else None,
            join_policy=Usergroup.JOIN_POLICIES[json_data['join_policy']]
            if 'join_policy' in json_data and
            json_data['join_policy'] in Usergroup.JOIN_POLICIES else None,
            login_method=Usergroup.LOGIN_METHODS[json_data['login_method']]
            if 'login_method' in json_data and
            json_data['login_method'] in Usergroup.LOGIN_METHODS else None,
        )
        curr_uid = current_user.get_id()

        return GroupsAPI.create(
            uid=curr_uid,
            group=usergroup,
        )

    def head(self, id_usergroup):
        """Head not supported."""
        abort(405)

    def options(self, id_usergroup):
        """HTTP Options not supported."""
        abort(405)

    def put(self, id_usergroup):
        """Put not supported."""
        abort(405)

    def delete(self, id_usergroup):
        """Delete not supported."""
        abort(405)


class GroupResource(Resource):

    """The group resource."""

    method_decorators = [
        require_api_auth(),
        error_handler
    ]

    @marshal_with(UsergroupObject)
    @require_oauth_scopes('groups:read')
    def get(self, id_usergroup):
        """Get a group.

        :param id_usergroup: the identifier of a group
        """
        return GroupsAPI.get_group(id_usergroup=id_usergroup)

    def head(self, id_usergroup):
        """HTTP Head not supported."""
        abort(405)

    def options(self, id_usergroup):
        """HTTP Options not supported."""
        # TODO
        abort(405)

    @marshal_with(UsergroupObject)
    @require_oauth_scopes('groups:write')
    def put(self, id_usergroup):
        """HTTP Put: update group's informations."""
        json_data = request.get_json() or {}

        usergroup = Usergroup(
            name=json_data['name'] if 'name' in json_data else None,
            description=json_data['description']
            if 'description' in json_data else None,
            join_policy=Usergroup.JOIN_POLICIES[json_data['join_policy']]
            if 'join_policy' in json_data and
            json_data['join_policy'] in Usergroup.JOIN_POLICIES else None,
            login_method=Usergroup.LOGIN_METHODS[json_data['login_method']]
            if 'login_method' in json_data and
            json_data['login_method'] in Usergroup.LOGIN_METHODS else None,
        )
        gapi = GroupsAPI(user_group=GroupsAPI.get_group(id_usergroup))
        gapi.check_access()
        return gapi.update(group=usergroup)

    def post(self, i_dont_know, id_usergroup):
        """HTTP Post not supported."""
        # TODO
        abort(405)

    @require_oauth_scopes('groups:write')
    def delete(self, id_usergroup):
        """Delete a group.

        :param id_usergroup: the identifier of a group
        """
        gapi = GroupsAPI(user_group=GroupsAPI.get_group(id_usergroup))
        gapi.delete()
        return "", 204


class UsersResource(Resource):

    """The users resource."""

    method_decorators = [
        require_api_auth(),
        error_handler
    ]

    @marshal_with(UserUserUsergroupObject)
    @require_oauth_scopes('groups:read')
    def get(self, id_usergroup):
        """Get the user's list.

        Url parameters:
            - page
            - per_page
        """
        parser = reqparse.RequestParser()
        parser.add_argument('page', type=int,
                            help="Require a specific page")
        parser.add_argument('per_page', type=int,
                            help="Set how much result per page")

        args = parser.parse_args()
        page = args['page']
        per_page = args['per_page']

        gapi = GroupsAPI(user_group=GroupsAPI.get_group(id_usergroup))

        return pagination.RestfulSQLAlchemyPagination(
            gapi.query_members(),
            page=page or 1, per_page=per_page or 10
        ).items


class UserResource(Resource):

    """The user resource."""

    method_decorators = [
        require_api_auth(),
        error_handler
    ]

    @marshal_with(UserUserUsergroupObject)
    @require_oauth_scopes('groups:read')
    def get(self, id_usergroup, id_user):
        """Get info of user in a group.

        :param id_usergroup: the identifier of a group
        :param id_user: the identifier of a user
        """
        gapi = GroupsAPI(user_group=GroupsAPI.get_group(id_usergroup))
        return gapi.get_info(id_user=id_user)

    @marshal_with(UserUserUsergroupObject)
    @require_oauth_scopes('groups:write')
    def post(self, id_usergroup, id_user):
        """HTTP Post: insert a user in the group."""
        json_data = request.get_json() or {}

        user_status = UserUsergroup.USER_STATUS[json_data['user_status']] \
            if 'user_status' in json_data \
            and json_data['user_status'] in UserUsergroup.USER_STATUS else None

        gapi = GroupsAPI(user_group=GroupsAPI.get_group(id_usergroup))

        return gapi.add(id_user=id_user, status=user_status)

    @marshal_with(UserUserUsergroupObject)
    @require_oauth_scopes('groups:write')
    def put(self, id_usergroup, id_user):
        """HTTP Put: update user's group informations."""
        json_data = request.get_json() or {}

        user_status = json_data['user_status'] if 'user_status' \
            in json_data else None

        gapi = GroupsAPI(user_group=GroupsAPI.get_group(id_usergroup))

        return gapi.update_user_status(id_user=id_user, status=user_status)

    @require_oauth_scopes('groups:write')
    def delete(self, id_usergroup, id_user):
        """Delete a user in the group.

        :param id_usergroup: the identifier of a group
        :param id_user: the identifier of the user
        """
        gapi = GroupsAPI(user_group=GroupsAPI.get_group(id_usergroup))
        gapi.remove(id_user=id_user)
        return "", 204


def setup_app(app, api):
    """setup the resources urls."""
    api.add_resource(
        GroupsResource,
        '/api/groups'
    )
    api.add_resource(
        GroupResource,
        '/api/groups/<int:id_usergroup>'
    )
    api.add_resource(
        UsersResource,
        '/api/groups/<int:id_usergroup>/users'
    )
    api.add_resource(
        UserResource,
        '/api/groups/<int:id_usergroup>/users/<int:id_user>'
    )

    # Register scopes
    with app.app_context():
        from invenio.modules.oauth2server.models import Scope
        from invenio.modules.oauth2server.registry import scopes
        scopes.register(Scope(
            'groups:read',
            group='Groups',
            help_text='Allow read my groups.',
        ))
        scopes.register(Scope(
            'groups:write',
            group='Groups',
            help_text='Allow modify my groups.',
        ))
