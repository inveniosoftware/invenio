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

"""Restful API for records."""


from functools import wraps
import json

from flask import make_response
from flask.ext.login import current_user
from flask.ext.restful import abort, Resource
from flask import request
from invenio.ext.restful import require_api_auth, pagination
from invenio.modules.formatter.models import Format
from invenio.modules.formatter import format_record
from .errors import RecordError, RecordNotFoundError, RecordDeletedError, \
    RecordForbiddenViewError, RecordUnsuppotedMediaTypeError


def error_handler(f):
    @wraps(f)
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except (RecordForbiddenViewError,
                RecordNotFoundError,
                RecordUnsuppotedMediaTypeError,
                RecordDeletedError) as e:
            abort(e.status, message=e.message, status=e.status)
        except RecordError as e:
            if len(e.args) >= 1:
                abort(400, message=e.args[0], status=400)
            else:
                abort(500, message="Internal server error", status=500)
    return inner


class BaseRecordResource(Resource):
    def __init__(self):
        self.representations = {}
        # get all mime-types that are not None
        self.mimetypes = dict([(f.mime_type, f.code) for f in Format.query.all()
                               if f.mime_type is not None])

        for mime_type in self.mimetypes.keys():
            self.representations[mime_type] = (
                lambda r, s, h:  make_response(r, s, h)
            )

    def get_output_format(self):
        # Check requested output format.
        # Set default mime type if 'Accept' is not in headers.
        given_mimetype = request.headers.get('Accept', 'application/json')

        for t in given_mimetype.split(","):
            output_format = self.mimetypes.get(t.split(';')[0])
            if output_format is not None:
                return output_format

        raise RecordUnsuppotedMediaTypeError(
            message="Output format(s) {} are/is not supported.".format(
                given_mimetype
            )
        )


class RecordResource(BaseRecordResource):

    """The record resource."""

    method_decorators = [
        #require_api_auth(),
        error_handler
    ]

    def get(self, record_id):
        from invenio.legacy.search_engine import record_exists, \
            check_user_can_view_record

        # Get output format
        output_format = self.get_output_format()

        # Check record's existence
        record_status = record_exists(record_id)
        if record_status == 0:
            raise RecordNotFoundError(
                message="Record {} does not exist.".format(record_id),
            )
        elif record_status == -1:
            raise RecordDeletedError(
                message="Record {} was deleted.".format(record_id),
            )

        # Check record's access
        (auth_code, auth_mesg) = check_user_can_view_record(
            current_user,
            record_id
        )
        if auth_code == 1:
            raise RecordForbiddenViewError(
                message="Access to record {} is forbidden.".format(record_id),
            )

        # Return record with requested output format.
        result = format_record(recID=record_id, of=output_format)
        return (result, 200)

    def post(self, record_id):
        abort(405)

    def head(self, record_id):
        abort(405)

    def put(self, record_id):
        abort(405)

    def patch(self, record_id):
        abort(405)

    def options(self, record_id):
        abort(405)


class RecordListResource(BaseRecordResource):

    method_decorators = [
        #require_api_auth(),
        error_handler
    ]

    def get(self):
        # Temporarily disable search until fully tested.
        abort(405)

        from invenio.legacy.search_engine import perform_request_search, \
            record_exists, check_user_can_view_record

        given_mimetype = request.headers.get('Accept', 'application/json')
        output_format = self.mimetypes.get(given_mimetype)
        if output_format is None:
            raise RecordUnsuppotedMediaTypeError(
                message="Output format {} is not supported.".format(
                    given_mimetype
                ))

        # get URL parameters
        query = request.args.get('query', '')
        sort_field = request.args.get('sort_field', 'title')
        sort_order = request.args.get('sort_order', 'a')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 5))

        if page < 0:
            raise RecordError(
                message="Invalid page {}".format(page),
                status=400
            )

        if per_page < 0:
            raise RecordError(
                message="Invalid per_page {}".format(per_page),
                status=400
            )

        rec_ids = perform_request_search(p=query, sf=sort_field,
                                         so=sort_order, of='id')
        rec_ids_to_keep = []
        for recid in rec_ids:
            if record_exists(recid) > 0:
                (auth_code, auth_mesg) = check_user_can_view_record(
                    current_user, recid)
                if auth_code == 0:
                    rec_ids_to_keep.append(recid)
        records_in_requested_format = []
        if rec_ids_to_keep:
            for recid in rec_ids_to_keep:
                result = format_record(recID=recid, of=output_format)
                records_in_requested_format.append(result)

        records_to_return = []
        headers = {}
        if records_in_requested_format:
            p = pagination.RestfulPagination(
                page=page,
                per_page=per_page,
                total_count=len(records_in_requested_format)
            )
            if (page > p.pages):
                raise RecordError(
                    message="Invalid page {}".format(page),
                    status=400
                )
            records_to_return = p.slice(records_in_requested_format)
            kwargs = {}
            kwargs['endpoint'] = request.endpoint
            kwargs['args'] = request.args
            link_header = p.link_header(**kwargs)
            headers[link_header[0]] = link_header[1]
        return (json.dumps(records_to_return), 200, headers)

    def post(self):
        abort(405)

    def head(self):
        abort(405)

    def put(self, record_id):
        abort(405)

    def patch(self, record_id):
        abort(405)

    def options(self, record_id):
        abort(405)


def setup_app(app, api):
    """setup the resources urls."""
    api.add_resource(
        RecordResource,
        '/api/records/<int:record_id>'
    )
    api.add_resource(
        RecordListResource,
        '/api/records/'
    )
