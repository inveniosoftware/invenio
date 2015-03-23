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

""" Restful API for tags.

Some useful variables are shown below.
py:data: tag_post_schema , stores data when creating a new tag
py:data: tag_update_schema , stores data when updating a tag
py:data: add_tags_schema , stores a list of tags that will be
attached to a record
"""

from functools import wraps
from flask_login import current_user
from flask_restful import abort, Resource, fields, marshal
from flask import request
from invenio.ext.restful import (
    require_api_auth, require_header,
    RESTValidator
)
from invenio.modules.tags import api as tags_api
from invenio.modules.tags.models import WtgTAG
from .errors import (
    TagError, TagNotCreatedError,
    TagNotFoundError, TagNotDeletedError, TagOwnerError, TagNotUpdatedError,
    TagsNotFetchedError, TagValidationError, TagRecordAssociationError,
    RecordNotFoundError
)


def error_handler(f):
    """error handler."""
    @wraps(f)
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except (TagNotCreatedError, TagNotFoundError,
                TagNotDeletedError, TagNotUpdatedError,
                TagsNotFetchedError, TagOwnerError,
                TagRecordAssociationError, RecordNotFoundError) as e:
            abort(e.status_code, message=e.error_msg, status=e.status_code)
        except TagValidationError as e:
            abort(e.status_code, message=e.error_msg, status=e.status_code,
                  errors=e.error_list)
        except TagError as e:
            if len(e.args) >= 1:
                abort(400, message=e.args[0], status=400)
            else:
                abort(500, message="Internal server error", status=500)
    return inner


class TagRepresenation(object):

    """A representation of a tag.

    This class will be only used to return a tag as JSON.
    """

    marshaling_fields = dict(
        id=fields.Integer,
        name=fields.String,
        id_user=fields.Integer,
        group_name=fields.String,
        group_access_rights=fields.String,
        show_in_description=fields.Boolean
    )

    def __init__(self, retrieved_tag):
        """Initialization.

        Declared the attributes to marshal with a tag.
        :param retrieved_tag: a tag from the database
        """
        #get fields from the given tag
        self.id = retrieved_tag.id
        self.name = retrieved_tag.name
        self.id_user = retrieved_tag.id_user
        if retrieved_tag.usergroup is None:
            self.group_name = ''
        else:
            self.group_name = retrieved_tag.usergroup.name
        #set the group access rights as a string
        group_rights_list = (
            WtgTAG.ACCESS_RIGHTS[retrieved_tag.group_access_rights]
        )
        if len(group_rights_list) == 0:
            self.group_access_rights = "Nothing"
        elif len(group_rights_list) == 1:
            self.group_access_rights = "View"
        else:
            self.group_access_rights = ",".join(group_rights_list)
        self.show_in_description = retrieved_tag.show_in_description

    def marshal(self):
        """Marshal the Tag.

        Marshal a tag with the defined attributes(marshaling_fields) as JSON.
        """
        return marshal(self, self.marshaling_fields)


tag_post_schema = dict(
    name=dict(required=True, type="string"),
)


tag_update_schema = dict(
    rights=dict(required=False,
                type="integer",
                allowed=map(lambda e: e, WtgTAG.ACCESS_RIGHTS)),
    groupname=dict(required=False, type="string"),
    show_in_description=dict(required=False, type="boolean"),
)


class TagResource(Resource):

    """The Tag Resource."""

    method_decorators = [
        require_api_auth(),
        error_handler
    ]

    def get(self, tag_name):
        """Get a tag.

        :param tag_name: the name of the tag to retrieve
        """
        uid = current_user.get_id()
        tag_retrieved = tags_api.get_tag_of_user(uid, tag_name)
        tag = TagRepresenation(tag_retrieved)
        return tag.marshal()

    def delete(self, tag_name):
        """Delete a tag.

        Checks if the tag is attached to records. If True,
        the tag is attached and then is deleted.

        :param tag_name: the name of the tag to delete
        """
        uid = current_user.get_id()
        tags_api.delete_tag_from_user(uid, tag_name)
        return "", 204

    @require_header('Content-Type', 'application/json')
    def patch(self, tag_name):
        """Update a tag.

        The attributes that can be updated are:
        - group name
        - group access rights
        - show_in_description
        :param tag_name: the name of the tag to update
        """
        json_data = request.get_json()
        v = RESTValidator(tag_update_schema)
        if v.validate(json_data) is False:
            raise TagValidationError(
                error_msg="Validation for tag update failed",
                status_code=400,
                error_list=v.get_errors())
        uid = current_user.get_id()
        tag_retrieved = tags_api.update_tag_of_user(uid, tag_name, json_data)
        tag = TagRepresenation(tag_retrieved)
        return tag.marshal(), 201

    def post(self, tag_name):
        """post."""
        abort(405)

    def options(self, tag_name):
        """options."""
        abort(405)

    def put(self, tag_name):
        """put."""
        abort(405)

    def head(self, tag_name):
        """head."""
        abort(405)


class TagListResource(Resource):

    """The tags list resource."""

    method_decorators = [
        require_api_auth(),
        error_handler
    ]

    def get(self):
        """ Get a list of tags.

        Get the list of tags a user owns.
        """
        uid = current_user.get_id()
        tags_retrieved = tags_api.get_all_tags_of_user(uid)
        tags = [TagRepresenation(t) for t in tags_retrieved]
        return map(lambda t: t.marshal(), tags)

    def delete(self):
        """Delete all tags.

        Delete all the tags a user owns.
        """
        uid = current_user.get_id()
        tags_api.delete_all_tags_from_user(uid)
        return "", 204

    @require_header('Content-Type', 'application/json')
    def post(self):
        """Create a new tag.

        Creates a new tag and sets as owner the current user.
        """
        json_data = request.get_json()
        v = RESTValidator(tag_post_schema)
        if v.validate(json_data) is False:
            raise TagValidationError(
                error_msg="Validation error for tag creation",
                status_code=400,
                error_list=v.get_errors())
        uid = current_user.get_id()
        tag_to_create = tags_api.create_tag_for_user(uid, json_data['name'])
        tag_to_return = TagRepresenation(tag_to_create)
        return tag_to_return.marshal(), 201

    def patch(self):
        """PATCH."""
        abort(405)

    def options(self):
        """OPTIONS."""
        abort(405)

    def put(self):
        """PUT."""
        abort(405)

    def head(self):
        """HEAD."""
        abort(405)


add_tags_schema = dict(
    tags=dict(type="list", schema=dict(type="string"))
)


class RecordTagResource(Resource):

    """Handles a tag attached on a record."""

    method_decorators = [
        require_api_auth(),
        error_handler
    ]

    def delete(self, record_id, tag_name):
        """Detach a tag from a record.

        :param record_id: the identifier of the record
        :param tag_name: the name of the tag
        """
        uid = current_user.get_id()
        tags_api.detach_tag_from_record(uid, tag_name, record_id)
        return "", 204

    def post(self, record_id, tag_name):
        """A POST request.

        :param record_id: the identifier of the record
        :param tag_name: the name of the tag
        """
        abort(405)

    def put(self, record_id, tag_name):
        """A PUT request.

        :param record_id: the identifier of the record
        :param tag_name: the name of the tag
        """
        abort(405)

    def patch(self, record_id, tag_name):
        """A PATCH request.

        :param record_id: the identifier of the record
        :param tag_name: the name of the tag
        """
        abort(405)

    def options(self, record_id, tag_name):
        """A OPTIONS request.

        :param record_id: the identifier of the record
        :param tag_name: the name of the tag
        """
        abort(405)

    def head(self, record_id, tag_name):
        """A HEAD request.

        :param record_id: the identifier of the record
        :param tag_name: the name of the tag
        """
        abort(405)

    def get(self, record_id, tag_name):
        """A GET request.

        :param record_id: the identifier of the record
        :param tag_name: the name of the tag
        """
        abort(405)


class RecordListTagResource(Resource):

    """This resource handles tags when it comes to records."""

    method_decorators = [
        require_api_auth(),
        error_handler
    ]

    @require_header('Content-Type', 'application/json')
    def post(self, record_id):
        """Attach a list of tags to a record.

        If a tag in the list exists in database then it is attached
        to the record else the tag is created an then it is attached
        to the record
        :param record_id: the identifier of the record
        """
        json_data = request.get_json()
        attachTagsValidator = RESTValidator(add_tags_schema)
        if attachTagsValidator.validate(json_data) is False:
            raise TagValidationError(
                error_msg="Validation error in attaching tags on record",
                status_code=400,
                error_list=attachTagsValidator.get_errors())
        uid = current_user.get_id()
        tags_just_attached = tags_api.attach_tags_to_record(uid,
                                                            json_data['tags'],
                                                            record_id)
        if len(tags_just_attached) == 0:
            return []
        else:
            return map(
                lambda t: TagRepresenation(t).marshal(), tags_just_attached
            )

    def get(self, record_id):
        """Retrieve all the attached on a record tags.

        :param record_id: the identifier of the record
        """
        attached_tags = tags_api.get_attached_tags_on_record(record_id)
        if len(attached_tags) == 0:
            return []
        else:
            return map(lambda t: TagRepresenation(t).marshal(), attached_tags)

    def delete(self, record_id):
        """Detach all the tags from a record.

        :param record_id: the identifier of the record
        """
        pass

    def put(self, record_id):
        """Replace all tags for a record.

        :param record_id: the identifier of the record
        """
        pass

    def head(self, record_id):
        """A HEAD request."""
        abort(405)

    def patch(self, record_id):
        """A PATCH request."""
        abort(405)

    def options(self, record_id):
        """A OPTIONS request."""
        abort(405)

#
# Register API resources
#


def setup_app(app, api):
    """setup the resources urls."""
    api.add_resource(
        TagListResource,
        '/api/tags/'
    )
    api.add_resource(
        TagResource,
        '/api/tags/<string:tag_name>',
    )
    api.add_resource(
        RecordListTagResource,
        '/api/records/<int:record_id>/tags/'
    )
    api.add_resource(
        RecordTagResource,
        '/api/records/<int:record_id>/tags/<string:tag_name>'
    )
