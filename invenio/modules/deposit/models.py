# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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
"""
Classes for wrapping BibWorkflowObject and friends to make it easier to
work with the data attributes.
"""

from uuid import uuid4
import json
import os
from datetime import datetime

from sqlalchemy.orm.exc import NoResultFound
from werkzeug.datastructures import MultiDict
from werkzeug.utils import secure_filename
from flask import redirect, render_template, flash, url_for, request, session
from flask.ext.login import current_user

from invenio.ext.sqlalchemy import db
from invenio.bibworkflow_config import CFG_OBJECT_VERSION, CFG_WORKFLOW_STATUS
from invenio.modules.workflows.models import BibWorkflowObject, Workflow
from invenio.bibworkflow_engine import BibWorkflowEngine
from invenio.bibworkflow_api import continue_oid

from invenio.modules.deposit import forms
from invenio.webdeposit_form import CFG_FIELD_FLAGS, DataExporter
from invenio.webdeposit_signals import file_uploaded
from invenio.webdeposit_storage import Storage


#
# Exceptions
#
class DepositionError(Exception):
    """ Base class for deposition errors """
    pass


class InvalidDepositionType(DepositionError):
    """ Raised when a deposition type cannot be found """
    pass


class DepositionDoesNotExists(DepositionError):
    """ Raised when a deposition does not exists """
    pass


class DraftDoesNotExists(DepositionError):
    """ Raised when a draft does not exists """
    pass


class FormDoesNotExists(DepositionError):
    """ Raised when a draft does not exists """
    pass


class DepositionNotDeletable(DepositionError):
    """ Raised when a deposition cannot be deleted """
    pass



#
# Helpers
#
class FactoryMixin(object):
    """
    Mix-in class to help create objects from persisted object state.
    """
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
    """ Determines if type is enabled """

    default = False
    """
    Determines if type is the default - warnings are issed if conflicts exsists
    """

    deletable = False
    """
    Determine if a deposition is deletable after submission.
    """

    group = None
    """ Name of group to include this type in. """

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
        Render page when deposition was successfully completed

        Method can be overwritten by subclasses to provide custom
        user interface.
        """
        flash('%(name)s was successfully finished.' %
              {'name': cls.name}, 'success')
        return redirect(url_for('.index'))

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
        Deposition.run().
        """
        return continue_oid(
            deposition.id,
            start_point="restart_task",
        )

    @classmethod
    def all(cls):
        """ Get a dictionary of deposition types """
        from invenio.webdeposit_load_deposition_types import deposition_types
        return deposition_types

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
        from invenio.webdeposit_load_deposition_types import deposition_default
        return deposition_default


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
        # TODO: Add checksum and content_type attributes
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

    def fill_draft(self, deposition, draft_id, form_class=None, clear=True):
        """
        Fill a draft with cached draft values
        """
        draft = deposition.get_or_create_draft(
            draft_id, form_class=form_class
        )

        draft.process(self.data, complete_form=True)

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
            type=self.form_class.__name__ if self.form_class else None,
            values=self.values,
            flags=self.flags,
            validate=self.validate,
        )

    def __setstate__(self, state):
        self.completed = state['completed']
        self.form_class = getattr(forms, state['type']) if state['type'] else None
        self.values = state['values']
        self.flags = state['flags']
        self.validate = state.get('validate', True)

    def is_completed(self):
        return self.completed

    def has_form(self):
        return self.form_class is not None

    def complete(self):
        """
        Set state of draft to completed.
        """
        self.completed = True

    def update(self, form):
        """
        Update draft values and flags with data from form.
        """
        json_data = dict((key, value) for key, value in form.json_data.items()
                         if value is not None)

        self.values = json_data
        self.flags = form.get_flags()

    def process(self, data, complete_form=False):
        """
        Process, validate and store incoming form data and return response.
        """
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
            if validated_flags[name] != flags
        )
        # Determine changed messages
        changed_msgs = dict(
            (name, messages) for name, messages in post_processed_msgs.items()
            if validated_msgs[name] != messages or process_field_names is None
            or name in process_field_names
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
        draft_data = self.values if load_draft else {}
        if formdata:
            formdata = MultiDict(formdata)

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

    Basically an interface to work BibWorkflowObject data attribute in an
    easy manner.
    """
    def __init__(self, workflow_object, type=None, user_id=None):
        self.workflow_object = workflow_object
        if not workflow_object:
            self.files = []
            self.drafts = {}
            self.type = (
                DepositionType.get(type) if type
                else DepositionType.get_default()
            )
            self.title = ''
            self.sips = []

            self.engine = BibWorkflowEngine(
                name=self.type.get_identifier(),
                id_user=user_id,
                module_name="webdeposit"
            )
            self.workflow_object = BibWorkflowObject(
                id_workflow=self.engine.uuid,
                id_user=user_id,
                version=CFG_OBJECT_VERSION.RUNNING,
            )
            self.workflow_object.set_data({})
        else:
            self.__setstate__(workflow_object.get_data())
            self.engine = None

    @property
    def id(self):
        return self.workflow_object.id

    @property
    def user_id(self):
        return self.workflow_object.id_user

    @property
    def created(self):
        return self.workflow_object.created

    @property
    def modified(self):
        return self.workflow_object.modified

    def __getstate__(self):
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
        self.type = DepositionType.get(state['type'])
        self.title = state['title']
        self.files = [
            DepositionFile.factory(f_state, uuid=f_state['id'])
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
        if self.engine:
            self.engine.save(status=CFG_WORKFLOW_STATUS.RUNNING)
        self.workflow_object.save(
            version=self.workflow_object.version or CFG_OBJECT_VERSION.RUNNING
        )

    def delete(self):
        """
        Delete the current deposition
        """
        if not self.type.deletable and self.is_finished():
            raise DepositionNotDeletable(self)

        for f in self.files:
            f.delete()

        if self.workflow_object.id_workflow != '':
            if self.workflow_object.id_workflow:
                Workflow.delete(uuid=self.workflow_object.id_workflow)

            BibWorkflowObject.query.filter_by(
                id_workflow=self.workflow_object.id_workflow
            ).delete()
        else:
            db.session.remove(self.workflow_object)
        db.session.commit()

    def run_workflow(self):
        """
        Execute the underlying workflow

        If you made modifications to the deposition you must save if before
        running the workflow, using the save() method.
        """
        if self.workflow_object.version == CFG_OBJECT_VERSION.FINAL:
            return self.type.render_completed(self)

        self.update()
        status = self.type.run_workflow(self).status
        self.reload()

        if status == CFG_WORKFLOW_STATUS.ERROR:
            return self.type.render_error(self)
        elif status != CFG_WORKFLOW_STATUS.COMPLETED:
            return self.type.render_step(self)
        elif status in [CFG_WORKFLOW_STATUS.FINISHED,
                        CFG_WORKFLOW_STATUS.COMPLETED]:
            return self.type.render_completed(self)

    def is_finished(self):
        """
        Check if deposition finished
        """
        return self.workflow_object.version == CFG_OBJECT_VERSION.FINAL

    def set_render_context(self, ctx):
        """
        Set rendering context - used in workflow tasks to set what is to be
        rendered.
        """
        self.workflow_object.deposition_context = ctx

    def get_render_context(self):
        """
        Get rendering context - used by DepositionType.render_step
        """
        return getattr(self.workflow_object, 'deposition_context', {})

    def get_draft(self, draft_id):
        """
        Get draft
        """
        if draft_id not in self.drafts:
            raise DraftDoesNotExists(draft_id)
        return self.drafts[draft_id]

    def get_or_create_draft(self, draft_id, form_class=None):
        """
        Get or create a draft for given draft_id
        """
        if draft_id not in self.drafts:
            self.drafts[draft_id] = DepositionDraft(
                draft_id, form_class=form_class, deposition_ref=self
            )
        return self.drafts[draft_id]

    def get_latest_sip(self, include_sealed=True):
        """
        Get the latest *unsealed* submission information package
        """
        if len(self.sips) > 0:
            sip = self.sips[-1]
            if include_sealed or not sip.is_sealed():
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

    def get_file(self, file_id):
        for f in self.files:
            if f.uuid == file_id:
                return f
        return None

    def add_file(self, deposition_file):
        self.files.append(deposition_file)
        file_uploaded.send(
            self.type, deposition=self, deposition_file=deposition_file
        )

    def remove_file(self, file_id):
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

    @classmethod
    def create(cls, user, type=None):
        """
        Create a new deposition object.

        To persist the deposition, you must call save() on the created object.
        If no type is defined, the default deposition type will be assigned.

        @param user: The owner of the deposition
        @param type: Deposition type identifier.
        """
        obj = cls(None, type=type, user_id=user.get_id())
        return obj

    @classmethod
    def get(cls, object_id, user=None, type=None):
        """
        Get the deposition with specified object id.

        @param object_id: The BibWorkflowObject id.
        @param user: Owner of the BibWorkflowObject
        @param type: Depostion type identifier.
        """
        if type:
            type = DepositionType.get(type)

        try:
            workflow_object = BibWorkflowObject.query.filter_by(
                id=object_id
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
    def get_depositions(cls, user, type=None):
        params = [
            Workflow.module_name == 'webdeposit',
            Workflow.id_user == user.get_id()
        ]

        if type:
            params.append(Workflow.name == type.get_identifier())

        objects = BibWorkflowObject.query.join("workflow").options(
            db.contains_eager('workflow')).filter(*params).order_by(
            BibWorkflowObject.modified.desc()).all()

        def _create_obj(o):
            try:
                obj = cls(o)
                if type is None or obj.type == type:
                    return obj
            except InvalidDepositionType:
                pass
            return None

        return filter(lambda x: x is not None, map(_create_obj, objects))


class SubmissionInformationPackage(FactoryMixin):
    def __init__(self, uuid=None, metadata={}):
        self.uuid = uuid or str(uuid4())
        self.metadata = metadata
        self.package = ""
        self.timestamp = None
        self.agents = []

    def __getstate__(self):
        return dict(
            id=self.uuid,
            metadata=self.metadata,
            package=self.package,
            timestamp=self.timestamp,
            agents=[a.__getstate__() for a in self.agents],
        )

    def __setstate__(self, state):
        self.uuid = state['id']
        self.metadata = state.get('metadata', {})
        self.package = state.get('package', None)
        self.timestamp = state.get('timestamp', None)
        self.agents = [Agent.factory(a_state)
                       for a_state in state.get('agents', [])]

    def seal(self):
        self.timestamp = datetime.now().isoformat()

    def is_sealed(self):
        return self.timestamp is not None


class Agent(FactoryMixin):
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
        from invenio.webuser_flask import current_user
        self.ip_address = request.remote_addr
        self.user_id = current_user.get_id()
        self.email_address = current_user.info.get('email', '')
