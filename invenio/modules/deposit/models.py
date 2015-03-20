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

"""Deposition data model classes.

Classes for wrapping BibWorkflowObject and friends to make it easier to
work with the data attributes.
"""

import json
import os
from datetime import datetime

from uuid import uuid4

from dateutil.tz import tzutc

from flask import current_app, flash, redirect, render_template, request, \
    session, url_for
from flask_login import current_user
from flask_restful import fields, marshal

from invenio.base.helpers import unicodifier
from invenio.ext.restful import UTCISODateTime

from invenio.ext.sqlalchemy import db
from invenio.modules.workflows.engine import WorkflowStatus
from invenio.modules.workflows.models import BibWorkflowObject, ObjectVersion, \
    Workflow

from sqlalchemy.orm.exc import NoResultFound

from werkzeug.datastructures import MultiDict
from werkzeug.utils import secure_filename

from .form import CFG_FIELD_FLAGS, DataExporter
from .signals import file_uploaded
from .storage import DepositionStorage, Storage


#
# Exceptions
#
class DepositionError(Exception):

    """Base class for deposition errors."""

    pass


class InvalidDepositionType(DepositionError):

    """Raise when a deposition type cannot be found."""

    pass


class InvalidDepositionAction(DepositionError):

    """Raise when deposition is in an invalid state for action."""

    pass


class DepositionDoesNotExists(DepositionError):

    """Raise when a deposition does not exists."""

    pass


class DraftDoesNotExists(DepositionError):

    """Raise when a draft does not exists."""

    pass


class FormDoesNotExists(DepositionError):

    """Raise when a draft does not exists."""

    pass


class FileDoesNotExists(DepositionError):

    """Raise when a draft does not exists."""

    pass


class DepositionNotDeletable(DepositionError):

    """Raise when a deposition cannot be deleted."""

    pass


class FilenameAlreadyExists(DepositionError):

    """Raise when an identical filename is already present in a deposition."""

    pass


class ForbiddenAction(DepositionError):

    """Raise when action on a deposition, draft or file is not authorized."""

    pass


class InvalidApiAction(DepositionError):

    """Raise when an invalid API action is requested."""

    pass


#
# Helpers
#
class FactoryMixin(object):

    """Mix-in class to help create objects from persisted object state."""

    @classmethod
    def factory(cls, state, *args, **kwargs):
        obj = cls(*args, **kwargs)
        obj.__setstate__(state)
        return obj


#
# Primary classes
#
class DepositionType(object):

    """
    A base class for the deposition types to ensure certain
    properties are defined on each type.

    A deposition type is just a BibWorkflow with a couple of extra methods.

    To customize rendering behavior of the workflow for a given deposition type
    you can override the render_error(), render_step() and render_completed()
    methods.
    """

    workflow = []
    """ Workflow definition """

    name = ""
    """ Display name for this deposition type """

    name_plural = ""
    """ Plural version of display name for this deposition type """

    enabled = False
    """ Determines if type is enabled - TODO: REMOVE"""

    default = False
    """
    Determines if type is the default - warnings are issed if conflicts exsists
    TODO: remove
    """

    deletable = False
    """
    Determine if a deposition is deletable after submission.
    """

    editable = False
    """
    Determine if a deposition is editable after submission.
    """

    stopable = False
    """
    Determine if a deposition workflow can be stopped (i.e. discard changes).
    """

    group = None
    """ Name of group to include this type in. """

    api = False
    """
    Determines if API is enabled for this type (requires workflow to be
    compatible with the API).
    """

    draft_definitions = {'_default': None}
    """
    Dictionary of all drafts for this deposition type
    """

    marshal_file_fields = dict(
        checksum=fields.String,
        filename=fields.String(attribute='name'),
        id=fields.String(attribute='uuid'),
        filesize=fields.String(attribute='size'),
    )
    """ REST API structure of a file """

    marshal_draft_fields = dict(
        metadata=fields.Raw(attribute='values'),
        completed=fields.Boolean,
        id=fields.String,
    )
    """ REST API structure of a draft """

    marshal_deposition_fields = dict(
        id=fields.Integer,
        title=fields.String,
        created=UTCISODateTime,
        modified=UTCISODateTime,
        owner=fields.Integer(attribute='user_id'),
        state=fields.String,
        submitted=fields.Boolean,
        files=fields.Nested(marshal_file_fields),
        drafts=fields.Nested(marshal_draft_fields, attribute='drafts_list'),
    )
    """ REST API structure of a deposition """

    @classmethod
    def default_draft_id(cls, deposition):
        return '_default'

    @classmethod
    def render_error(cls, dummy_deposition):
        """
        Render a page when deposition had an workflow error.

        Method can be overwritten by subclasses to provide custom
        user interface.
        """
        flash('%(name)s deposition has returned error.' %
              {'name': cls.name}, 'error')
        return redirect(url_for('.index'))

    @classmethod
    def render_step(self, deposition):
        """
        Render a page for a given deposition step.

        Method can be overwritten by subclasses to provide custom
        user interface.
        """
        ctx = deposition.get_render_context()
        if ctx:
            return render_template(**ctx)
        else:
            return render_template('deposit/error.html', **dict(
                depostion=deposition,
                deposition_type=(
                    None if deposition.type.is_default()
                    else deposition.type.get_identifier()
                ),
                uuid=deposition.id,
                my_depositions=Deposition.get_depositions(
                    current_user, type=deposition.type
                ),
            ))

    @classmethod
    def render_completed(cls, dummy_deposition):
        """
        Render page when deposition was successfully completed (i.e workflow
        just finished successfully).

        Method can be overwritten by subclasses to provide custom
        user interface.
        """
        flash('%(name)s was successfully finished.' %
              {'name': cls.name}, 'success')
        return redirect(url_for('.index'))

    @classmethod
    def render_final(cls, deposition):
        """
        Render page when deposition was *already* successfully completed (i.e
        a finished workflow is being executed a second time).

        This allows you render e.g. a preview of the record. The distinction
        between render_completed and render_final is primarily useful for the
        REST API (see api_final and api_completed)

        Method can be overwritten by subclasses to provide custom
        user interface.
        """
        return cls.render_completed(deposition)

    @classmethod
    def api_completed(cls, deposition):
        """
        Workflow just finished processing so return an 202 Accepted, since
        usually further background processing may happen.
        """
        return deposition.marshal(), 202

    @classmethod
    def api_final(cls, deposition):
        """
        Workflow already finished, and the user tries to re-execute the
        workflow, so send a 400 Bad Request back.
        """
        return dict(
            message="Deposition workflow already completed",
            status=400,
        ), 400

    @classmethod
    def api_step(cls, deposition):
        """
        Workflow was halted during processing. The workflow task that halted
        processing is expected to provide a response to send back to the
        client.

        The default response code is 500 Internal Server Error. A workflow task
        is expected to use Deposition.set_render_context() with a dictionary
        which is returned to the client. Set the key 'status', to change the
        status code, e.g.::

            d.set_render_context(dict(status=400, message="Bad request"))

        If no response is provided by the workflow task, it is regarded as
        an internal server error.
        """
        ctx = deposition.get_render_context()
        if ctx:
            return ctx.get('response', {}), ctx.get('status', 500)
        return cls.api_error(deposition)

    @classmethod
    def api_error(cls, deposition):
        return dict(message='Internal Server Error', status=500), 500

    @classmethod
    def api_action(cls, deposition, action_id):
        if action_id == 'run':
            return deposition.run_workflow(headless=True)
        elif action_id == 'reinitialize':
            deposition.reinitialize_workflow()
            return deposition.run_workflow(headless=True)
        elif action_id == 'stop':
            deposition.stop_workflow()
            return deposition.run_workflow(headless=True)
        raise InvalidApiAction(action_id)

    @classmethod
    def api_metadata_schema(cls, draft_id):
        """
        Get the input validation schema for this draft_id

        Allows you to override API defaults.
        """
        from wtforms.fields.core import FieldList, FormField

        if draft_id in cls.draft_definitions:
            schema = dict()
            formclass = cls.draft_definitions[draft_id]
            for fname, fclass in formclass()._fields.items():

                if isinstance(fclass, FieldList):
                    schema[fname] = dict(type='list')
                elif isinstance(fclass, FormField):
                    schema[fname] = dict(type='dict')
                else:
                    schema[fname] = dict(type='any')
            return dict(type='dict', schema=schema)
        return None

    @classmethod
    def marshal_deposition(cls, obj):
        """
        Generate a JSON representation for REST API of a Deposition
        """
        return marshal(obj, cls.marshal_deposition_fields)

    @classmethod
    def marshal_draft(cls, obj):
        """
        Generate a JSON representation for REST API of a DepositionDraft
        """
        return marshal(obj, cls.marshal_draft_fields)

    @classmethod
    def marshal_file(cls, obj):
        """
        Generate a JSON representation for REST API of a DepositionFile
        """
        return marshal(obj, cls.marshal_file_fields)

    @classmethod
    def authorize(cls, deposition, action):
        if action == 'create':
            return True  # Any authenticated user
        elif action == 'delete':
            if deposition.has_sip():
                return deposition.type.deletable
            return True
        elif action == 'reinitialize':
            return deposition.type.editable
        elif action == 'stop':
            return deposition.type.stopable
        elif action in ['add_file', 'remove_file', 'sort_files']:
            # Don't allow to add/remove/sort files after first submission
            return not deposition.has_sip()
        elif action in ['add_draft', ]:
            # Allow adding drafts when inprogress (independent of SIP exists
            # or not).
            return deposition.state == 'inprogress'
        else:
            return not deposition.has_sip()

    @classmethod
    def authorize_draft(cls, deposition, draft, action):
        if action == 'update':
            # If deposition allows adding  a draft, then allow editing the
            # draft.
            return cls.authorize(deposition, 'add_draft')
        return cls.authorize(deposition, 'add_draft')

    @classmethod
    def authorize_file(cls, deposition, deposition_file, action):
        return cls.authorize(deposition, 'add_file')

    @classmethod
    def get_identifier(cls):
        """ Get type identifier (identical to workflow name) """
        return cls.__name__

    @classmethod
    def is_enabled(cls):
        """ Check if workflow is enabled """
        # Wrapping in a method to eventually allow enabling/disabling
        # via configuration.
        return cls.enabled

    @classmethod
    def is_default(cls):
        """ Check if workflow is the default """
        # Wrapping in a method to eventually allow configuration
        # via configuration.
        return cls.default

    @classmethod
    def run_workflow(cls, deposition):
        """
        Run workflow for the given BibWorkflowObject.

        Usually not invoked directly, but instead indirectly through
        Deposition.run_workflow().
        """
        if deposition.workflow_object.workflow is None or (
                deposition.workflow_object.version == ObjectVersion.INITIAL
                and
                deposition.workflow_object.workflow.status ==
                WorkflowStatus.NEW):
            return deposition.workflow_object.start_workflow(
                workflow_name=cls.get_identifier(),
                id_user=deposition.workflow_object.id_user,
                module_name="webdeposit"
            )
        else:
            return deposition.workflow_object.continue_workflow(
                start_point="restart_task",
            )

    @classmethod
    def reinitialize_workflow(cls, deposition):
        # Only reinitialize if really needed (i.e. you can only
        # reinitialize a fully completed workflow).
        wo = deposition.workflow_object
        if wo.version == ObjectVersion.COMPLETED and \
           wo.workflow.status == WorkflowStatus.COMPLETED:

            wo.version = ObjectVersion.INITIAL
            wo.workflow.status = WorkflowStatus.NEW

            # Clear deposition drafts
            deposition.drafts = {}

    @classmethod
    def stop_workflow(cls, deposition):
        # Only stop workflow if really needed
        wo = deposition.workflow_object
        if wo.version != ObjectVersion.COMPLETED and \
           wo.workflow.status != WorkflowStatus.COMPLETED:

            # Only workflows which has been fully completed once before
            # can be stopped
            if deposition.has_sip():
                wo.version = ObjectVersion.COMPLETED
                wo.workflow.status = WorkflowStatus.COMPLETED

                # Clear all drafts
                deposition.drafts = {}

                # Set title - FIXME: find better way to set title
                sip = deposition.get_latest_sip(sealed=True)
                title = sip.metadata.get('title', 'Untitled')
                deposition.title = title

    @classmethod
    def all(cls):
        """ Get a dictionary of deposition types """
        from .registry import deposit_types
        return deposit_types.mapping()

    @classmethod
    def get(cls, identifier):
        try:
            return cls.all()[identifier]
        except KeyError:
            raise InvalidDepositionType(identifier)

    @classmethod
    def keys(cls):
        """ Get a list of deposition type names """
        return cls.all().keys()

    @classmethod
    def values(cls):
        """ Get a list of deposition type names """
        return cls.all().values()

    @classmethod
    def get_default(cls):
        """ Get a list of deposition type names """
        from .registry import deposit_default_type
        return deposit_default_type.get()

    def __unicode__(self):
        """ Return a name for this class """
        return self.get_identifier()

    @classmethod
    def all_authorized(cls, user_info=None):
        """
        Return a dict of deposit types that the current user
        is allowed to view.
        """
        user_info = user_info or current_user

        all_types = cls.all()
        auth_types = user_info.get('precached_allowed_deposition_types', set())

        return {key: all_types[key] for key in auth_types if key in all_types}


class DepositionFile(FactoryMixin):

    """
    Represents an uploaded file

    Creating a normal deposition file::

        uploaded_file = request.files['file']
        filename = secure_filename(uploaded_file.filename)
        backend = DepositionStorage(deposition_id)

        d = DepositionFile(backend=backend)
        d.save(uploaded_file, filename)

    Creating a chunked deposition file::

        uploaded_file = request.files['file']
        filename = secure_filename(uploaded_file.filename)
        chunk = request.files['chunk']
        chunks = request.files['chunks']
        backend = ChunkedDepositionStorage(deposition_id)

        d = DepositionFile(id=file_id, backend=backend)
        d.save(uploaded_file, filename, chunk, chunks)
        if chunk == chunks:
            d.save(finish=True, filename=filename)

    Reading a file::

        d = DepositionFile.from_json(data)

        if d.is_local():
            send_file(d.get_syspath())
        else:
            redirect(d.get_url())

        d.delete()

    Deleting a file::

        d = DepositionFile.from_json(data)
        d.delete()

    """

    def __init__(self, uuid=None, backend=None):
        self.uuid = uuid or str(uuid4())
        self._backend = backend
        self.name = ''

    def __getstate__(self):
        # TODO: Add content_type attributes
        return dict(
            id=self.uuid,
            path=self.path,
            name=self.name,
            size=self.size,
            checksum=self.checksum,
            #bibdoc=self.bibdoc
        )

    def __setstate__(self, state):
        self.uuid = state['id']
        self._path = state['path']
        self.name = state['name']
        self.size = state['size']
        self.checksum = state['checksum']

    def __repr__(self):
        data = self.__getstate__()
        del data['path']
        return json.dumps(data)

    @property
    def backend(self):
        if not self._backend:
            self._backend = Storage(None)
        return self._backend

    @property
    def path(self):
        if self._path is None:
            raise Exception("No path set")
        return self._path

    def save(self, incoming_file, filename=None, *args, **kwargs):
        self.name = secure_filename(filename or incoming_file.filename)
        (self._path, self.size, self.checksum, result) = self.backend.save(
            incoming_file, filename, *args, **kwargs
        )
        return result

    def delete(self):
        """ Delete the file on storage """
        return self.backend.delete(self.path)

    def is_local(self):
        """ Determine if file is a local file """
        return self.backend.is_local(self.path)

    def get_url(self):
        """ Get a URL for the file """
        return self.backend.get_url(self.path)

    def get_syspath(self):
        """ Get a local system path to the file """
        return self.backend.get_syspath(self.path)


class DepositionDraftCacheManager(object):
    """
    Draft cache manager takes care of storing draft values in the cache prior
    to a workflow being run. The data can be loaded by the prefill_draft()
    workflow task.
    """
    def __init__(self, user_id):
        self.user_id = user_id
        self.data = {}

    @classmethod
    def from_request(cls):
        """
        Create a new draft cache from the current request.
        """
        obj = cls(current_user.get_id())

        # First check if we can get it via a json
        data = request.get_json(silent=True)
        if not data:
            # If, not simply merge all both query parameters and request body
            # parameters.
            data = request.values.to_dict()
        obj.data = data
        return obj

    @classmethod
    def get(cls):
        obj = cls(current_user.get_id())
        obj.load()
        return obj

    def save(self):
        """ Save data to session """
        if self.has_data():
            session['deposit_prefill'] = self.data
            session.modified = True
        else:
            self.delete()

    def load(self):
        """ Load data from session """
        self.data = session.get('deposit_prefill', {})

    def delete(self):
        """ Delete data in session """
        if 'deposit_prefill' in session:
            del session['deposit_prefill']
            session.modified = True

    def has_data(self):
        """
        Determine if the cache has data.
        """
        return bool(self.data)

    def fill_draft(self, deposition, draft_id, clear=True):
        """
        Fill a draft with cached draft values
        """
        draft = deposition.get_or_create_draft(draft_id)
        draft.process(self.data)

        if clear:
            self.data = {}
            self.delete()
        return draft


class DepositionDraft(FactoryMixin):
    """
    Represents the state of a form
    """
    def __init__(self, draft_id, form_class=None, deposition_ref=None):
        self.id = draft_id
        self.completed = False
        self.form_class = form_class
        self.values = {}
        self.flags = {}
        self._form = None
        # Back reference to the depositions
        self._deposition_ref = deposition_ref
        self.validate = False

    def __getstate__(self):
        return dict(
            completed=self.completed,
            values=self.values,
            flags=self.flags,
            validate=self.validate,
        )

    def __setstate__(self, state):
        self.completed = state['completed']
        self.form_class = None
        if self._deposition_ref:
            self.form_class = self._deposition_ref.type.draft_definitions.get(
                self.id
            )
        self.values = state['values']
        self.flags = state['flags']
        self.validate = state.get('validate', True)

    def is_completed(self):
        return self.completed

    def has_form(self):
        return self.form_class is not None

    def authorize(self, action):
        if not self._deposition_ref:
            return True  # Not connected to deposition so authorize anything.
        return self._deposition_ref.type.authorize_draft(
            self._deposition_ref, self, action
        )

    def complete(self):
        """
        Set state of draft to completed.
        """
        self.completed = True

    def update(self, form):
        """
        Update draft values and flags with data from form.
        """
        data = dict((key, value) for key, value in form.data.items()
                    if value is not None)

        self.values = data
        self.flags = form.get_flags()

    def process(self, data, complete_form=False):
        """
        Process, validate and store incoming form data and return response.
        """
        if not self.authorize('update'):
            raise ForbiddenAction('update', self)

        if not self.has_form():
            raise FormDoesNotExists(self.id)

        # The form is initialized with form and draft data. The original
        # draft_data is accessible in Field.object_data, Field.raw_data is the
        # new form data and Field.data is the processed form data or the
        # original draft data.
        #
        # Behind the scences, Form.process() is called, which in turns call
        # Field.process_data(), Field.process_formdata() and any filters
        # defined.
        #
        # Field.object_data contains the value of process_data(), while
        # Field.data contains the value of process_formdata() and any filters
        # applied.
        form = self.get_form(formdata=data)

        # Run form validation which will call Field.pre_valiate(),
        # Field.validators, Form.validate_<field>() and Field.post_validate().
        # Afterwards Field.data has been validated and any errors will be
        # present in Field.errors.
        validated = form.validate()

        # Call Form.run_processors() which in turn will call
        # Field.run_processors() that allow fields to set flags (hide/show)
        # and values of other fields after the entire formdata has been
        # processed and validated.
        validated_flags, validated_data, validated_msgs = (
            form.get_flags(), form.data, form.messages
        )
        form.post_process(formfields=[] if complete_form else data.keys())
        post_processed_flags, post_processed_data, post_processed_msgs = (
            form.get_flags(), form.data, form.messages
        )

        # Save form values
        self.update(form)

        # Build result dictionary
        process_field_names = None if complete_form else data.keys()

        # Determine if some fields where changed during post-processing.
        changed_values = dict(
            (name, value) for name, value in post_processed_data.items()
            if validated_data[name] != value
        )

        # Determine changed flags
        changed_flags = dict(
            (name, flags) for name, flags in post_processed_flags.items()
            if validated_flags.get(name, []) != flags
        )
        # Determine changed messages
        changed_msgs = dict(
            (name, messages) for name, messages in post_processed_msgs.items()
            if validated_msgs.get(name, []) != messages
            or process_field_names is None or name in process_field_names
        )

        result = {}

        if changed_msgs:
            result['messages'] = changed_msgs
        if changed_values:
            result['values'] = changed_values
        if changed_flags:
            for flag in CFG_FIELD_FLAGS:
                fields = [
                    (name, flag in field_flags)
                    for name, field_flags in changed_flags.items()
                ]
                result[flag + '_on'] = map(
                    lambda x: x[0], filter(lambda x: x[1], fields)
                )
                result[flag + '_off'] = map(
                    lambda x: x[0], filter(lambda x: not x[1], fields)
                )

        return form, validated, result

    def get_form(self, formdata=None, load_draft=True,
                 validate_draft=False):
        """
        Create form instance with draft data and form data if provided.

        :param formdata: Incoming form data.
        :param files: Files to ingest into form
        :param load_draft: True to initialize form with draft data.
        :param validate_draft: Set to true to validate draft data, when no form
             data is provided.
        """
        if not self.has_form():
            raise FormDoesNotExists(self.id)

        # If a field is not present in formdata, Form.process() will assume it
        # is blank instead of using the draft_data value. Most of the time we
        # are only submitting a single field in JSON via AJAX requests. We
        # therefore reset non-submitted fields to the draft_data value with
        # form.reset_field_data().

        # WTForms deal with unicode - we deal with UTF8 so convert all
        draft_data = unicodifier(self.values) if load_draft else {}
        formdata = MultiDict(formdata or {})

        form = self.form_class(
            formdata=formdata, **draft_data
        )
        if formdata:
            form.reset_field_data(exclude=formdata.keys())

        # Set field flags
        if load_draft and self.flags:
            form.set_flags(self.flags)

        # Ingest files in form
        if self._deposition_ref:
            form.files = self._deposition_ref.files
        else:
            form.files = []

        if validate_draft and draft_data and formdata is None:
            form.validate()

        return form

    @classmethod
    def merge_data(cls, drafts):
        """
        Merge data of multiple drafts

        Duplicate keys will be overwritten without warning.
        """
        data = {}
        # Don't include *) disabled fields, and *) empty optional fields
        func = lambda f: not f.flags.disabled and (f.flags.required or f.data)

        for d in drafts:
            if d.has_form():
                visitor = DataExporter(
                    filter_func=func
                )
                visitor.visit(d.get_form())
                data.update(visitor.data)
            else:
                data.update(d.values)

        return data


class Deposition(object):
    """
    Wraps a BibWorkflowObject

    Basically an interface to work with BibWorkflowObject data attribute in an
    easy manner.
    """
    def __init__(self, workflow_object, type=None, user_id=None):
        self.workflow_object = workflow_object
        if not workflow_object:
            self.files = []
            self.drafts = {}
            self.type = self.get_type(type)
            self.title = ''
            self.sips = []

            self.workflow_object = BibWorkflowObject.create_object(
                id_user=user_id,
            )
            # Ensure default data is set for all objects.
            self.update()
        else:
            self.__setstate__(workflow_object.get_data())
        self.engine = None

    #
    # Properties proxies to BibWorkflowObject
    #
    @property
    def id(self):
        return self.workflow_object.id

    @property
    def user_id(self):
        return self.workflow_object.id_user

    @user_id.setter
    def user_id(self, value):
        self.workflow_object.id_user = value
        self.workflow_object.workflow.id_user = value

    @property
    def created(self):
        return self.workflow_object.created

    @property
    def modified(self):
        return self.workflow_object.modified

    @property
    def drafts_list(self):
        # Needed for easy marshaling by API
        return self.drafts.values()

    #
    # Proxy methods
    #
    def authorize(self, action):
        """
        Determine if certain action is authorized

        Delegated to deposition type to allow overwriting default behavior.
        """
        return self.type.authorize(self, action)

    #
    #  Serialization related methods
    #
    def marshal(self):
        """
        API representation of an object.

        Delegated to the DepositionType, to allow overwriting default
        behaviour.
        """
        return self.type.marshal_deposition(self)

    def __getstate__(self):
        """
        Serialize deposition state for storing in the BibWorkflowObject
        """
        # The bibworkflow object id and owner is implicit, as the Deposition
        # object only wraps the data attribute of a BibWorkflowObject.

        # FIXME: Find better solution for setting the title.
        for d in self.drafts.values():
            if 'title' in d.values:
                self.title = d.values['title']
                break

        return dict(
            type=self.type.get_identifier(),
            title=self.title,
            files=[f.__getstate__() for f in self.files],
            drafts=dict(
                [(d_id, d.__getstate__()) for d_id, d in self.drafts.items()]
            ),
            sips=[f.__getstate__() for f in self.sips],
        )

    def __setstate__(self, state):
        """
        Deserialize deposition from state stored in BibWorkflowObject
        """
        self.type = DepositionType.get(state['type'])
        self.title = state['title']
        self.files = [
            DepositionFile.factory(
                f_state,
                uuid=f_state['id'],
                backend=DepositionStorage(self.id),
            )
            for f_state in state['files']
        ]
        self.drafts = dict(
            [(d_id, DepositionDraft.factory(d_state, d_id,
                                            deposition_ref=self))
             for d_id, d_state in state['drafts'].items()]
        )
        self.sips = [
            SubmissionInformationPackage.factory(s_state, uuid=s_state['id'])
            for s_state in state.get('sips', [])
        ]

    #
    # Persistence related methods
    #
    def update(self):
        """
        Update workflow object with latest data.
        """
        data = self.__getstate__()
        # BibWorkflow calls get_data() before executing any workflow task, and
        # and calls set_data() after. Hence, unless we update the data
        # attribute it will be overwritten.
        try:
            self.workflow_object.data = data
        except AttributeError:
            pass
        self.workflow_object.set_data(data)

    def reload(self):
        """
        Get latest data from workflow object
        """
        self.__setstate__(self.workflow_object.get_data())

    def save(self):
        """
        Save the state of the deposition.

        Uses the __getstate__ method to make a JSON serializable
        representation which, sets this as data on the workflow object
        and saves it.
        """
        self.update()
        self.workflow_object.save()

    def delete(self):
        """
        Delete the current deposition
        """
        if not self.authorize('delete'):
            raise DepositionNotDeletable(self)

        for f in self.files:
            f.delete()

        if self.workflow_object.id_workflow:
            Workflow.delete(uuid=self.workflow_object.id_workflow)

            BibWorkflowObject.query.filter_by(
                id_workflow=self.workflow_object.id_workflow
            ).delete()
        else:
            db.session.delete(self.workflow_object)
        db.session.commit()

    #
    # Workflow execution
    #
    def run_workflow(self, headless=False):
        """
        Execute the underlying workflow

        If you made modifications to the deposition you must save if before
        running the workflow, using the save() method.
        """
        if self.workflow_object.workflow is not None:
            current_status = self.workflow_object.workflow.status
            if current_status == WorkflowStatus.COMPLETED:
                return self.type.api_final(self) if headless \
                    else self.type.render_final(self)

        self.update()
        self.engine = self.type.run_workflow(self)
        self.reload()
        status = self.engine.status

        if status == WorkflowStatus.ERROR:
            return self.type.api_error(self) if headless else \
                self.type.render_error(self)
        elif status != WorkflowStatus.COMPLETED:
            return self.type.api_step(self) if headless else \
                self.type.render_step(self)
        elif status == WorkflowStatus.COMPLETED:
            return self.type.api_completed(self) if headless else \
                self.type.render_completed(self)

    def reinitialize_workflow(self):
        """
        Reinitialize a workflow object (i.e. prepare it for editing)
        """
        if self.state != 'done':
            raise InvalidDepositionAction("Action only allowed for "
                                          "depositions in state 'done'.")

        if not self.authorize('reinitialize'):
            raise ForbiddenAction('reinitialize', self)

        self.type.reinitialize_workflow(self)

    def stop_workflow(self):
        """
        Stop a running workflow object (e.g. discard changes while editing).
        """
        if self.state != 'inprogress' or not self.submitted:
            raise InvalidDepositionAction("Action only allowed for "
                                          "depositions in state 'inprogress'.")

        if not self.authorize('stop'):
            raise ForbiddenAction('stop', self)

        self.type.stop_workflow(self)

    def set_render_context(self, ctx):
        """
        Set rendering context - used in workflow tasks to set what is to be
        rendered (either by API or UI)
        """
        self.workflow_object.deposition_context = ctx

    def get_render_context(self):
        """
        Get rendering context - used by DepositionType.render_step/api_step
        """
        return getattr(self.workflow_object, 'deposition_context', {})

    @property
    def state(self):
        """
        Return simplified workflow state - inprogress, done or error
        """
        try:
            status = self.workflow_object.workflow.status
            if status == WorkflowStatus.ERROR:
                return "error"
            elif status == WorkflowStatus.COMPLETED:
                return "done"
        except AttributeError:
            pass
        return "inprogress"

    #
    # Draft related methods
    #
    def get_draft(self, draft_id):
        """
        Get draft
        """
        if draft_id not in self.drafts:
            raise DraftDoesNotExists(draft_id)
        return self.drafts[draft_id]

    def get_or_create_draft(self, draft_id):
        """
        Get or create a draft for given draft_id
        """
        if draft_id not in self.drafts:
            if draft_id not in self.type.draft_definitions:
                raise DraftDoesNotExists(draft_id)

            if not self.authorize('add_draft'):
                raise ForbiddenAction('add_draft', self)

            self.drafts[draft_id] = DepositionDraft(
                draft_id,
                form_class=self.type.draft_definitions[draft_id],
                deposition_ref=self,
            )
        return self.drafts[draft_id]

    def get_default_draft_id(self):
        """
        Get the default draft id for this deposition.
        """
        return self.type.default_draft_id(self)

    #
    # Submission information package related methods
    #
    def get_latest_sip(self, sealed=None):
        """
        Get the latest submission information package

        :param sealed: Set to true to only returned latest sealed SIP. Set to
            False to only return latest unsealed SIP.
        """
        if len(self.sips) > 0:
            for sip in reversed(self.sips):
                if sealed is None:
                    return sip
                elif sealed and sip.is_sealed():
                    return sip
                elif not sealed and not sip.is_sealed():
                    return sip
        return None

    def create_sip(self):
        """
        Create a new submission information package (SIP) with metadata from
        the drafts.
        """
        metadata = DepositionDraft.merge_data(self.drafts.values())
        metadata['files'] = map(
            lambda x: dict(path=x.path, name=os.path.splitext(x.name)[0]),
            self.files
        )

        sip = SubmissionInformationPackage(metadata=metadata)
        self.sips.append(sip)

        return sip

    def has_sip(self, sealed=True):
        """
        Determine if deposition has a sealed submission information package.
        """
        for sip in self.sips:
            if (sip.is_sealed() and sealed) or \
               (not sealed and not sip.is_sealed()):
                return True
        return False

    @property
    def submitted(self):
        return self.has_sip()

    #
    # File related methods
    #
    def get_file(self, file_id):
        for f in self.files:
            if f.uuid == file_id:
                return f
        return None

    def add_file(self, deposition_file):
        if not self.authorize('add_file'):
            raise ForbiddenAction('add_file', self)

        for f in self.files:
            if f.name == deposition_file.name:
                raise FilenameAlreadyExists(deposition_file.name)
        self.files.append(deposition_file)
        file_uploaded.send(
            self.type.get_identifier(),
            deposition=self,
            deposition_file=deposition_file,
        )

    def remove_file(self, file_id):
        if not self.authorize('remove_file'):
            raise ForbiddenAction('remove_file', self)

        idx = None
        for i, f in enumerate(self.files):
            if f.uuid == file_id:
                idx = i

        if idx is not None:
            return self.files.pop(idx)
        return None

    def sort_files(self, file_id_list):
        """
        Order the files according the list of ids provided to this function.
        """
        if not self.authorize('sort_files'):
            raise ForbiddenAction('sort_files', self)

        search_dict = dict(
            [(f, i) for i, f in enumerate(file_id_list)]
        )

        def _sort_files_cmp(f_x, f_y):
            i_x = search_dict.get(f_x.uuid, None)
            i_y = search_dict.get(f_y.uuid, None)
            if i_x == i_y:
                return 0
            elif i_x is None or i_x > i_y:
                return 1
            elif i_y is None or i_x < i_y:
                return -1

        self.files = sorted(self.files, _sort_files_cmp)

    #
    # Class methods
    #
    @classmethod
    def get_type(self, type_or_id):
        if type_or_id and isinstance(type_or_id, type) and \
           issubclass(type_or_id, DepositionType):
                return type_or_id
        else:
            return DepositionType.get(type_or_id) if type_or_id else \
                DepositionType.get_default()

    @classmethod
    def create(cls, user, type=None):
        """
        Create a new deposition object.

        To persist the deposition, you must call save() on the created object.
        If no type is defined, the default deposition type will be assigned.

        @param user: The owner of the deposition
        @param type: Deposition type identifier.
        """
        t = cls.get_type(type)

        if not t.authorize(None, 'create'):
            raise ForbiddenAction('create')

        # Note: it is correct to pass 'type' and not 't' below to constructor.
        obj = cls(None, type=type, user_id=user.get_id())
        return obj

    @classmethod
    def get(cls, object_id, user=None, type=None):
        """
        Get the deposition with specified object id.

        @param object_id: The BibWorkflowObject id.
        @param user: Owner of the BibWorkflowObject
        @param type: Deposition type identifier.
        """
        if type:
            type = DepositionType.get(type)

        try:
            workflow_object = BibWorkflowObject.query.filter(
                BibWorkflowObject.id == object_id,
                # id_user!=0 means current version, as opposed to some snapshot
                # version.
                BibWorkflowObject.id_user != 0,
            ).one()
        except NoResultFound:
            raise DepositionDoesNotExists(object_id)

        if user and workflow_object.id_user != user.get_id():
            raise DepositionDoesNotExists(object_id)

        obj = cls(workflow_object)
        if type and obj.type != type:
            raise DepositionDoesNotExists(object_id, type)
        return obj

    @classmethod
    def get_depositions(cls, user=None, type=None):
        params = [
            Workflow.module_name == 'webdeposit',
        ]

        if user:
            params.append(BibWorkflowObject.id_user == user.get_id())
        else:
            params.append(BibWorkflowObject.id_user != 0)

        if type:
            params.append(Workflow.name == type.get_identifier())

        objects = BibWorkflowObject.query.join("workflow").options(
            db.contains_eager('workflow')).filter(*params).order_by(
            BibWorkflowObject.modified.desc()).all()

        def _create_obj(o):
            try:
                obj = cls(o)
            except InvalidDepositionType as err:
                current_app.logger.exception(err)
                return None
            if type is None or obj.type == type:
                return obj
            return None

        return filter(lambda x: x is not None, map(_create_obj, objects))


class SubmissionInformationPackage(FactoryMixin):

    """Submission information package (SIP).

    :param uuid: Unique identifier for this SIP
    :param metadata: Metadata in JSON for this submission information package
    :param package: Full generated metadata for this package (i.e. normally
        MARC for records, but could anything).
    :param timestamp: UTC timestamp in ISO8601 format of when package was
        sealed.
    :param agents: List of agents for this package (e.g. creator, ...)
    :param task_ids: List of task ids submitted to ingest this package (may be
        appended to after SIP has been sealed).
    """

    def __init__(self, uuid=None, metadata={}):
        self.uuid = uuid or str(uuid4())
        self.metadata = metadata
        self.package = ""
        self.timestamp = None
        self.agents = []
        self.task_ids = []

    def __getstate__(self):
        return dict(
            id=self.uuid,
            metadata=self.metadata,
            package=self.package,
            timestamp=self.timestamp,
            task_ids=self.task_ids,
            agents=[a.__getstate__() for a in self.agents],
        )

    def __setstate__(self, state):
        self.uuid = state['id']
        self._metadata = state.get('metadata', {})
        self.package = state.get('package', None)
        self.timestamp = state.get('timestamp', None)
        self.agents = [Agent.factory(a_state)
                       for a_state in state.get('agents', [])]
        self.task_ids = state.get('task_ids', [])

    def seal(self):
        self.timestamp = datetime.now(tzutc()).isoformat()

    def is_sealed(self):
        return self.timestamp is not None

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        import datetime
        import json

        class DateTimeEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, (datetime.datetime, datetime.date)):
                    encoded_object = obj.isoformat()
                else:
                    encoded_object = json.JSONEncoder.default(self, obj)
                return encoded_object

        data = json.dumps(value, cls=DateTimeEncoder)
        self._metadata = json.loads(data)


class Agent(FactoryMixin):

    """Agent."""

    def __init__(self, role=None, from_request_context=False):
        self.role = role
        self.user_id = None
        self.ip_address = None
        self.email_address = None
        if from_request_context:
            self.from_request_context()

    def __getstate__(self):
        return dict(
            role=self.role,
            user_id=self.user_id,
            ip_address=self.ip_address,
            email_address=self.email_address,
        )

    def __setstate__(self, state):
        self.role = state['role']
        self.user_id = state['user_id']
        self.ip_address = state['ip_address']
        self.email_address = state['email_address']

    def from_request_context(self):
        from flask import request
        from invenio.ext.login import current_user
        self.ip_address = request.remote_addr
        self.user_id = current_user.get_id()
        self.email_address = current_user.info.get('email', '')
