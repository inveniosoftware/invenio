# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2015 CERN.
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

"""Deposit REST API."""

from functools import wraps

from cerberus import Validator
from flask import request
from flask_login import current_user
from flask_restful import Resource, abort, reqparse
from werkzeug.utils import secure_filename

from invenio.ext.restful import require_api_auth, error_codes, \
    require_oauth_scopes, require_header
from invenio.modules.access.engine import acc_authorize_action
from invenio.modules.deposit.models import Deposition, \
    DepositionFile, InvalidDepositionType, DepositionDoesNotExists, \
    DraftDoesNotExists, FormDoesNotExists, DepositionNotDeletable, \
    InvalidApiAction, FilenameAlreadyExists, \
    FileDoesNotExists, ForbiddenAction, DepositionError
from invenio.modules.deposit.storage import \
    DepositionStorage, UploadError


from .registry import deposit_default_type


class APIValidator(Validator):

    """Add new datatype 'raw', that accepts anything."""

    def _validate_type_any(self, field, value):
        pass


# Request parser
list_parser = reqparse.RequestParser()
list_parser.add_argument('state', type=str)
list_parser.add_argument('submitted', type=bool)
list_parser.add_argument('type', type=str)


draft_data_schema = dict(
    metadata=dict(type="dict"),
    completed=dict(type="boolean"),
)

draft_data_extended_schema = draft_data_schema.copy()
draft_data_extended_schema['type'] = dict(type="string")
draft_data_extended_schema['draft_id'] = dict(type="string")

file_schema = dict(
    filename=dict(type="string", minlength=1, maxlength=255),
)

file_schema_list = dict(
    id=dict(type="string"),
)


#
# Decorators
#
def error_handler(f):
    """Decorator to handle deposition exceptions."""
    @wraps(f)
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except DepositionDoesNotExists:
            abort(404, message="Deposition does not exist", status=404)
        except DraftDoesNotExists:
            abort(404, message="Draft does not exist", status=404)
        except InvalidApiAction:
            abort(404, message="Action does not exist", status=404)
        except DepositionNotDeletable:
            abort(403, message="Deposition is not deletable", status=403)
        except ForbiddenAction:
            abort(403, message="Forbidden", status=403)
        except InvalidDepositionType:
            abort(400, message="Invalid deposition type", status=400)
        except FormDoesNotExists:
            abort(400, message="Form does not exist", status=400)
        except FileDoesNotExists:
            abort(400, message="File does not exist", status=400)
        except FilenameAlreadyExists:
            abort(400, message="Filename already exist", status=400)
        except UploadError:
            abort(400)
        except DepositionError as e:
            if len(e.args) >= 1:
                abort(400, message=e.args[0], status=400)
            else:
                abort(500, message="Internal server error", status=500)
    return inner


def api_request_globals(f):
    """Set a variable in request to allow identification of API requests."""
    @wraps(f)
    def inner(*args, **kwargs):
        request.is_api_request = True
        return f(*args, **kwargs)
    return inner


def filter_draft_errors(result):
    """Extract error messages from a draft.process() result dictionary."""
    error_messages = []
    for field, msgs in result.get('messages', {}).items():
        if msgs.get('state', None) == 'error':
            for m in msgs['messages']:
                error_messages.append(dict(
                    field=field,
                    message=m,
                    code=error_codes['validation_error'],
                ))
    return error_messages


def filter_validation_errors(errors):
    """Extract error messages from Cerberus error dictionary."""
    error_messages = []
    for field, msgs in errors.items():
        if isinstance(msgs, dict):
            for f, m in msgs.items():
                error_messages.append(dict(
                    field=f,
                    message=m,
                    code=error_codes['validation_error'],
                ))
        else:
            error_messages.append(dict(
                field=field,
                message=msgs,
                code=error_codes['validation_error'],
            ))
    return error_messages


def can_access_deposit_type(type_):
    """Return True if current user can access given deposition type."""
    if type_ is None:
        default_type = deposit_default_type.get()
        type_ = default_type and default_type.get_identifier() or None
    return type_ in current_user.get('precached_allowed_deposition_types', [])


# =========
# Mix-ins
# =========
deposition_decorators = [
    require_api_auth(),
    error_handler,
    api_request_globals,
]


class InputProcessorMixin(object):

    """Mix-in class for validating and processing deposition input data."""

    input_schema = draft_data_extended_schema

    def validate_input(self, deposition, draft_id=None):
        """Validate input data for creating and update a deposition."""
        v = APIValidator()
        draft_id = draft_id or deposition.get_default_draft_id()
        metadata_schema = deposition.type.api_metadata_schema(draft_id)

        if metadata_schema:
            schema = self.input_schema.copy()
            schema['metadata'] = metadata_schema
        else:
            schema = self.input_schema

        # Either conform to dictionary schema or dictionary is empty
        if not v.validate(request.json, schema) and \
           request.json:
            abort(
                400,
                message="Bad request",
                status=400,
                errors=filter_validation_errors(v.errors),
            )

    def process_input(self, deposition, draft_id=None):
        """Process input data."""
        # If data provided, process it
        if request.json:
            if draft_id is None:
                # Defaults to `_default' draft id unless specified
                draft = deposition.get_or_create_draft(
                    request.json.get(
                        'draft_id',
                        deposition.get_default_draft_id()
                    )
                )
            else:
                draft = deposition.get_draft(draft_id)

            # Process data
            dummy_form, validated, result = draft.process(
                request.json.get('metadata', {}), complete_form=True
            )

            # Validation failed to abort
            if not validated:
                abort(
                    400,
                    message="Bad request",
                    status=400,
                    errors=filter_draft_errors(result),
                )

            if validated and request.json.get('completed', False):
                draft.complete()


# =========
# Resources
# =========
class DepositionListResource(Resource, InputProcessorMixin):

    """Collection of depositions."""

    method_decorators = deposition_decorators

    def get(self):
        """List depositions.

        :param type: Upload type identifier (optional)
        """
        args = list_parser.parse_args()
        result = Deposition.get_depositions(
            user=current_user, type=args['type'] or None
        )
        return map(lambda o: o.marshal(), result)

    @require_header('Content-Type', 'application/json')
    @require_oauth_scopes('deposit:write')
    def post(self):
        """Create a new deposition."""
        if not can_access_deposit_type(request.json.get('type', None)):
            raise ForbiddenAction('deposit_create_with_type')
        # Create deposition (uses default deposition type unless type is given)
        d = Deposition.create(current_user, request.json.get('type', None))
        # Validate input data according to schema
        self.validate_input(d)
        # Process input data
        self.process_input(d)
        # Save if all went fine
        d.save()
        return d.marshal(), 201

    def put(self):
        abort(405)

    def delete(self):
        abort(405)

    def head(self):
        abort(405)

    def options(self):
        abort(405)

    def patch(self):
        abort(405)


class DepositionResource(Resource, InputProcessorMixin):

    """Deposition item."""

    method_decorators = deposition_decorators

    def get(self, resource_id):
        """Get a deposition."""
        return Deposition.get(resource_id, user=current_user).marshal()

    def post(self, resource_id):
        abort(405)

    @require_header('Content-Type', 'application/json')
    @require_oauth_scopes('deposit:write')
    def put(self, resource_id):
        """Update a deposition."""
        d = Deposition.get(resource_id, user=current_user)
        self.validate_input(d)
        self.process_input(d)
        d.save()
        return d.marshal()

    @require_oauth_scopes('deposit:write')
    def delete(self, resource_id):
        """Delete existing deposition."""
        d = Deposition.get(resource_id, user=current_user)
        d.delete()
        return "", 204

    def head(self, resource_id):
        abort(405)

    def options(self, resource_id):
        abort(405)

    def patch(self, resource_id):
        abort(405)


class DepositionDraftListResource(Resource):

    """Deposition draft collection."""

    method_decorators = deposition_decorators

    def get(self, resource_id):
        """List all drafts."""
        d = Deposition.get(resource_id, user=current_user)
        return map(lambda x: d.type.marshal_draft(x), d.drafts_list)

    def post(self, resource_id):
        abort(405)

    def put(self, resource_id):
        abort(405)

    def delete(self, resource_id):
        abort(405)

    def head(self, resource_id):
        abort(405)

    def options(self, resource_id):
        abort(405)

    def patch(self, resource_id):
        abort(405)


class DepositionDraftResource(Resource, InputProcessorMixin):

    """Deposition draft item."""

    method_decorators = deposition_decorators
    input_schema = draft_data_schema

    def get(self, oauth, resource_id, draft_id):
        """Get a deposition draft."""
        d = Deposition.get(resource_id, user=current_user)
        return d.type.marshal_draft(d.get_draft(draft_id))

    def post(self, resource_id, draft_id):
        abort(405)

    @require_header('Content-Type', 'application/json')
    @require_oauth_scopes('deposit:write')
    def put(self, resource_id, draft_id):
        """Update a deposition draft."""
        d = Deposition.get(resource_id, user=current_user)
        self.validate_input(d, draft_id)
        self.process_input(d, draft_id)
        d.save()

    def delete(self, resource_id, draft_id):
        abort(405)

    def head(self, resource_id, draft_id):
        abort(405)

    def options(self, resource_id, draft_id):
        abort(405)

    def patch(self, resource_id, draft_id):
        abort(405)


class DepositionActionResource(Resource):

    """Representation of deposition action.

    Primarily used to execute the underlyinh workflow.
    """

    method_decorators = deposition_decorators

    def get(self, resource_id, action_id):
        abort(405)

    @require_oauth_scopes('deposit:actions')
    def post(self, resource_id, action_id):
        """Run an action."""
        d = Deposition.get(resource_id, user=current_user)
        return d.type.api_action(d, action_id)

    def put(self, resource_id, action_id):
        abort(405)

    def delete(self, resource_id, action_id):
        abort(405)

    def head(self, resource_id, action_id):
        abort(405)

    def options(self, resource_id, action_id):
        abort(405)

    def patch(self, resource_id, action_id):
        abort(405)


class DepositionFileListResource(Resource):

    """Represents a collection of deposition files."""

    method_decorators = deposition_decorators

    def get(self, resource_id):
        """Get deposition list of files."""
        d = Deposition.get(resource_id, user=current_user)
        return map(lambda f: d.type.marshal_file(f), d.files)

    @require_header('Content-Type', 'multipart/form-data')
    @require_oauth_scopes('deposit:write')
    def post(self, resource_id):
        """Upload a file."""
        d = Deposition.get(resource_id, user=current_user)

        # Bail-out early if not permitted (add_file will also check, but then
        # we already uploaded the file)
        if not d.authorize('add_file'):
            raise ForbiddenAction('add_file', d)

        uploaded_file = request.files['file']
        filename = secure_filename(
            request.form.get('filename') or uploaded_file.filename
        )

        df = DepositionFile(backend=DepositionStorage(d.id))

        if df.save(uploaded_file, filename=filename):
            try:
                d.add_file(df)
                d.save()
            except FilenameAlreadyExists as e:
                df.delete()
                raise e

        return d.type.marshal_file(df), 201

    @require_header('Content-Type', 'application/json')
    @require_oauth_scopes('deposit:write')
    def put(self, resource_id):
        """Sort files in collection."""
        if not isinstance(request.json, list):
            abort(
                400,
                message="Bad request",
                status=400,
                errors=[dict(
                    message="Expected a list",
                    code=error_codes["validation_error"],
                )],
            )

        v = APIValidator()
        for file_item in request.json:
            if not v.validate(file_item, file_schema_list):
                abort(
                    400,
                    message="Bad request",
                    status=400,
                    errors=map(lambda x: dict(
                        message=x,
                        code=error_codes["validation_error"]
                    ), v.errors),
                )

        d = Deposition.get(resource_id, user=current_user)

        for file_item in request.json:
            if not d.get_file(file_item['id']):
                raise FileDoesNotExists(file_item['id'])

        # Sort files raise ForbiddenAction if not authorized
        d.sort_files(map(lambda x: x['id'], request.json))
        d.save()
        return map(lambda f: d.type.marshal_file(f), d.files)

    def delete(self, resource_id):
        abort(405)

    def head(self, resource_id):
        abort(405)

    def options(self, resource_id):
        abort(405)

    def patch(self, resource_id):
        abort(405)


class DepositionFileResource(Resource):

    """Represent a deposition file."""

    method_decorators = deposition_decorators

    def get(self, resource_id, file_id):
        """Get a deposition file."""
        d = Deposition.get(resource_id, user=current_user)
        df = d.get_file(file_id)
        if df is None:
            abort(404, message="File does not exist", status=404)
        return d.type.marshal_file(df)

    @require_oauth_scopes('deposit:write')
    def delete(self, resource_id, file_id):
        """Delete existing deposition file."""
        d = Deposition.get(resource_id, user=current_user)

        # Sort files raise ForbiddenAction if not authorized
        df = d.remove_file(file_id)
        if df is None:
            abort(404, message="File does not exist", status=404)
        df.delete()
        d.save()
        return "", 204

    def post(self, resource_id, file_id):
        abort(405)

    @require_header('Content-Type', 'application/json')
    @require_oauth_scopes('deposit:write')
    def put(self, resource_id, file_id):
        """Update a deposition file - i.e. rename it."""
        v = APIValidator()
        if not v.validate(request.json, file_schema):
            abort(
                400,
                message="Bad request",
                status=400,
                errors=map(lambda x: dict(
                    message=x,
                    code=error_codes["validation_error"]
                ), v.errors),
            )

        d = Deposition.get(resource_id, user=current_user)
        df = d.get_file(file_id)

        if not d.type.authorize_file(d, df, 'update_metadata'):
            raise ForbiddenAction('update_metadata', df)

        new_name = secure_filename(request.json['filename'])
        if new_name != request.json['filename']:
            abort(
                400,
                message="Bad request",
                status=400,
                errors=[dict(
                    message="Not a valid filename",
                    code=error_codes["validation_error"]
                )],
            )

        df.name = new_name
        d.save()

        return d.type.marshal_file(df)

    def head(self, resource_id, file_id):
        abort(405)

    def options(self, resource_id, file_id):
        abort(405)

    def patch(self, resource_id, file_id):
        abort(405)


#
# Register API resources
#
def setup_app(app, api):
    api.add_resource(
        DepositionListResource,
        '/api/deposit/depositions/',
    )
    api.add_resource(
        DepositionResource,
        '/api/deposit/depositions/<string:resource_id>',
    )
    api.add_resource(
        DepositionFileListResource,
        '/api/deposit/depositions/<string:resource_id>/files/',
    )
    api.add_resource(
        DepositionDraftListResource,
        '/api/deposit/depositions/<string:resource_id>/metadata/',
    )
    api.add_resource(
        DepositionDraftResource,
        '/api/deposit/depositions/<string:resource_id>/metadata/'
        '<string:draft_id>',
    )
    api.add_resource(
        DepositionActionResource,
        '/api/deposit/depositions/<string:resource_id>/actions/'
        '<string:action_id>',
    )
    api.add_resource(
        DepositionFileResource,
        '/api/deposit/depositions/<string:resource_id>/files/<string:file_id>',
    )

    # Register scopes
    with app.app_context():
        from invenio.modules.oauth2server.models import Scope
        from invenio.modules.oauth2server.registry import scopes
        scopes.register(Scope(
            'deposit:write',
            group='Deposit',
            help_text='Allow upload (but not publishing).',
        ))
        scopes.register(Scope(
            'deposit:actions',
            group='Deposit',
            help_text='Allow publishing of uploads.',
        ))
